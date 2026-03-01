from __future__ import annotations

import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.models import Project, ProjectContentFeatures, User
import backend.services.content_features_generator as content_features_generator_module
from backend.services.content_features_generator import ProjectContentFeaturesGenerator


def _build_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal


def _seed_project(db):
    user = User(id=1, email="gen@example.com")
    db.add(user)
    db.flush()
    project = Project(
        user_id=1,
        name="Generator Project",
        video_duration_seconds=260,
        gemini_cached_content_name="cachedContents/project-1",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_generate_feature_only_updates_target_feature(monkeypatch):
    SessionLocal = _build_session()
    monkeypatch.setattr(content_features_generator_module, "SessionLocal", SessionLocal)
    generator = ProjectContentFeaturesGenerator()

    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id
        record = ProjectContentFeatures(project_id=project.id)
        db.add(record)
        db.commit()

    async def fake_run_feature(project_id: int, feature_id: str):
        assert feature_id == "clips"
        generator._set_feature_state(
            "clips",
            project_id,
            status="completed",
            progress=100,
            payload={"clips": [{"id": "clip_1"}]},
            error=None,
        )

    monkeypatch.setattr(generator, "_run_feature", fake_run_feature)
    asyncio.run(generator.generate_feature(project_id, "clips", force=False))

    with SessionLocal() as db:
        record = (
            db.query(ProjectContentFeatures)
            .filter(ProjectContentFeatures.project_id == project_id)
            .first()
        )
        assert record is not None
        assert record.clips_status == "completed"
        assert record.subtitles_status == "not_started"
        assert record.chapters_status == "not_started"
        assert record.moments_status == "not_started"


def test_generate_all_invokes_all_feature_tasks(monkeypatch):
    SessionLocal = _build_session()
    monkeypatch.setattr(content_features_generator_module, "SessionLocal", SessionLocal)
    generator = ProjectContentFeaturesGenerator()

    with SessionLocal() as db:
        project = _seed_project(db)
        project_id = project.id

    called: set[str] = set()

    async def fake_clips(project_id: int):
        called.add("clips")
        generator._set_feature_state("clips", project_id, status="completed", progress=100, payload={"clips": []}, error=None)

    async def fake_subtitles(project_id: int):
        called.add("subtitles")
        generator._set_feature_state("subtitles", project_id, status="completed", progress=100, payload={"segments": []}, error=None)

    async def fake_chapters(project_id: int):
        called.add("chapters")
        generator._set_feature_state("chapters", project_id, status="completed", progress=100, payload={"chapters": []}, error=None)

    async def fake_moments(project_id: int):
        called.add("moments")
        generator._set_feature_state("moments", project_id, status="completed", progress=100, payload={"moments": []}, error=None)

    monkeypatch.setattr(generator, "_generate_clips", fake_clips)
    monkeypatch.setattr(generator, "_generate_subtitles", fake_subtitles)
    monkeypatch.setattr(generator, "_generate_chapters", fake_chapters)
    monkeypatch.setattr(generator, "_generate_moments", fake_moments)

    asyncio.run(generator.generate_all(project_id, force=False))
    assert called == {"clips", "subtitles", "chapters", "moments"}
