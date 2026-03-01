import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.dependencies import get_db
from backend.models import Project, ProjectPsychologyAnalysis, User
from backend.routers import project_psychology


def _build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(project_psychology.router)

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
    project = Project(user_id=1, name="Psychology Project")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_psychology_status_not_started():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id

    res = client.get(f"/api/projects/{project_id}/psychology/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "not_started"
    assert data["generated_at"] is None


def test_psychology_regenerate_sets_pending(monkeypatch):
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id

    monkeypatch.setattr(project_psychology.settings, "TASKS_MODE", "cloud_tasks")
    call = {"interval_seconds": None}
    def _fake_enqueue(project_id: int, run_id: int | None, interval_seconds: int = 5):
        call["interval_seconds"] = interval_seconds
        return {"mode": "cloud_tasks", "request_id": "x", "task_name": "x"}
    monkeypatch.setattr(project_psychology, "enqueue_psychology_generation", _fake_enqueue)

    res = client.post(
        f"/api/projects/{project_id}/psychology/regenerate",
        json={"interval_seconds": 2},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending"
    assert call["interval_seconds"] == 2


def test_psychology_get_returns_400_when_not_ready():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        db.add(
            ProjectPsychologyAnalysis(
                project_id=project_id,
                psychology_json="{}",
                status="pending",
                version=1,
            )
        )
        db.commit()

    res = client.get(f"/api/projects/{project_id}/psychology")
    assert res.status_code == 400
    assert "not ready" in res.json()["detail"]


def test_psychology_get_returns_completed_payload():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        db.add(
            ProjectPsychologyAnalysis(
                project_id=project_id,
                psychology_json=json.dumps({
                    "variants": {
                        "2": {
                            "curiosity": {"curiosityScore": 72, "spikes": [], "openLoops": [], "closedLoops": []},
                            "curiosity_narrative": {
                                "interval_seconds": 2,
                                "curiosityScore": 72,
                                "totalOpenLoops": 2,
                                "avgLoopDuration": 9,
                                "intervals": [],
                            },
                            "emotional_arc": {},
                            "tension_release": {},
                            "persuasion_signals": {
                                "authority": 10,
                                "urgency": 10,
                                "socialProof": 10,
                                "certainty": 10,
                                "scarcity": 10,
                            },
                            "persuasion_narrative": {
                                "interval_seconds": 2,
                                "persuasionScore": 45,
                                "dominantSignal": "Authority",
                                "intervals": [],
                            },
                            "cognitive_load": {},
                        }
                    },
                    "latest_interval_seconds": 2,
                }),
                status="completed",
                version=1,
            )
        )
        db.commit()

    res = client.get(f"/api/projects/{project_id}/psychology?interval_seconds=2")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["psychology"]["curiosity"]["curiosityScore"] == 72
    assert "curiosity_narrative" in data["psychology"]
    assert "persuasion_signals" in data["psychology"]


def test_psychology_get_variant_missing_returns_400():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        db.add(
            ProjectPsychologyAnalysis(
                project_id=project_id,
                psychology_json=json.dumps(
                    {
                        "variants": {"5": {"curiosity": {"curiosityScore": 55}}},
                        "latest_interval_seconds": 5,
                    }
                ),
                status="completed",
                version=1,
            )
        )
        db.commit()

    res = client.get(f"/api/projects/{project_id}/psychology?interval_seconds=2")
    assert res.status_code == 400
    assert "Variant not generated for interval_seconds=2" in res.json()["detail"]


def test_psychology_regenerate_idempotent_when_pending(monkeypatch):
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        db.add(
            ProjectPsychologyAnalysis(
                project_id=project_id,
                psychology_json="{}",
                status="pending",
                version=1,
            )
        )
        db.commit()

    called = {"value": False}

    def _fake_enqueue(*args, **kwargs):
        called["value"] = True
        return {"mode": "cloud_tasks", "request_id": "x", "task_name": "x"}

    monkeypatch.setattr(project_psychology.settings, "TASKS_MODE", "cloud_tasks")
    monkeypatch.setattr(project_psychology, "enqueue_psychology_generation", _fake_enqueue)

    res = client.post(f"/api/projects/{project_id}/psychology/regenerate")
    assert res.status_code == 200
    assert res.json()["status"] == "pending"
    assert called["value"] is False


def test_psychology_project_not_found():
    client, _ = _build_client()

    for method, path in [
        (client.get, "/api/projects/999/psychology/status"),
        (client.post, "/api/projects/999/psychology/regenerate"),
        (client.get, "/api/projects/999/psychology"),
    ]:
        res = method(path)
        assert res.status_code == 404


def test_psychology_invalid_interval_returns_422():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id

    res_get = client.get(f"/api/projects/{project_id}/psychology?interval_seconds=3")
    assert res_get.status_code == 422

    res_post = client.post(
        f"/api/projects/{project_id}/psychology/regenerate",
        json={"interval_seconds": 10},
    )
    assert res_post.status_code == 422
