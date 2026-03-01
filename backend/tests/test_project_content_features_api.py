import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.dependencies import get_db
from backend.models import PremiumTranscriptInterval, Project, ProjectContentFeatures, User
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
            clips_json=json.dumps(
                {
                    "key_moments": [
                        {
                            "id": "moment_1",
                            "title": "Breakthrough Insight",
                            "category": "critical_insight",
                            "start_time_seconds": 12,
                            "end_time_seconds": 33,
                            "duration_seconds": 21,
                            "justification": "This reframes the entire argument with concrete evidence.",
                            "impact_level": "high",
                            "context": "After setup",
                            "key_quote": "The pivot starts here.",
                        }
                    ]
                }
            ),
        )
        db.add(record)
        db.commit()

    res = client.get(f"/api/projects/{project_id}/content-features/clips")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["payload"]["key_moments"][0]["id"] == "moment_1"


def test_feature_endpoint_returns_completed_chapters_hierarchical_payload():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        record = ProjectContentFeatures(
            project_id=project.id,
            chapters_status="completed",
            chapters_json=json.dumps(
                {
                    "totalChapters": 1,
                    "chapters": [
                        {
                            "id": "chapter_1",
                            "title": "Proof Progression",
                            "start_time_seconds": 0,
                            "end_time_seconds": 60,
                            "duration_seconds": 60,
                            "summary": "The section establishes a claim, supports it with concrete evidence, and transitions toward a practical conclusion.",
                            "psychological_intent": "deliver_proof",
                            "chapter_type": "Demonstration",
                            "subchapters": [
                                {
                                    "id": "chapter_1_sub_1",
                                    "title": "Claim setup",
                                    "start_time_seconds": 0,
                                    "end_time_seconds": 24,
                                    "duration_seconds": 24,
                                    "summary": "The speaker introduces the claim boundaries and expected outcome with enough context for interpretation.",
                                },
                                {
                                    "id": "chapter_1_sub_2",
                                    "title": "Demonstration",
                                    "start_time_seconds": 24,
                                    "end_time_seconds": 60,
                                    "duration_seconds": 36,
                                    "summary": "The speaker delivers concrete evidence and explains why it supports the claim under real constraints.",
                                },
                            ],
                        }
                    ],
                }
            ),
        )
        db.add(record)
        db.commit()

    res = client.get(f"/api/projects/{project_id}/content-features/chapters")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["payload"]["totalChapters"] == 1
    assert data["payload"]["chapters"][0]["psychological_intent"] == "deliver_proof"
    assert data["payload"]["chapters"][0]["chapter_type"] == "Demonstration"
    assert len(data["payload"]["chapters"][0]["subchapters"]) == 2


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


def test_generate_single_feature_starts_background_job(monkeypatch):
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)

    async def fake_generate_feature(project_id: int, feature_id: str, force: bool = False):
        return None

    monkeypatch.setattr(project_content_features.generator, "generate_feature", fake_generate_feature)
    res = client.post(
        f"/api/projects/{project.id}/content-features/clips/generate",
        json={"force": False},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["triggered"] is True
    assert data["status"] == "loading"


def test_generate_single_feature_idempotent_while_processing(monkeypatch):
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        record = ProjectContentFeatures(project_id=project.id, clips_status="processing")
        db.add(record)
        db.commit()

    async def fake_generate_feature(project_id: int, feature_id: str, force: bool = False):
        raise AssertionError("should not be called")

    monkeypatch.setattr(project_content_features.generator, "generate_feature", fake_generate_feature)
    res = client.post(
        f"/api/projects/{project_id}/content-features/clips/generate",
        json={"force": False},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["triggered"] is False


def test_transcript_passage_prefers_premium_transcript_table():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        db.add(
            PremiumTranscriptInterval(
                project_id=project_id,
                video_id=project.video_id or 1,
                interval_id=1,
                interval_index=0,
                start_time_seconds=0,
                end_time_seconds=20,
                transcript_text="Welcome everyone to this session.",
            )
        )
        db.add(
            PremiumTranscriptInterval(
                project_id=project_id,
                video_id=project.video_id or 1,
                interval_id=2,
                interval_index=1,
                start_time_seconds=20,
                end_time_seconds=40,
                transcript_text="Today we will cover the core strategy.",
            )
        )
        db.commit()

    res = client.get(f"/api/projects/{project_id}/transcript-passage")
    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "premium_transcript_table"
    assert len(data["segments"]) == 2
    assert "Welcome everyone" in data["passage"]
