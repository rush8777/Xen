from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import User, Video, OAuthConnection
from ..services import VideoDTO, VideoLibraryService, YouTubeService

router = APIRouter(prefix="/api/videos", tags=["videos"])
class VideoListResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


def _get_or_create_user(db: Session) -> User:
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, email=None, name=None)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _format_number(num: Optional[int]) -> Optional[str]:
    if num is None:
        return None
    if num == 0:
        return "0"
    if num < 1000:
        return f"{num}"
    suffixes = ["K", "M", "B", "T"]
    idx = 0
    n = float(num)
    while n >= 1000 and idx < len(suffixes):
        n /= 1000.0
        idx += 1
    if idx == 0:
        return f"{num}"
    return f"{n:.1f}{suffixes[idx - 1]}"


def _format_duration(seconds: Optional[int]) -> Optional[str]:
    if seconds is None:
        return None
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:d}:{sec:02d}"


def _dto_to_list_item(dto: VideoDTO) -> dict:
    views_text = _format_number(dto.view_count)
    likes_text = _format_number(dto.like_count)
    comments_text = _format_number(dto.comment_count)

    stats_parts: list[str] = []
    if likes_text:
        stats_parts.append(f"{likes_text} likes")
    if comments_text:
        stats_parts.append(f"{comments_text} comments")

    return {
        "id": dto.platform_video_id,
        "platform_video_id": dto.platform_video_id,
        "title": dto.title,
        "description": dto.description,
        "platform": dto.platform,
        "channel": dto.channel_title,
        "channel_title": dto.channel_title,
        "channel_id": dto.channel_id,
        "thumbnail": dto.thumbnail_url,
        "thumbnail_url": dto.thumbnail_url,
        "url": dto.url,
        "views": dto.view_count,
        "view_count": dto.view_count,
        "views_text": f"{views_text} views" if views_text else None,
        "likes": dto.like_count,
        "like_count": dto.like_count,
        "comments": dto.comment_count,
        "comment_count": dto.comment_count,
        "duration_seconds": dto.duration_seconds,
        "duration_text": _format_duration(dto.duration_seconds),
        "stats_text": " • ".join([p for p in stats_parts if p]) or None,
        "published_at": dto.published_at,
        "published_time_text": None,
        "categories": dto.categories or [],
        "tags": dto.tags or [],
    }


@router.get("", response_model=VideoListResponse)
def list_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    platform: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search by title or channel"),
    sort: str = Query("recent", pattern="^(recent|views|likes)$"),
    duration_min: Optional[int] = Query(None, ge=0),
    duration_max: Optional[int] = Query(None, ge=0),
    live: bool = Query(False, description="If true, fetch directly from platform APIs without using the DB"),
    db: Session = Depends(get_db),
):
    user = _get_or_create_user(db)

    if live:
        if platform and platform != "youtube":
            raise HTTPException(
                status_code=400,
                detail=f"Platform '{platform}' not yet implemented",
            )

        yt = YouTubeService.from_db(db, user)
        if not yt:
            raise HTTPException(status_code=400, detail="No YouTube connection found")

        dtos = yt.fetch_recent_videos(max_results=page_size)
        items = [_dto_to_list_item(dto) for dto in dtos]
        return {
            "items": items,
            "total": len(items),
            "page": 1,
            "page_size": len(items),
        }

    service = VideoLibraryService(db, user)

    query = db.query(Video).filter(Video.user_id == user.id)

    if platform:
        query = query.filter(Video.platform == platform)
    if category:
        query = query.filter(Video.categories.like(f"%{category}%"))
    if q:
        pattern = f"%{q.lower()}%"
        query = query.filter(
            func.lower(Video.title).like(pattern)
            | func.lower(Video.channel_title).like(pattern)
        )
    if duration_min is not None:
        query = query.filter(Video.duration_seconds >= duration_min)
    if duration_max is not None:
        query = query.filter(Video.duration_seconds <= duration_max)

    if sort == "views":
        query = query.order_by(Video.view_count.desc().nullslast(), Video.published_at.desc().nullslast())
    elif sort == "likes":
        query = query.order_by(Video.like_count.desc().nullslast(), Video.published_at.desc().nullslast())
    else:
        query = query.order_by(Video.published_at.desc().nullslast(), Video.cached_at.desc().nullslast())

    total = query.count()
    items = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [service.to_response(v).dict() for v in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)) -> dict:
    """List all unique categories from videos"""
    user = _get_or_create_user(db)

    rows = (
        db.query(Video.categories)
        .filter(Video.user_id == user.id, Video.categories.isnot(None))
        .all()
    )
    categories: set[str] = set()
    for row in rows:
        raw = row[0] or ""
        for cat in raw.split(","):
            cat_clean = cat.strip()
            if cat_clean:
                categories.add(cat_clean)
    return {"categories": sorted(categories)}


class RefreshResponse(BaseModel):
    status: str
    refreshed: int
    note: Optional[str] = None


@router.post("/refresh", response_model=RefreshResponse)
def refresh_videos(
    platform: Optional[str] = Query(None, description="If provided, only refresh that platform"),
    db: Session = Depends(get_db),
):
    user = _get_or_create_user(db)
    library = VideoLibraryService(db, user)

    dtos: list[VideoDTO] = []
    note: Optional[str] = None

    platforms = [platform] if platform else ["youtube"]
    for plat in platforms:
        if plat == "youtube":
            yt = YouTubeService.from_db(db, user)
            if yt:
                fetched_dtos = yt.fetch_recent_videos()
                if fetched_dtos:
                    dtos.extend(fetched_dtos)
                else:
                    note = "No videos found from YouTube API"
            else:
                note = "No YouTube connection found"
        else:
            note = f"Platform '{plat}' not yet implemented"

    # Filter out None values and process valid DTOs
    valid_dtos = [dto for dto in dtos if dto is not None]
    videos = library.bulk_upsert(valid_dtos)
    return RefreshResponse(status="ok", refreshed=len(videos), note=note)


@router.get("/{video_id}")
def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get a specific video by ID"""
    user = _get_or_create_user(db)
    service = VideoLibraryService(db, user)

    video = (
        db.query(Video)
        .filter(Video.user_id == user.id, Video.id == video_id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return service.to_response(video).dict()


@router.post("/debug-add-samples")
def debug_add_samples(db: Session = Depends(get_db)):
    """Debug endpoint to add sample videos directly"""
    user = _get_or_create_user(db)
    library = VideoLibraryService(db, user)
    
    # Add sample videos - commented out to prevent sample data
    # dtos = _sample_videos("youtube")
    # videos = library.bulk_upsert(dtos)
    
    return {
        "status": "ok",
        "added": 0,
        "message": "Sample data generation is currently disabled."
    }