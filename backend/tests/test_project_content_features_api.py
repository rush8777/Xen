import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.dependencies import get_db
from backend.models import Project, ProjectContentFeatures, User
from backend.routers import project_content_features


def _build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(project_content_features.router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), TestingSessionLocal


def _seed_project(db):
    user = User(id=1, email="user@example.com")
    db.add(user)
    db.flush()
    project = Project(user_id=1, name="Test Project", video_duration_seconds=240)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_content_features_status_not_started():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)

    res = client.get(f"/api/projects/{project.id}/content-features/status")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == project.id
    assert set(data["features"].keys()) == {"clips", "subtitles", "chapters", "moments"}
    assert all(v["status"] == "not_started" for v in data["features"].values())


def test_generate_starts_background_jobs(monkeypatch):
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)

    async def fake_generate_all(project_id: int, force: bool = False):
        return None

    monkeypatch.setattr(project_content_features.generator, "generate_all", fake_generate_all)
    res = client.post(f"/api/projects/{project.id}/content-features/generate", json={"force": False})
    assert res.status_code == 200
    data = res.json()
    assert data["triggered"] is True
    assert data["status"] == "loading"


def test_generate_idempotent_while_processing(monkeypatch):
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        record = ProjectContentFeatures(project_id=project.id, clips_status="processing")
        db.add(record)
        db.commit()

    async def fake_generate_all(project_id: int, force: bool = False):
        raise AssertionError("should not be called")

    monkeypatch.setattr(project_content_features.generator, "generate_all", fake_generate_all)
    res = client.post(f"/api/projects/{project_id}/content-features/generate", json={"force": False})
    assert res.status_code == 200
    data = res.json()
    assert data["triggered"] is False


def test_feature_endpoint_returns_completed_payload():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        record = ProjectContentFeatures(
            project_id=project.id,
            clips_status="completed",
            clips_json=json.dumps({"clips": [{"id": "clip_1"}]}),
        )
        db.add(record)
        db.commit()

    res = client.get(f"/api/projects/{project_id}/content-features/clips")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["payload"]["clips"][0]["id"] == "clip_1"


def test_feature_endpoint_returns_400_when_not_ready():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)

    res = client.get(f"/api/projects/{project.id}/content-features/moments")
    assert res.status_code == 400
    assert "not ready" in res.json()["detail"]


def test_subtitles_export_srt_and_vtt():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        subtitles_payload = {
            "segments": [
                {
                    "start_time_seconds": 0,
                    "end_time_seconds": 3,
                    "text": "Hello world",
                    "lines": ["Hello world"],
                }
            ]
        }
        record = ProjectContentFeatures(
            project_id=project.id,
            subtitles_status="completed",
            subtitles_json=json.dumps(subtitles_payload),
        )
        db.add(record)
        db.commit()

    srt_res = client.post(
            f"/api/projects/{project_id}/content-features/subtitles/export",
        json={"format": "srt"},
    )
    assert srt_res.status_code == 200
    srt = srt_res.json()
    assert srt["filename"].endswith(".srt")
    assert "00:00:00,000 --> 00:00:03,000" in srt["content"]

    vtt_res = client.post(
            f"/api/projects/{project_id}/content-features/subtitles/export",
        json={"format": "vtt"},
    )
    assert vtt_res.status_code == 200
    vtt = vtt_res.json()
    assert vtt["filename"].endswith(".vtt")
    assert vtt["content"].startswith("WEBVTT")
