from datetime import datetime, timedelta
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.dependencies import get_db
from backend.models import Chat, Project, User
from backend.routers import chats


def _build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(chats.router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), TestingSessionLocal


def _seed_user_project(db, *, user_id: int, project_name: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        user = User(id=user_id, email=f"user-{user_id}@example.com")
        db.add(user)
        db.flush()
    project = Project(user_id=user_id, name=project_name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return user, project


def _valid_course_payload():
    return {
        "courseTitle": "Hook Optimization Course",
        "slides": [
            {"id": "s1", "type": "title", "title": "Hook Optimization", "subtitle": "Start strong"},
            {"id": "s2", "type": "text-only", "title": "Audit", "body": "Review first 3 seconds"},
            {"id": "s3", "type": "text-image", "title": "Pattern interrupt", "body": "Use movement quickly"},
            {
                "id": "s4",
                "type": "cards",
                "title": "Playbook",
                "cards": [{"heading": "Cut speed", "description": "Increase edits in first 10s"}],
            },
            {
                "id": "s5",
                "type": "checklist",
                "title": "Action list",
                "items": [{"text": "Rewrite hook"}, {"text": "Add motion cue"}],
            },
            {
                "id": "s6",
                "type": "quiz",
                "title": "Quick test",
                "quizQuestion": "What matters most in first 3s?",
                "quizOptions": ["No opening", "Strong hook"],
                "correctAnswer": 1,
            },
        ],
    }


def test_default_project_resolution_user_scoped():
    _, SessionLocal = _build_client()
    with SessionLocal() as db:
        _, p1 = _seed_user_project(db, user_id=1, project_name="User One A")
        _, p2 = _seed_user_project(db, user_id=1, project_name="User One B")
        _, p3 = _seed_user_project(db, user_id=2, project_name="User Two A")

        older = Chat(project_id=p1.id, name="old", updated_at=datetime.utcnow() - timedelta(days=1))
        newer_same_user = Chat(project_id=p2.id, name="new", updated_at=datetime.utcnow())
        newest_other_user = Chat(project_id=p3.id, name="other", updated_at=datetime.utcnow() + timedelta(minutes=1))
        db.add_all([older, newer_same_user, newest_other_user])
        db.commit()

        resolved = chats._resolve_default_project_for_new_chat(db=db, user_id=1)
        assert resolved is not None
        assert resolved.id == p2.id


def test_default_project_resolution_global_when_user_null():
    _, SessionLocal = _build_client()
    with SessionLocal() as db:
        _, p1 = _seed_user_project(db, user_id=1, project_name="Project A")
        _, p2 = _seed_user_project(db, user_id=2, project_name="Project B")
        db.add_all(
            [
                Chat(project_id=p1.id, name="older", updated_at=datetime.utcnow() - timedelta(hours=1)),
                Chat(project_id=p2.id, name="latest", updated_at=datetime.utcnow()),
            ]
        )
        db.commit()

        resolved = chats._resolve_default_project_for_new_chat(db=db, user_id=None)
        assert resolved is not None
        assert resolved.id == p2.id


def test_first_message_without_mention_uses_latest_project():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        _seed_user_project(db, user_id=1, project_name="No Chat Yet")

    response = client.post(
        "/api/chats/send-message",
        json={"chat_id": None, "message": "Please help me improve this", "user_id": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["project"]["name"] == "No Chat Yet"


def test_project_id_in_payload_forces_target_project():
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        _seed_user_project(db, user_id=1, project_name="Project A")
        _, project_b = _seed_user_project(db, user_id=1, project_name="Project B")

    response = client.post(
        "/api/chats/send-message",
        json={
            "chat_id": None,
            "project_id": project_b.id,
            "message": "Analyze this video",
            "user_id": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["project"]["id"] == project_b.id
    assert body["project"]["name"] == "Project B"


def test_course_gate_blocks_smalltalk_even_if_intent_true():
    allowed = chats._should_generate_course(
        user_message="hello",
        intent={"is_course_request": True, "confidence": 0.99},
        provided_clarification_answers={},
        course_mode_enabled=True,
    )
    assert allowed is False


def test_course_gate_requires_explicit_trigger_for_mid_confidence_intent():
    blocked = chats._should_generate_course(
        user_message="Can you analyze this video quickly?",
        intent={"is_course_request": True, "confidence": 0.7},
        provided_clarification_answers={},
        course_mode_enabled=True,
    )
    assert blocked is False

    allowed = chats._should_generate_course(
        user_message="Create a short course for this video",
        intent={"is_course_request": True, "confidence": 0.7},
        provided_clarification_answers={},
        course_mode_enabled=True,
    )
    assert allowed is True


def test_course_gate_blocks_even_explicit_course_request_when_mode_off():
    blocked = chats._should_generate_course(
        user_message="Create a short course for this video",
        intent={"is_course_request": True, "confidence": 0.99},
        provided_clarification_answers={"goal": "Retention"},
        course_mode_enabled=False,
    )
    assert blocked is False


def test_course_intent_true_returns_course_payload(monkeypatch):
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        _, project = _seed_user_project(db, user_id=1, project_name="Course Project")
        chat = Chat(project_id=project.id, name="course-chat")
        db.add(chat)
        db.commit()
        db.refresh(chat)
        chat_id = chat.id

    async def fake_detect(self, **kwargs):
        return {"is_course_request": True, "confidence": 0.9, "goal": "Improve hook"}

    async def fake_generate(self, **kwargs):
        return ("Generated course summary", _valid_course_payload(), True, 1, ["ctx"])

    monkeypatch.setattr("backend.services.rag_chat_service.RagChatService.detect_course_intent_async", fake_detect)
    monkeypatch.setattr("backend.services.rag_chat_service.RagChatService.generate_course_async", fake_generate)

    response = client.post(
        "/api/chats/send-message",
        json={"chat_id": chat_id, "message": "Create me a course to improve retention", "user_id": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["course_generated"] is True
    assert body["course_summary"] == "Generated course summary"
    assert body["course_data"]["courseTitle"] == "Hook Optimization Course"


def test_invalid_course_json_falls_back_to_text_response(monkeypatch):
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        _, project = _seed_user_project(db, user_id=1, project_name="Fallback Project")
        chat = Chat(project_id=project.id, name="fallback-chat")
        db.add(chat)
        db.commit()
        db.refresh(chat)
        chat_id = chat.id

    async def fake_detect(self, **kwargs):
        return {"is_course_request": True, "confidence": 0.9, "goal": "Improve"}

    async def fake_generate(self, **kwargs):
        raise ValueError("invalid payload")

    async def fake_reply(self, **kwargs):
        return ("Fallback reply", False, 0, [])

    monkeypatch.setattr("backend.services.rag_chat_service.RagChatService.detect_course_intent_async", fake_detect)
    monkeypatch.setattr("backend.services.rag_chat_service.RagChatService.generate_course_async", fake_generate)
    monkeypatch.setattr("backend.services.rag_chat_service.RagChatService.generate_reply_async", fake_reply)

    response = client.post(
        "/api/chats/send-message",
        json={"chat_id": chat_id, "message": "Teach me", "user_id": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["course_generated"] is False
    assert body["course_data"] is None
    assert body["messages"][-1]["content"] == "Fallback reply"


def test_stream_done_includes_course_fields_when_generated(monkeypatch):
    client, SessionLocal = _build_client()
    with SessionLocal() as db:
        _, project = _seed_user_project(db, user_id=1, project_name="Stream Course Project")
        chat = Chat(project_id=project.id, name="stream-chat")
        db.add(chat)
        db.commit()
        db.refresh(chat)
        chat_id = chat.id

    async def fake_detect(self, **kwargs):
        return {"is_course_request": True, "confidence": 0.95, "goal": "Improve views"}

    async def fake_generate(self, **kwargs):
        return ("Stream course summary", _valid_course_payload(), True, 2, ["c1", "c2"])

    monkeypatch.setattr("backend.services.rag_chat_service.RagChatService.detect_course_intent_async", fake_detect)
    monkeypatch.setattr("backend.services.rag_chat_service.RagChatService.generate_course_async", fake_generate)

    response = client.post(
        "/api/chats/send-message-stream",
        json={"chat_id": chat_id, "message": "Build a course for this video", "user_id": 1},
    )
    assert response.status_code == 200

    raw = response.text
    done_payload = None
    for event_blob in raw.split("\n\n"):
        if "event: done" not in event_blob:
            continue
        for line in event_blob.splitlines():
            if line.startswith("data: "):
                done_payload = json.loads(line[6:])
                break
        if done_payload:
            break

    assert done_payload is not None
    assert done_payload["course_generated"] is True
    assert done_payload["course_summary"] == "Stream course summary"
    assert done_payload["course_data"]["courseTitle"] == "Hook Optimization Course"
