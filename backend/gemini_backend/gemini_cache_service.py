from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from google.genai import types

from ..models import GeminiCache
from .gemini_client import client, upload_video_to_gemini, SYSTEM_INSTRUCTIONS


def calculate_video_hash(video_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(video_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _is_cache_valid(entry: GeminiCache) -> bool:
    if not entry.expires_at:
        return True
    return datetime.utcnow() < entry.expires_at


async def get_or_create_video_cache(
    *,
    db: Session,
    video_path: Path,
    prompt_template_key: str,
    ttl_seconds: int,
    model: str = "models/gemini-2.5-flash",
    display_name: str | None = None,
    system_instruction: str | None = None,
) -> GeminiCache:
    video_hash = calculate_video_hash(video_path)

    existing = (
        db.query(GeminiCache)
        .filter(
            GeminiCache.video_hash == video_hash,
            GeminiCache.prompt_template_key == prompt_template_key,
            GeminiCache.model == model,
        )
        .first()
    )

    if existing and _is_cache_valid(existing):
        return existing

    gemini_file_name = await upload_video_to_gemini(video_path)
    video_file = client.files.get(name=gemini_file_name)

    while getattr(video_file.state, "name", None) == "PROCESSING":
        await asyncio.sleep(2.5)
        video_file = client.files.get(name=video_file.name)

    if getattr(video_file.state, "name", None) != "ACTIVE":
        raise RuntimeError(
            f"Video file is not ACTIVE: {getattr(video_file.state, 'name', video_file.state)}"
        )

    cache_config_kwargs = {
        "display_name": display_name or f"{prompt_template_key}-{video_hash[:12]}",
        "system_instruction": system_instruction or SYSTEM_INSTRUCTIONS,
        "contents": [video_file],
    }
    if ttl_seconds > 0:
        cache_config_kwargs["ttl"] = f"{ttl_seconds}s"

    cache = client.caches.create(
        model=model,
        config=types.CreateCachedContentConfig(**cache_config_kwargs),
    )

    expires_at = (
        datetime.utcnow() + timedelta(seconds=ttl_seconds)
        if ttl_seconds > 0
        else None
    )

    if existing:
        entry = existing
        entry.gemini_file_name = video_file.name
        entry.gemini_file_uri = getattr(video_file, "uri", None)
        entry.cached_content_name = cache.name
        entry.ttl_seconds = ttl_seconds
        entry.expires_at = expires_at
    else:
        entry = GeminiCache(
            video_hash=video_hash,
            prompt_template_key=prompt_template_key,
            model=model,
            gemini_file_name=video_file.name,
            gemini_file_uri=getattr(video_file, "uri", None),
            cached_content_name=cache.name,
            ttl_seconds=ttl_seconds,
            expires_at=expires_at,
        )
        db.add(entry)

    db.commit()
    db.refresh(entry)
    return entry