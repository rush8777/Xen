from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, User
from backend.services.video_library import VideoDTO, VideoLibraryService


def _session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_upsert_video_creates_and_updates():
    db = _session()
    user = User(id=1, email=None, name=None)
    db.add(user)
    db.commit()
    db.refresh(user)

    service = VideoLibraryService(db, user)
    dto = VideoDTO(
        platform="youtube",
        platform_video_id="abc123",
        title="Test video",
        description="desc",
        channel_title="Channel",
        thumbnail_url="http://example.com/thumb.jpg",
        url="http://example.com/watch?v=abc123",
        duration_seconds=95,
        view_count=1234,
        like_count=10,
        comment_count=2,
        categories=["cat1"],
        tags=["tag1", "tag2"],
        published_at=datetime.now(timezone.utc) - timedelta(days=2),
    )

    video = service.upsert_video(dto)
    assert video.id is not None
    assert video.title == "Test video"

    # Update title to verify upsert behavior
    dto_updated = dto.copy(update={"title": "Updated title", "view_count": 2000})
    video_updated = service.upsert_video(dto_updated)
    assert video_updated.id == video.id
    assert video_updated.title == "Updated title"
    assert video_updated.view_count == 2000


def test_response_formatting():
    db = _session()
    user = User(id=1, email=None, name=None)
    db.add(user)
    db.commit()
    db.refresh(user)

    service = VideoLibraryService(db, user)
    dto = VideoDTO(
        platform="youtube",
        platform_video_id="xyz",
        title="Formatting Test",
        channel_title="Formatter",
        duration_seconds=3661,
        view_count=1523000,
        like_count=3210,
        comment_count=150,
        published_at=datetime.now(timezone.utc) - timedelta(hours=5),
    )
    video = service.upsert_video(dto)

    resp = service.to_response(video)
    assert resp.duration_text == "1:01:01"
    assert resp.views_text == "1.5M views"
    assert resp.stats_text is not None

