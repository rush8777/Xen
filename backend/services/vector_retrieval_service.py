"""
vector_retrieval_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Handles query embedding generation and cosine similarity search across
VideoSubInterval and IntervalEmbedding tables.

All DB access is synchronous (SQLAlchemy ORM). Call from async contexts
via run_in_executor or directly from sync code.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class RetrievedInterval:
    """A single retrieved interval with its similarity score and metadata."""

    source: str  # "sub_interval" | "interval_embedding"
    interval_id: int
    video_id: int
    start_time_seconds: int
    end_time_seconds: int
    similarity: float  # 0.0 – 1.0

    # Sub-interval fields (may be None for interval-level results)
    camera_frame: Optional[str] = None
    environment_background: Optional[str] = None
    people_figures: Optional[str] = None
    objects_props: Optional[str] = None
    text_symbols: Optional[str] = None
    motion_changes: Optional[str] = None
    lighting_color: Optional[str] = None
    audio_visible_indicators: Optional[str] = None
    occlusions_limits: Optional[str] = None
    raw_combined_text: Optional[str] = None

    # Interval-level field
    combined_interval_text: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_embedding(raw: Optional[str]) -> Optional[list[float]]:
    """Parse JSON-encoded embedding string to float list. Returns None on error."""
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and parsed:
            return [float(v) for v in parsed]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _seconds_to_timestamp(seconds: int) -> str:
    """Convert integer seconds to MM:SS string."""
    m, s = divmod(max(0, seconds), 60)
    return f"{m:02d}:{s:02d}"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VectorRetrievalService:
    """
    Retrieves relevant video intervals for a user query using:
      1. Gemini gemini-embedding-001 for query embedding generation.
      2. In-memory cosine similarity against stored embeddings.
      3. Ranked, de-duplicated context assembly.

    Falls back gracefully to text-only search when embeddings are absent.
    """

    EMBEDDING_MODEL = "models/gemini-embedding-001"
    MAX_EMBEDDING_DIM = 768  # gemini-embedding-001 output dimension

    def __init__(self) -> None:
        from ..gemini_backend.gemini_client import client as _gemini_client  # lazy
        self._client = _gemini_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_query_embedding(self, query_text: str) -> Optional[list[float]]:
        """
        Call Gemini gemini-embedding-001 to embed the user query.
        Returns None on failure so callers can fall back gracefully.
        """
        import asyncio

        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: self._client.models.embed_content(
                    model=self.EMBEDDING_MODEL,
                    contents=query_text,
                ),
            )
            embedding = result.embeddings[0].values if result.embeddings else None
            if embedding:
                return list(embedding)
        except Exception as exc:
            logger.warning("[VectorRetrieval] Embedding generation failed: %s", exc)
        return None

    def search_similar_intervals(
        self,
        *,
        db: Session,
        project_id: int,
        query_embedding: Optional[list[float]],
        query_text: str,
        limit: int = 5,
    ) -> list[RetrievedInterval]:
        """
        Search VideoSubInterval and IntervalEmbedding tables for the given
        project's video.  Returns up to `limit` results ranked by similarity.

        When `query_embedding` is None (embedding generation failed), falls
        back to returning the first N intervals as context.
        """
        from ..models import Project, VideoSubInterval, IntervalEmbedding, VideoInterval

        # Resolve the video_id for this project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.video_id:
            logger.debug("[VectorRetrieval] No video linked to project %s", project_id)
            return []

        video_id: int = project.video_id
        results: list[RetrievedInterval] = []

        # ------------------------------------------------------------------
        # Search VideoSubInterval table
        # ------------------------------------------------------------------
        sub_intervals = (
            db.query(VideoSubInterval)
            .filter(VideoSubInterval.video_id == video_id)
            .all()
        )

        for si in sub_intervals:
            embedding = _parse_embedding(si.embedding)
            if query_embedding and embedding:
                similarity = _cosine_similarity(query_embedding, embedding)
            elif query_embedding is None:
                # Fallback: use index-based pseudo-score so early intervals surface
                similarity = 0.5
            else:
                similarity = 0.0

            results.append(
                RetrievedInterval(
                    source="sub_interval",
                    interval_id=si.interval_id,
                    video_id=si.video_id,
                    start_time_seconds=si.start_time_seconds,
                    end_time_seconds=si.end_time_seconds,
                    similarity=similarity,
                    camera_frame=si.camera_frame,
                    environment_background=si.environment_background,
                    people_figures=si.people_figures,
                    objects_props=si.objects_props,
                    text_symbols=si.text_symbols,
                    motion_changes=si.motion_changes,
                    lighting_color=si.lighting_color,
                    audio_visible_indicators=si.audio_visible_indicators,
                    occlusions_limits=si.occlusions_limits,
                    raw_combined_text=si.raw_combined_text,
                )
            )

        # ------------------------------------------------------------------
        # Search IntervalEmbedding table
        # ------------------------------------------------------------------
        interval_embeddings = (
            db.query(IntervalEmbedding, VideoInterval)
            .join(VideoInterval, IntervalEmbedding.interval_id == VideoInterval.id)
            .filter(IntervalEmbedding.video_id == video_id)
            .all()
        )

        for ie, vi in interval_embeddings:
            embedding = _parse_embedding(ie.embedding)
            if query_embedding and embedding:
                similarity = _cosine_similarity(query_embedding, embedding)
            elif query_embedding is None:
                similarity = 0.45
            else:
                similarity = 0.0

            results.append(
                RetrievedInterval(
                    source="interval_embedding",
                    interval_id=vi.id,
                    video_id=ie.video_id,
                    start_time_seconds=vi.start_time_seconds,
                    end_time_seconds=vi.end_time_seconds,
                    similarity=similarity,
                    combined_interval_text=ie.combined_interval_text,
                )
            )

        # ------------------------------------------------------------------
        # Sort, de-duplicate by time window, apply limit
        # ------------------------------------------------------------------
        results.sort(key=lambda r: r.similarity, reverse=True)
        seen_windows: set[tuple[int, int]] = set()
        deduplicated: list[RetrievedInterval] = []
        for r in results:
            window = (r.start_time_seconds, r.end_time_seconds)
            if window not in seen_windows:
                seen_windows.add(window)
                deduplicated.append(r)
            if len(deduplicated) >= limit:
                break

        return deduplicated

    def format_retrieved_context(
        self, intervals: list[RetrievedInterval]
    ) -> list[str]:
        """
        Convert RetrievedInterval objects into human-readable context strings
        suitable for inclusion in a Gemini system prompt.
        """
        if not intervals:
            return []

        chunks: list[str] = []
        for r in intervals:
            ts_start = _seconds_to_timestamp(r.start_time_seconds)
            ts_end = _seconds_to_timestamp(r.end_time_seconds)
            score_pct = f"{r.similarity * 100:.0f}%"
            header = f"[{ts_start}–{ts_end}] (relevance: {score_pct})"

            lines: list[str] = [header]

            if r.source == "sub_interval":
                for label, val in [
                    ("Camera", r.camera_frame),
                    ("Environment", r.environment_background),
                    ("People", r.people_figures),
                    ("Objects", r.objects_props),
                    ("Text/Symbols", r.text_symbols),
                    ("Motion", r.motion_changes),
                    ("Lighting", r.lighting_color),
                    ("Audio cues", r.audio_visible_indicators),
                    ("Occlusions", r.occlusions_limits),
                ]:
                    if val:
                        lines.append(f"  {label}: {val}")
                if r.raw_combined_text:
                    lines.append(f"  Summary: {r.raw_combined_text}")
            else:
                if r.combined_interval_text:
                    lines.append(f"  {r.combined_interval_text}")

            chunks.append("\n".join(lines))

        return chunks
