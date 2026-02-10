from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import List, Optional

import httpx
from sqlalchemy.orm import Session

from ..models import OAuthConnection, User
from .video_library import VideoDTO


class YouTubeService:
    """
    Lightweight YouTube fetcher that uses stored OAuth tokens to retrieve
    the authenticated user's recent uploads.
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, access_token: str):
        self.access_token = access_token

    @classmethod
    def from_db(cls, db: Session, user: User) -> Optional["YouTubeService"]:
        conn = (
            db.query(OAuthConnection)
            .filter(
                OAuthConnection.user_id == user.id,
                OAuthConnection.provider == "youtube",
            )
            .first()
        )
        if not conn or not conn.access_token:
            return None
            
        # Check if token is expired (handle both timezone-aware and naive datetimes)
        if conn.expires_at:
            now = datetime.now(timezone.utc) if conn.expires_at.tzinfo else datetime.utcnow()
            if conn.expires_at < now:
                return None
            
        return cls(access_token=conn.access_token)

    def fetch_recent_videos(self, max_results: int = 25) -> list[VideoDTO]:
        """
        Fetch recent videos for the authenticated channel. Falls back gracefully
        on errors by returning an empty list.
        """
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            # First, search for user's videos
            search_resp = httpx.get(
                f"{self.BASE_URL}/search",
                params={
                    "part": "snippet",
                    "forMine": "true",
                    "type": "video",
                    "order": "date",
                    "maxResults": str(max_results),
                },
                headers=headers,
                timeout=10.0,
            )
            
            if search_resp.status_code != 200:
                # Print error for debugging
                print(f"YouTube API search error: {search_resp.status_code}")
                print(f"Response: {search_resp.text}")
                return []

            search_items = search_resp.json().get("items") or []
            video_ids = [
                (item.get("id") or {}).get("videoId")
                for item in search_items
                if (item.get("id") or {}).get("videoId")
            ]

            if not video_ids:
                print("No video IDs found in search results")
                return []

            # Second, get detailed video information
            videos_resp = httpx.get(
                f"{self.BASE_URL}/videos",
                params={
                    "part": "snippet,contentDetails,statistics",
                    "id": ",".join(video_ids),
                },
                headers=headers,
                timeout=10.0,
            )
            
            if videos_resp.status_code != 200:
                print(f"YouTube API videos error: {videos_resp.status_code}")
                print(f"Response: {videos_resp.text}")
                return []

            dtos: list[VideoDTO] = []
            for item in videos_resp.json().get("items") or []:
                snippet = item.get("snippet") or {}
                statistics = item.get("statistics") or {}
                content = item.get("contentDetails") or {}

                video_id = item.get("id")
                if not video_id:
                    continue

                dtos.append(
                    VideoDTO(
                        platform="youtube",
                        platform_video_id=video_id,
                        etag=item.get("etag"),
                        title=snippet.get("title") or "Untitled video",
                        description=snippet.get("description"),
                        channel_title=snippet.get("channelTitle"),
                        channel_id=snippet.get("channelId"),
                        channel_url=f"https://www.youtube.com/channel/{snippet.get('channelId')}"
                        if snippet.get("channelId")
                        else None,
                        thumbnail_url=_best_thumbnail(snippet.get("thumbnails") or {}),
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        published_at=_parse_datetime(snippet.get("publishedAt")),
                        duration_seconds=_parse_iso8601_duration(content.get("duration")),
                        view_count=_safe_int(statistics.get("viewCount")),
                        like_count=_safe_int(statistics.get("likeCount")),
                        comment_count=_safe_int(statistics.get("commentCount")),
                        tags=snippet.get("tags") or [],
                        categories=None,
                        raw=item,
                    )
                )

            print(f"Successfully fetched {len(dtos)} videos from YouTube")
            return dtos

        except Exception as e:
            print(f"YouTube API exception: {type(e).__name__}: {str(e)}")
            return []


def _safe_int(value) -> Optional[int]:
    try:
        return int(value)
    except Exception:
        return None


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Example: 2024-05-01T12:00:00Z
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


_DURATION_PATTERN = re.compile(
    r"P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?"
)


def _parse_iso8601_duration(duration: Optional[str]) -> Optional[int]:
    if not duration:
        return None
    match = _DURATION_PATTERN.fullmatch(duration)
    if not match:
        return None
    parts = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    total_seconds = (
        parts.get("days", 0) * 86400
        + parts.get("hours", 0) * 3600
        + parts.get("minutes", 0) * 60
        + parts.get("seconds", 0)
    )
    return total_seconds


def _best_thumbnail(thumbnails: dict) -> Optional[str]:
    for key in ("maxres", "standard", "high", "medium", "default"):
        thumb = thumbnails.get(key)
        if thumb and thumb.get("url"):
            return thumb["url"]
    return None