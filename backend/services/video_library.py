from __future__ import annotations

from datetime import datetime, timezone
import json
from math import log10
from typing import Any, Iterable, List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models import PlatformVideo, User, Video


class VideoDTO(BaseModel):
    platform: str
    platform_video_id: str
    title: str
    description: str | None = None
    channel_title: str | None = None
    channel_id: str | None = None
    channel_url: str | None = None
    thumbnail_url: str | None = None
    url: str | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    categories: list[str] | None = None
    tags: list[str] | None = None
    published_at: datetime | None = None
    etag: str | None = None
    raw: dict[str, Any] | None = None


class VideoResponse(BaseModel):
    id: int
    title: str
    description: str | None
    platform: str
    channel: str | None
    channel_id: str | None
    thumbnail: str | None
    url: str | None
    views: int | None
    views_text: str | None
    likes: int | None
    comments: int | None
    duration_seconds: int | None
    duration_text: str | None
    stats_text: str | None
    published_at: datetime | None
    published_time_text: str | None
    categories: list[str]
    tags: list[str]


class VideoLibraryService:
    """
    Service responsible for normalizing, upserting, and formatting video data.
    """

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    def upsert_video(self, dto: VideoDTO) -> Video:
        if dto is None:
            raise ValueError("DTO cannot be None")
            
        pv = (
            self.db.query(PlatformVideo)
            .filter(
                PlatformVideo.user_id == self.user.id,
                PlatformVideo.platform == dto.platform,
                PlatformVideo.platform_video_id == dto.platform_video_id,
            )
            .first()
        )

        if pv and pv.video:
            video = pv.video
        else:
            # Create new video if pv doesn't exist or if pv.video is None
            video = Video(user_id=self.user.id, platform=dto.platform)
            self.db.add(video)
            
            if pv:
                # PlatformVideo exists but video is None, fix the relationship
                pv.video = video
            else:
                # Create new PlatformVideo
                pv = PlatformVideo(
                    user_id=self.user.id,
                    platform=dto.platform,
                    platform_video_id=dto.platform_video_id,
                    video=video,
                )
                self.db.add(pv)

        video.title = dto.title or "Untitled Video"
        video.description = dto.description
        video.channel_title = dto.channel_title
        video.channel_id = dto.channel_id
        video.channel_url = dto.channel_url
        video.thumbnail_url = dto.thumbnail_url
        video.url = dto.url
        video.duration_seconds = dto.duration_seconds
        video.view_count = dto.view_count
        video.like_count = dto.like_count
        video.comment_count = dto.comment_count
        video.categories = ",".join(dto.categories or [])
        video.tags = ",".join(dto.tags or [])
        video.published_at = dto.published_at
        video.cached_at = datetime.utcnow()

        pv.etag = dto.etag
        if dto.raw is not None:
            pv.extra = json.dumps(dto.raw)

        self.db.commit()
        self.db.refresh(video)
        return video

    def bulk_upsert(self, dtos: Iterable[VideoDTO]) -> list[Video]:
        videos: list[Video] = []
        for dto in dtos:
            if dto is None:
                continue
            videos.append(self.upsert_video(dto))
        return videos

    # --- Formatting helpers ---
    @staticmethod
    def _format_number(num: Optional[int]) -> Optional[str]:
        if num is None:
            return None
        if num == 0:
            return "0"
        if num < 1000:
            return f"{num}"
        suffixes = ["K", "M", "B", "T"]
        idx = min(int(log10(num) // 3), len(suffixes))
        scaled = num / (1000 ** idx)
        suffix = suffixes[idx - 1] if idx > 0 else ""
        return f"{scaled:.1f}{suffix}"

    @staticmethod
    def _format_duration(seconds: Optional[int]) -> Optional[str]:
        if seconds is None:
            return None
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:d}:{minutes:02d}:{sec:02d}"
        return f"{minutes:d}:{sec:02d}"

    @staticmethod
    def _relative_time(dt: Optional[datetime]) -> Optional[str]:
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        utc_dt = dt.astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - utc_dt
        days = delta.days
        seconds = delta.seconds

        if days > 365:
            years = days // 365
            return f"{years} year ago" if years == 1 else f"{years} years ago"
        if days > 30:
            months = days // 30
            return f"{months} month ago" if months == 1 else f"{months} months ago"
        if days > 0:
            return f"{days} day ago" if days == 1 else f"{days} days ago"
        if seconds >= 3600:
            hours = seconds // 3600
            return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
        if seconds >= 60:
            minutes = seconds // 60
            return f"{minutes} min ago" if minutes == 1 else f"{minutes} mins ago"
        return "just now"

    def to_response(self, video: Video) -> VideoResponse:
        categories = (
            [c for c in (video.categories or "").split(",") if c] if video.categories else []
        )
        tags = [t for t in (video.tags or "").split(",") if t] if video.tags else []

        views_text = self._format_number(video.view_count)
        duration_text = self._format_duration(video.duration_seconds)
        published_text = self._relative_time(video.published_at)

        stats_parts: list[str] = []
        if video.like_count is not None:
            stats_parts.append(f"{self._format_number(video.like_count)} likes")
        if video.comment_count is not None:
            stats_parts.append(f"{self._format_number(video.comment_count)} comments")
        stats_text = " • ".join([p for p in stats_parts if p])

        return VideoResponse(
            id=video.id,
            title=video.title,
            description=video.description,
            platform=video.platform,
            channel=video.channel_title,
            channel_id=video.channel_id,
            thumbnail=video.thumbnail_url,
            url=video.url,
            views=video.view_count,
            views_text=f"{views_text} views" if views_text else None,
            likes=video.like_count,
            comments=video.comment_count,
            duration_seconds=video.duration_seconds,
            duration_text=duration_text,
            stats_text=stats_text or None,
            published_at=video.published_at,
            published_time_text=published_text,
            categories=categories,
            tags=tags,
        )