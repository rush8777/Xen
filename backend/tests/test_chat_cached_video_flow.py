from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.models import Project, User
from backend.services.rag_chat_service import RagChatService


def _build_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal


def _seed_project(db, *, cached_content_name: str) -> Project:
    user = User(id=1, email="cache-test@example.com")
    db.add(user)
    db.flush()
    project = Project(
        user_id=1,
        name="Cached Video Project",
        gemini_cached_content_name=cached_content_name,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_generate_reply_uses_cached_video_when_cache_is_active(monkeypatch):
    SessionLocal = _build_session()
    with SessionLocal() as db:
        project = _seed_project(db, cached_content_name="cachedContents/active-1")
        service = RagChatService()

        calls: dict[str, object] = {}

        def fake_caches_get(*, name: str):
            calls["cache_name"] = name
            return SimpleNamespace(
                expire_time=datetime.now(timezone.utc) + timedelta(minutes=20)
            )

        def fake_generate_content(*, model, contents, config):
            calls["model"] = model
            calls["config"] = config
            return SimpleNamespace(text="answer from cached video")

        async def fail_if_called(**kwargs):
            raise AssertionError("RAG retrieval should not run while cache is active")

        monkeypatch.setattr(
            "backend.services.rag_chat_service.client.caches.get",
            fake_caches_get,
        )
        monkeypatch.setattr(
            "backend.services.rag_chat_service.client.models.generate_content",
            fake_generate_content,
        )
        monkeypatch.setattr(service, "retrieve_project_context_async", fail_if_called)

        text, rag_active, used, chunks = asyncio.run(
            service.generate_reply_async(
                project=project,
                messages=[{"role": "user", "content": "Hi"}],
                user_message="What is happening in the video?",
                db=db,
            )
        )

        assert text == "answer from cached video"
        assert rag_active is True
        assert used == 1
        assert len(chunks) == 1
        assert "Gemini cached video" in chunks[0]
        assert calls["cache_name"] == "cachedContents/active-1"
        assert getattr(calls["config"], "cached_content", None) == "cachedContents/active-1"


def test_generate_reply_falls_back_to_rag_when_cache_is_expired(monkeypatch):
    SessionLocal = _build_session()
    with SessionLocal() as db:
        project = _seed_project(db, cached_content_name="cachedContents/expired-1")
        service = RagChatService()

        calls: dict[str, object] = {}

        def fake_caches_get(*, name: str):
            calls["cache_name"] = name
            return SimpleNamespace(
                expire_time=datetime.now(timezone.utc) - timedelta(minutes=5)
            )

        async def fake_retrieve(**kwargs):
            calls["retrieval_called"] = True
            return ["timestamped context"], True

        def fake_generate_content(*, model, contents, config):
            calls["config"] = config
            return SimpleNamespace(text="answer from rag path")

        monkeypatch.setattr(
            "backend.services.rag_chat_service.client.caches.get",
            fake_caches_get,
        )
        monkeypatch.setattr(
            "backend.services.rag_chat_service.client.models.generate_content",
            fake_generate_content,
        )
        monkeypatch.setattr(service, "retrieve_project_context_async", fake_retrieve)

        text, rag_active, used, chunks = asyncio.run(
            service.generate_reply_async(
                project=project,
                messages=[{"role": "user", "content": "Hi"}],
                user_message="Summarize the key issue.",
                db=db,
            )
        )

        assert text == "answer from rag path"
        assert rag_active is True
        assert used == 1
        assert chunks == ["timestamped context"]
        assert calls["cache_name"] == "cachedContents/expired-1"
        assert calls.get("retrieval_called") is True
        assert getattr(calls["config"], "cached_content", None) in (None, "")
