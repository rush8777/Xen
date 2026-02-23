"""
vector_retrieval_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Handles query embedding generation and cosine similarity search across
VideoSubInterval records.

All DB access is synchronous (SQLAlchemy ORM). Call from async contexts
via run_in_executor or directly from sync code.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Similarity thresholds
DEFAULT_SIMILARITY_THRESHOLD = 0.3
CONTENT_SPECIFIC_THRESHOLD = 0.25
MAX_FIELD_CHARS = 20000
MAX_CHUNK_CHARS = 80000

# Content type mappings
CONTENT_KEYWORDS: dict[str, list[str]] = {
    "motion": ["motion", "movement", "moving", "action", "dynamic"],
    "camera": ["camera", "shot", "angle", "perspective", "view"],
    "environment": ["environment", "background", "setting", "location"],
    "people": ["people", "person", "character", "figure", "human"],
    "objects": ["object", "item", "prop", "thing"],
    "lighting": ["lighting", "light", "bright", "dark", "shadow"],
    "audio": ["audio", "sound", "music", "noise", "voice"],
}

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class RetrievedInterval:
    """A single retrieved interval with its similarity score and metadata."""

    source: str  # "sub_interval" | "premium_structural" | "premium_psychological" | "premium_performance" | "premium_transcript" | "premium_verification"
    interval_id: int
    video_id: int
    start_time_seconds: int
    end_time_seconds: int
    similarity: float  # 0.0 - 1.0

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

    # Interval-level field (unused when only sub-intervals are stored)
    combined_interval_text: Optional[str] = None
    premium_combined_text: Optional[str] = None


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


def _truncate(text: Optional[str], limit: int) -> Optional[str]:
    if not text:
        return None
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(0, limit - 3)].rstrip() + "..."


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class VectorRetrievalService:
    """
    Retrieves relevant video intervals for a user query using:
      1. Gemini gemini-embedding-001 for query embedding generation.
      2. In-memory cosine similarity against stored sub-interval embeddings.
      3. Ranked, de-duplicated context assembly.

    Falls back gracefully to text-only search when embeddings are absent.
    """

    # Embedding model name for `client.models.embed_content`.
    # (Unlike `generate_content`, this API expects the bare model name.)
    EMBEDDING_MODEL = "gemini-embedding-001"
    # Current gemini-embedding-001 output dimension.
    # (Keep in sync with what we store in DB; cosine similarity requires equal lengths.)
    MAX_EMBEDDING_DIM = 3072

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
                    contents=[query_text],
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
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        content_filter: Optional[str] = None,
    ) -> list[RetrievedInterval]:
        """
        Search vector-backed interval tables for the given project's video. Returns
        up to `limit` results ranked by similarity.

        When `query_embedding` is None (embedding generation failed), falls
        back to returning the first N intervals as context.
        """
        from ..models import (
            AnalysisEmbedding,
            AnalysisInterval,
            AnalysisRecord,
            PremiumPerformanceInterval,
            PremiumPerformanceIntervalEmbedding,
            PremiumPsychologicalInterval,
            PremiumPsychologicalIntervalEmbedding,
            PremiumStructuralInterval,
            PremiumStructuralIntervalEmbedding,
            PremiumTranscriptInterval,
            PremiumTranscriptIntervalEmbedding,
            PremiumVerificationInterval,
            PremiumVerificationIntervalEmbedding,
            Project,
            SubVideoIntervalEmbedding,
            VideoSubInterval,
        )

        # Resolve the video_id for this project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.video_id:
            logger.debug("[VectorRetrieval] No video linked to project %s", project_id)
            return []

        video_id: int = project.video_id
        results: list[RetrievedInterval] = []

        if not content_filter:
            content_filter = self.detect_content_type(query_text)

        effective_threshold = (
            min(similarity_threshold, CONTENT_SPECIFIC_THRESHOLD)
            if content_filter
            else similarity_threshold
        )

        unified_results = self._search_unified_analysis_records(
            db=db,
            project_id=project_id,
            query_embedding=query_embedding,
            query_text=query_text,
            similarity_threshold=effective_threshold,
            content_filter=content_filter,
            analysis_interval_model=AnalysisInterval,
            analysis_record_model=AnalysisRecord,
            analysis_embedding_model=AnalysisEmbedding,
        )
        if unified_results:
            return self._sort_deduplicate_limit(unified_results, limit=limit)

        # ------------------------------------------------------------------
        # Search VideoSubInterval table
        # ------------------------------------------------------------------
        sub_intervals = (
            db.query(VideoSubInterval, SubVideoIntervalEmbedding)
            .outerjoin(
                SubVideoIntervalEmbedding,
                SubVideoIntervalEmbedding.sub_interval_id == VideoSubInterval.id,
            )
            .filter(VideoSubInterval.video_id == video_id)
            .all()
        )

        def _collect_subintervals(active_filter: Optional[str]) -> None:
            for si, emb in sub_intervals:
                if not self._matches_content_filter(
                    {
                        "camera_frame": si.camera_frame,
                        "environment_background": si.environment_background,
                        "people_figures": si.people_figures,
                        "objects_props": si.objects_props,
                        "text_symbols": si.text_symbols,
                        "motion_changes": si.motion_changes,
                        "lighting_color": si.lighting_color,
                        "audio_visible_indicators": si.audio_visible_indicators,
                        "occlusions_limits": si.occlusions_limits,
                        "raw_combined_text": si.raw_combined_text,
                    },
                    active_filter,
                ):
                    continue

                embedding = _parse_embedding(emb.embedding if emb else None)
                if query_embedding and embedding:
                    similarity = _cosine_similarity(query_embedding, embedding)
                    if similarity < effective_threshold:
                        continue
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

        _collect_subintervals(content_filter)
        if not results and content_filter:
            _collect_subintervals(None)

        # ------------------------------------------------------------------
        # Search premium interval embedding tables
        # ------------------------------------------------------------------
        premium_sources = [
            (
                "premium_structural",
                PremiumStructuralInterval,
                PremiumStructuralIntervalEmbedding,
                PremiumStructuralIntervalEmbedding.structural_interval_id,
            ),
            (
                "premium_psychological",
                PremiumPsychologicalInterval,
                PremiumPsychologicalIntervalEmbedding,
                PremiumPsychologicalIntervalEmbedding.psychological_interval_id,
            ),
            (
                "premium_performance",
                PremiumPerformanceInterval,
                PremiumPerformanceIntervalEmbedding,
                PremiumPerformanceIntervalEmbedding.performance_interval_id,
            ),
            (
                "premium_transcript",
                PremiumTranscriptInterval,
                PremiumTranscriptIntervalEmbedding,
                PremiumTranscriptIntervalEmbedding.transcript_interval_id,
            ),
            (
                "premium_verification",
                PremiumVerificationInterval,
                PremiumVerificationIntervalEmbedding,
                PremiumVerificationIntervalEmbedding.verification_interval_id,
            ),
        ]

        for source_name, interval_model, emb_model, emb_fk in premium_sources:
            rows = (
                db.query(interval_model, emb_model)
                .outerjoin(
                    emb_model,
                    emb_fk == interval_model.id,
                )
                .filter(interval_model.project_id == project_id)
                .all()
            )
            for interval_row, emb_row in rows:
                embedding = _parse_embedding(emb_row.embedding if emb_row else None)
                if query_embedding and embedding:
                    similarity = _cosine_similarity(query_embedding, embedding)
                    if similarity < effective_threshold:
                        continue
                elif query_embedding is None:
                    similarity = 0.5
                else:
                    similarity = 0.0

                premium_text = (emb_row.combined_text if emb_row else None) or ""
                if content_filter:
                    filter_terms = CONTENT_KEYWORDS.get(content_filter, [])
                    if filter_terms and not any(t in premium_text.lower() for t in filter_terms):
                        continue

                results.append(
                    RetrievedInterval(
                        source=source_name,
                        interval_id=interval_row.interval_id,
                        video_id=interval_row.video_id,
                        start_time_seconds=interval_row.start_time_seconds,
                        end_time_seconds=interval_row.end_time_seconds,
                        similarity=similarity,
                        premium_combined_text=emb_row.combined_text if emb_row else None,
                    )
                )

        # ------------------------------------------------------------------
        # Sort, de-duplicate by time window, apply limit
        # ------------------------------------------------------------------
        return self._sort_deduplicate_limit(results, limit=limit)

    def _search_unified_analysis_records(
        self,
        *,
        db: Session,
        project_id: int,
        query_embedding: Optional[list[float]],
        query_text: str,
        similarity_threshold: float,
        content_filter: Optional[str],
        analysis_interval_model: Any,
        analysis_record_model: Any,
        analysis_embedding_model: Any,
    ) -> list[RetrievedInterval]:
        rows = (
            db.query(analysis_interval_model, analysis_record_model, analysis_embedding_model)
            .join(
                analysis_record_model,
                analysis_record_model.interval_id == analysis_interval_model.id,
            )
            .outerjoin(
                analysis_embedding_model,
                analysis_embedding_model.analysis_record_id == analysis_record_model.id,
            )
            .filter(
                analysis_interval_model.project_id == project_id,
                analysis_record_model.status == "completed",
            )
            .all()
        )
        if not rows:
            return []

        results: list[RetrievedInterval] = []
        for interval_row, record_row, embedding_row in rows:
            summary_text = (record_row.summary_text or "").strip()
            payload_raw = record_row.payload_json
            payload: dict[str, Any] = {}
            if payload_raw:
                try:
                    parsed_payload = json.loads(payload_raw)
                    if isinstance(parsed_payload, dict):
                        payload = parsed_payload
                except (json.JSONDecodeError, TypeError, ValueError):
                    payload = {}

            searchable_text = "\n".join(
                part for part in [summary_text, json.dumps(payload) if payload else ""] if part
            ).lower()
            if content_filter:
                terms = CONTENT_KEYWORDS.get(content_filter, [])
                if terms and not any(term in searchable_text for term in terms):
                    continue

            embedding = _parse_embedding(embedding_row.embedding if embedding_row else None)
            if query_embedding and embedding:
                similarity = _cosine_similarity(query_embedding, embedding)
                if similarity < similarity_threshold:
                    continue
            elif query_embedding is None:
                similarity = 0.5
            else:
                similarity = 0.0

            analysis_type = (record_row.analysis_type or "analysis").strip() or "analysis"
            result = RetrievedInterval(
                source=analysis_type,
                interval_id=interval_row.id,
                video_id=interval_row.video_id,
                start_time_seconds=interval_row.start_time_seconds,
                end_time_seconds=interval_row.end_time_seconds,
                similarity=similarity,
                premium_combined_text=summary_text or None,
            )
            if analysis_type == "vision_raw":
                result.camera_frame = payload.get("camera_frame")
                result.environment_background = payload.get("environment_background")
                result.people_figures = payload.get("people_figures")
                result.objects_props = payload.get("objects_props")
                result.text_symbols = payload.get("text_symbols")
                result.motion_changes = payload.get("motion_changes")
                result.lighting_color = payload.get("lighting_color")
                result.audio_visible_indicators = payload.get("audio_visible_indicators")
                result.occlusions_limits = payload.get("occlusions_limits")
                result.raw_combined_text = payload.get("raw_combined_text") or summary_text
            results.append(result)

        if not results and query_text:
            logger.debug(
                "[VectorRetrieval] Unified schema had rows but no matches for project %s.",
                project_id,
            )
        return results

    def _sort_deduplicate_limit(
        self,
        rows: list[RetrievedInterval],
        *,
        limit: int,
    ) -> list[RetrievedInterval]:
        rows.sort(key=lambda r: r.similarity, reverse=True)
        seen_keys: set[tuple[str, int, int]] = set()
        deduplicated: list[RetrievedInterval] = []
        for r in rows:
            key = (r.source, r.start_time_seconds, r.end_time_seconds)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduplicated.append(r)
            if len(deduplicated) >= limit:
                break
        return deduplicated

    # ------------------------------------------------------------------
    # Content filtering helpers
    # ------------------------------------------------------------------

    def detect_content_type(self, query: str) -> Optional[str]:
        """Detect what type of content the user is asking about."""
        query_lower = (query or "").lower()
        for content_type, words in CONTENT_KEYWORDS.items():
            if any(word in query_lower for word in words):
                return content_type
        return None

    def _matches_content_filter(
        self, interval_data: dict[str, Any], content_filter: Optional[str]
    ) -> bool:
        """Check if interval contains relevant content for the filter."""
        if not content_filter:
            return True

        filter_map = {
            "motion": ["motion_changes", "raw_combined_text"],
            "camera": ["camera_frame"],
            "environment": ["environment_background"],
            "people": ["people_figures"],
            "objects": ["objects_props"],
            "lighting": ["lighting_color"],
            "audio": ["audio_visible_indicators"],
        }

        relevant_fields = filter_map.get(content_filter.lower(), [])
        for field in relevant_fields:
            value = interval_data.get(field)
            if value and len(value.strip()) > 10:
                return True
        return False

    def format_retrieved_context(
        self,
        intervals: list[RetrievedInterval],
        *,
        content_filter: Optional[str] = None,
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

            if r.source in {"sub_interval", "vision_raw"}:
                filter_map = {
                    "motion": [("Motion", r.motion_changes)],
                    "camera": [("Camera", r.camera_frame)],
                    "environment": [("Environment", r.environment_background)],
                    "people": [("People", r.people_figures)],
                    "objects": [("Objects", r.objects_props)],
                    "lighting": [("Lighting", r.lighting_color)],
                    "audio": [("Audio cues", r.audio_visible_indicators)],
                }
                if content_filter:
                    field_list = filter_map.get(content_filter or "", [])
                    for label, val in field_list:
                        truncated = _truncate(val, MAX_FIELD_CHARS)
                        if truncated:
                            lines.append(f"  {label}: {truncated}")
                elif r.raw_combined_text:
                    summary = _truncate(r.raw_combined_text, MAX_CHUNK_CHARS)
                    if summary:
                        lines.append(f"  Summary: {summary}")
                else:
                    field_list = [
                        ("Camera", r.camera_frame),
                        ("Environment", r.environment_background),
                        ("People", r.people_figures),
                        ("Objects", r.objects_props),
                        ("Text/Symbols", r.text_symbols),
                        ("Motion", r.motion_changes),
                        ("Lighting", r.lighting_color),
                        ("Audio cues", r.audio_visible_indicators),
                        ("Occlusions", r.occlusions_limits),
                    ]
                    for label, val in field_list:
                        truncated = _truncate(val, MAX_FIELD_CHARS)
                        if truncated:
                            lines.append(f"  {label}: {truncated}")
            elif r.combined_interval_text:
                if r.combined_interval_text:
                    lines.append(
                        f"  {_truncate(r.combined_interval_text, MAX_CHUNK_CHARS)}"
                    )
            elif r.premium_combined_text:
                source_label = {
                    "vision_raw": "Visual interval",
                    "vector_interval_summary": "Interval summary",
                    "premium_structural": "Premium structural",
                    "premium_psychological": "Premium psychological",
                    "premium_performance": "Premium performance",
                    "premium_transcript": "Premium transcript",
                    "premium_verification": "Premium verification",
                }.get(r.source, "Premium")
                lines.append(f"  Source: {source_label}")
                lines.append(
                    f"  Summary: {_truncate(r.premium_combined_text, MAX_CHUNK_CHARS)}"
                )

            chunk = "\n".join(lines)
            if len(chunk) > MAX_CHUNK_CHARS:
                chunk = chunk[: max(0, MAX_CHUNK_CHARS - 3)].rstrip() + "..."
            chunks.append(chunk)

        return chunks
