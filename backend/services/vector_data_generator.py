"""
vector_data_generator.py
~~~~~~~~~~~~~~~~~~~~~~~~
Background service that generates structured video interval data via Gemini
and inserts it into VideoInterval, VideoSubInterval, and
SubVideoIntervalEmbedding tables.

The Gemini prompt is configurable via VECTOR_PROMPT_TEMPLATE in config or
overridden at call-site. The JSON schema Gemini must return is documented
below and maps 1-to-1 with the ORM models.

Expected Gemini JSON schema
----------------------------
{
    "intervals": [
    {
      "interval_index": 0,          // int, 0-based
      "start_time_seconds": 0,      // int
      "end_time_seconds": 20,       // int
      "sub_intervals": [
        {
          "sub_index": 0,                        // int, 0-based within interval
          "start_time_seconds": 0,               // int
          "end_time_seconds": 10,                // int
          "camera_frame": "...",                 // str | null
          "environment_background": "...",       // str | null
          "people_figures": "...",               // str | null
          "objects_props": "...",                // str | null
          "text_symbols": "...",                 // str | null
          "motion_changes": "...",               // str | null
          "lighting_color": "...",               // str | null
          "audio_visible_indicators": "...",     // str | null
          "occlusions_limits": "...",            // str | null
          "raw_combined_text": "...",            // str | null
          "embedding": [0.1, 0.2, ...]          // list[float] | null (stored in sub_video_interval_embeddings)
        }
      ],
      "combined_interval_text": "...",           // str | null  (for IntervalEmbedding)
      "interval_embedding": [0.1, 0.2, ...]     // list[float] | null
    }
  ]
}
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default prompt template
# The prompt is intentionally kept separate so it can be swapped without
# touching any other logic. Callers can override by passing prompt_template.
# ---------------------------------------------------------------------------

DEFAULT_VECTOR_PROMPT_TEMPLATE = """

ROLE

You are a computer-vision reporting system, not an analyst, narrator, or summarizer.
Your job is to produce a ground-truth visual log.

You are given one single continuous video in full.
You have access to the entire video timeline, but you must still report observations at fixed 20-second intervals.

TEMPORAL RULES (ABSOLUTE)

Observe the video at exact 20-second intervals starting from 00:00–00:20 
Continue sequentially until the video ends
DO NOT skip any interval
DO NOT merge intervals
Each interval must have its own complete description, even if nothing changes
Intervals are time-based, not clip-based

OBSERVATION-ONLY RULES (ANTI-HALLUCINATION CORE)

You MUST:

Describe only what is directly visible on screen
Use literal, surface-level language
Prefer explicit uncertainty over guessing
State visibility limits clearly

You MUST NOT:

Infer intent, emotion, purpose, or cause
Assume continuity beyond what is visible
Identify people unless identity is explicitly shown as readable on-screen text
Guess obscured or off-screen elements
Use interpretive phrases such as:

"appears to be"
"seems"
"probably"
"likely"
"suggests"

If something cannot be verified visually, state:

"Not visually identifiable."

REQUIRED OUTPUT STRUCTURE (MANDATORY)

Use the following structure for every interval:

INTERVAL: [MM:SS – MM:SS]

1. CAMERA & FRAME
2. ENVIRONMENT & BACKGROUND
3. PEOPLE / HUMAN FIGURES
4. OBJECTS & PROPS
5. TEXT & SYMBOLS
6. MOTION & CHANGES
7. LIGHTING & COLOR
8. AUDIO-VISIBLE INDICATORS
9. OCCLUSIONS & VISIBILITY LIMITS

SECTION RULES
**Should contain 200 words for each section**

1. CAMERA & FRAME

Camera position (static / moving / panning / zooming)
Framing (wide, medium, close-up)
Orientation (landscape / portrait)
On-screen overlays or UI elements

2. ENVIRONMENT & BACKGROUND

Physical setting only if visually obvious
Visible surfaces, structures, scenery
Foreground / midground / background elements

3. PEOPLE / HUMAN FIGURES

If present:

Count of individuals
Clothing, posture, visible physical traits
Observable actions only

No emotions, roles, or identity assumptions.

4. OBJECTS & PROPS

All visible objects
Shape, color, size (relative), material if visually clear
Position and motion state

5. TEXT & SYMBOLS

Transcribe text exactly as shown
Preserve case and spelling
If unreadable: state so explicitly

6. MOTION & CHANGES

Describe visible motion within the interval
If no motion: explicitly state "No visible motion"

7. LIGHTING & COLOR

Brightness level
Light sources if visible
Dominant colors and shadows

8. AUDIO-VISIBLE INDICATORS

Visual-only cues of sound (e.g., mouth movement, subtitles, microphones).
No audio inference.

9. OCCLUSIONS & VISIBILITY LIMITS

Cropped, blurred, obstructed elements
Any uncertainty or visibility limitation

FAILURE HANDLING

Blank or black frames must be described as such
Repeated scenes must still be fully described per interval
If nothing changes, still output all sections

FINAL HARD RULES

No summarization
No conclusions
No cross-interval reasoning
Skip if data is insufficient to analyze and keep a note "Cannot describe"
No compression or stylistic language
Accuracy over completeness

End output at the final interval only.

IMPORTANT: Return ONLY valid JSON matching this exact schema (no markdown fences, no explanations):

{
  "intervals": [
    {
      "interval_index": 0,
      "start_time_seconds": 0,
      "end_time_seconds": 20,
      "combined_interval_text": "string or null",
      "interval_embedding": null,
      "sub_intervals": [
        {
          "sub_index": 0,
          "start_time_seconds": 0,
          "end_time_seconds": 20,
          "camera_frame": "string or null",
          "environment_background": "string or null",
          "people_figures": "string or null",
          "objects_props": "string or null",
          "text_symbols": "string or null",
          "motion_changes": "string or null",
          "lighting_color": "string or null",
          "audio_visible_indicators": "string or null",
          "occlusions_limits": "string or null",
          "raw_combined_text": "string or null",
          "embedding": null
        }
      ]
    }
  ]
}
""".strip()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_embedding(embedding: Optional[List[float]]) -> Optional[str]:
    """Serialize a float list to a JSON string for DB storage."""
    if embedding is None:
        return None
    try:
        return json.dumps(embedding)
    except (TypeError, ValueError):
        return None


def _parse_intervals_json(text: str) -> Dict[str, Any]:
    """Parse and lightly validate the JSON returned by Gemini."""
    # Strip markdown fences if Gemini wraps the response
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        # Remove first line (```json or ```) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        stripped = "\n".join(inner).strip()

    data = json.loads(stripped)
    if not isinstance(data, dict) or "intervals" not in data:
        raise ValueError("Gemini JSON must contain an 'intervals' key")
    if not isinstance(data["intervals"], list):
        raise ValueError("'intervals' must be a list")
    return data


def _build_subinterval_text(sub_dict: Dict[str, Any]) -> str:
    """Create a deterministic text summary from sub-interval fields."""
    parts: List[str] = []
    for label, key in [
        ("Camera", "camera_frame"),
        ("Environment", "environment_background"),
        ("People", "people_figures"),
        ("Objects", "objects_props"),
        ("Text", "text_symbols"),
        ("Motion", "motion_changes"),
        ("Lighting", "lighting_color"),
        ("Audio", "audio_visible_indicators"),
        ("Occlusions", "occlusions_limits"),
    ]:
        value = sub_dict.get(key)
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                parts.append(f"{label}: {cleaned}")
    return "\n".join(parts)


async def _embed_texts(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generate Gemini text embeddings for a list of strings.
    Returns a list aligned to `texts`, with None for any failed item.
    """
    if not texts:
        return []

    from ..gemini_backend.gemini_client import client as _gemini_client  # lazy

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: _gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
            ),
        )
    except Exception as exc:
        logger.warning("[VectorGen] Embedding generation failed: %s", exc)
        return [None] * len(texts)

    embeddings: List[Optional[List[float]]] = []
    if not getattr(result, "embeddings", None):
        return [None] * len(texts)

    for emb in result.embeddings:
        values = getattr(emb, "values", None)
        if values:
            embeddings.append(list(values))
        else:
            embeddings.append(None)

    if len(embeddings) < len(texts):
        embeddings.extend([None] * (len(texts) - len(embeddings)))

    return embeddings


# ---------------------------------------------------------------------------
# Core DB insertion logic (sync, runs inside executor)
# ---------------------------------------------------------------------------


def _insert_vector_data(
    db: Session,
    video_id: int,
    intervals_data: List[Dict[str, Any]],
) -> None:
    """
    Insert parsed interval data into VideoInterval, VideoSubInterval, and
    SubVideoIntervalEmbedding tables. Skips records that already exist
    (idempotent).
    """
    from ..models import VideoInterval, VideoSubInterval, SubVideoIntervalEmbedding  # noqa: E402

    for interval_dict in intervals_data:
        interval_index = int(interval_dict.get("interval_index", 0))
        start_sec = int(interval_dict.get("start_time_seconds", 0))
        end_sec = int(interval_dict.get("end_time_seconds", start_sec + 20))

        # ------------------------------------------------------------------
        # Upsert VideoInterval
        # ------------------------------------------------------------------
        db_interval = (
            db.query(VideoInterval)
            .filter(
                VideoInterval.video_id == video_id,
                VideoInterval.interval_index == interval_index,
            )
            .first()
        )

        if not db_interval:
            db_interval = VideoInterval(
                video_id=video_id,
                interval_index=interval_index,
                start_time_seconds=start_sec,
                end_time_seconds=end_sec,
            )
            db.add(db_interval)
            db.flush()  # get db_interval.id

        # ------------------------------------------------------------------
        # Upsert VideoSubIntervals
        # ------------------------------------------------------------------
        for sub_dict in interval_dict.get("sub_intervals", []):
            sub_start = int(sub_dict.get("start_time_seconds", start_sec))

            existing_sub = (
                db.query(VideoSubInterval)
                .filter(
                    VideoSubInterval.video_id == video_id,
                    VideoSubInterval.start_time_seconds == sub_start,
                )
                .first()
            )
            serialized_embedding = _serialize_embedding(sub_dict.get("embedding"))
            if existing_sub:
                if serialized_embedding:
                    existing_embedding = (
                        db.query(SubVideoIntervalEmbedding)
                        .filter(
                            SubVideoIntervalEmbedding.sub_interval_id
                            == existing_sub.id
                        )
                        .first()
                    )
                    if not existing_embedding:
                        db.add(
                            SubVideoIntervalEmbedding(
                                sub_interval_id=existing_sub.id,
                                embedding=serialized_embedding,
                            )
                        )
                continue  # skip duplicate

            new_sub = VideoSubInterval(
                interval_id=db_interval.id,
                video_id=video_id,
                sub_index=int(sub_dict.get("sub_index", 0)),
                start_time_seconds=sub_start,
                end_time_seconds=int(sub_dict.get("end_time_seconds", sub_start + 20)),
                camera_frame=sub_dict.get("camera_frame"),
                environment_background=sub_dict.get("environment_background"),
                people_figures=sub_dict.get("people_figures"),
                objects_props=sub_dict.get("objects_props"),
                text_symbols=sub_dict.get("text_symbols"),
                motion_changes=sub_dict.get("motion_changes"),
                lighting_color=sub_dict.get("lighting_color"),
                audio_visible_indicators=sub_dict.get("audio_visible_indicators"),
                occlusions_limits=sub_dict.get("occlusions_limits"),
                raw_combined_text=sub_dict.get("raw_combined_text"),
            )
            db.add(new_sub)
            db.flush()  # get new_sub.id

            if serialized_embedding:
                db.add(
                    SubVideoIntervalEmbedding(
                        sub_interval_id=new_sub.id,
                        embedding=serialized_embedding,
                    )
                )

    db.commit()


# ---------------------------------------------------------------------------
# Public async entry-point
# ---------------------------------------------------------------------------


async def generate_vector_data_for_project(
    project_id: int,
    prompt_template: Optional[str] = None,
    max_retries: int = 3,
) -> None:
    """
    Background coroutine: generate vector data for the given project.

    Flow:
      1. Load project from DB.
      2. Mark status = 'pending'.
      3. Call Gemini with cached video + vector prompt.
      4. Parse JSON and insert into vector tables.
      5. Mark status = 'completed' (or 'failed' on error with retry logic).

    This function is designed to be launched as an asyncio task (fire-and-forget).
    """
    from ..database import SessionLocal
    from ..models import Project
    from ..gemini_backend.gemini_client import call_gemini_with_cached_video

    prompt = prompt_template or DEFAULT_VECTOR_PROMPT_TEMPLATE

    db = SessionLocal()
    try:
        # ------------------------------------------------------------------
        # Load project
        # ------------------------------------------------------------------
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(
                "[VectorGen] Project %s not found – aborting.", project_id
            )
            return

        if not project.gemini_cached_content_name:
            logger.warning(
                "[VectorGen] Project %s has no cached content – cannot generate "
                "vector data without a Gemini-cached video.",
                project_id,
            )
            project.vector_generation_status = "failed"
            project.vector_generation_error = (
                "No Gemini cached content available for this project."
            )
            db.commit()
            return

        if not project.video_id:
            logger.warning(
                "[VectorGen] Project %s has no video_id – cannot insert vector "
                "records without a linked video.",
                project_id,
            )
            project.vector_generation_status = "failed"
            project.vector_generation_error = (
                "Project has no linked video record (video_id is None)."
            )
            db.commit()
            return

        # ------------------------------------------------------------------
        # Mark pending
        # ------------------------------------------------------------------
        project.vector_generation_status = "pending"
        project.vector_generation_started_at = datetime.utcnow()
        project.vector_generation_error = None
        db.commit()
        logger.info("[VectorGen] Starting vector generation for project %s.", project_id)

        # ------------------------------------------------------------------
        # Call Gemini with retry
        # ------------------------------------------------------------------
        last_error: Exception | None = None
        raw_text: str | None = None

        for attempt in range(1, max_retries + 1):
            try:
                raw_text = await call_gemini_with_cached_video(
                    cached_content_name=project.gemini_cached_content_name,
                    prompt=prompt,
                    response_mime_type="application/json",
                )
                break  # success
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "[VectorGen] Gemini call failed (attempt %d/%d) for project %s: %s",
                    attempt,
                    max_retries,
                    project_id,
                    exc,
                )
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # exponential back-off

        if raw_text is None:
            raise RuntimeError(
                f"Gemini call failed after {max_retries} attempts: {last_error}"
            )

        # ------------------------------------------------------------------
        # Parse response
        # ------------------------------------------------------------------
        data = _parse_intervals_json(raw_text)
        intervals_list: List[Dict[str, Any]] = data["intervals"]
        logger.info(
            "[VectorGen] Parsed %d intervals for project %s.",
            len(intervals_list),
            project_id,
        )

        # ------------------------------------------------------------------
        # Ensure sub-interval embeddings exist (fallback to embedding API)
        # ------------------------------------------------------------------
        sub_texts: List[str] = []
        sub_targets: List[Tuple[Dict[str, Any], str]] = []
        for interval in intervals_list:
            for sub in interval.get("sub_intervals", []) or []:
                sub_raw_text = sub.get("raw_combined_text")
                if not sub_raw_text:
                    sub_raw_text = _build_subinterval_text(sub)
                    if sub_raw_text:
                        sub["raw_combined_text"] = sub_raw_text
                if sub_raw_text and not sub.get("embedding"):
                    sub_texts.append(sub_raw_text)
                    sub_targets.append((sub, "embedding"))

        if sub_texts:
            sub_embeddings = await _embed_texts(sub_texts)
            for (target, key), emb in zip(sub_targets, sub_embeddings):
                target[key] = emb

        # ------------------------------------------------------------------
        # Insert into DB (runs synchronously; wrap in executor for async safety)
        # ------------------------------------------------------------------
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            _insert_vector_data,
            db,
            project.video_id,
            intervals_list,
        )

        # ------------------------------------------------------------------
        # Mark completed
        # ------------------------------------------------------------------
        # Re-fetch to avoid stale object after executor
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.vector_generation_status = "completed"
            project.vector_generation_completed_at = datetime.utcnow()
            project.vector_generation_error = None
            db.commit()
            logger.info(
                "[VectorGen] Vector data generation completed for project %s.",
                project_id,
            )

            # Auto-trigger premium analysis (if not started) after vector completion.
            current_premium_status = project.premium_analysis_status or "not_started"
            if current_premium_status == "not_started":
                try:
                    from .premium_analysis_service import (
                        generate_premium_analysis_for_project,
                    )

                    asyncio.create_task(
                        generate_premium_analysis_for_project(project_id)
                    )
                    logger.info(
                        "[VectorGen] Auto-triggered premium analysis for project %s.",
                        project_id,
                    )
                except Exception as exc:
                    logger.warning(
                        "[VectorGen] Failed to auto-trigger premium analysis for project %s: %s",
                        project_id,
                        exc,
                    )

    except Exception as exc:
        logger.error(
            "[VectorGen] Vector data generation failed for project %s: %s",
            project_id,
            exc,
        )
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.vector_generation_status = "failed"
                project.vector_generation_error = str(exc)
                db.commit()
        except Exception as inner_exc:
            logger.error(
                "[VectorGen] Could not update failure status for project %s: %s",
                project_id,
                inner_exc,
            )
    finally:
        try:
            db.close()
        except Exception:
            pass
