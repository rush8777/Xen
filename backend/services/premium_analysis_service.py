from __future__ import annotations

import asyncio
import ast
import json
import logging
import re
from datetime import datetime
from typing import Optional

from .premium_prompts import (
    PREMIUM_PROMPT_1,
    PREMIUM_PROMPT_2,
    PREMIUM_PROMPT_3,
    PREMIUM_PROMPT_4,
    PREMIUM_PROMPT_5,
)

logger = logging.getLogger(__name__)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        inner = lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
        return "\n".join(inner).strip()
    return stripped


def _extract_json_container(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


def _extract_first_valid_json_object(text: str) -> str:
    """
    Extract the first decodable JSON object from model output.
    This avoids greedy first-{ / last-} slicing when extra text is present.
    """
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[{[]", text):
        start = match.start()
        try:
            parsed, end = decoder.raw_decode(text[start:])
            if isinstance(parsed, dict):
                return text[start:start + end]
        except Exception:
            continue
    return text


def _quote_unquoted_keys(text: str) -> str:
    # Convert JSON-like object keys such as {foo: 1} to {"foo": 1}.
    return re.sub(
        r'([{\[,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)(\s*:)',
        r'\1"\2"\3',
        text,
    )


def _parse_json_with_fallbacks(text: str) -> dict:
    candidate = _strip_code_fence(text)
    candidate = candidate.replace("\ufeff", "")
    candidate = candidate.replace("“", "\"").replace("”", "\"").replace("’", "'")
    candidate = candidate.replace("\u2013", "-").replace("\u2014", "-")
    candidate = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", candidate)

    candidates: list[str] = [candidate]

    extracted_first = _extract_first_valid_json_object(candidate)
    if extracted_first != candidate:
        candidates.append(extracted_first)

    extracted = _extract_json_container(candidate)
    if extracted != candidate:
        candidates.append(extracted)

    for raw in list(candidates):
        no_trailing_commas = re.sub(r",(\s*[}\]])", r"\1", raw)
        if no_trailing_commas != raw:
            candidates.append(no_trailing_commas)
        quoted_keys = _quote_unquoted_keys(raw)
        if quoted_keys != raw:
            candidates.append(quoted_keys)
        if quoted_keys != raw:
            quoted_no_trailing = re.sub(r",(\s*[}\]])", r"\1", quoted_keys)
            if quoted_no_trailing != quoted_keys:
                candidates.append(quoted_no_trailing)
        # Heuristic: insert a missing comma between a closed string and next object key.
        missing_comma_between_keys = re.sub(
            r'(")\s*("(?=[^"]+"\s*:))',
            r'\1,\2',
            raw,
        )
        if missing_comma_between_keys != raw:
            candidates.append(missing_comma_between_keys)

    seen: set[str] = set()
    last_error: Exception | None = None
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception as exc:
            last_error = exc

        try:
            parsed_literal = ast.literal_eval(candidate)
            if isinstance(parsed_literal, dict):
                return parsed_literal
        except Exception:
            pass

    raise ValueError(f"Unable to parse model output as JSON object: {last_error}")


def _serialize_embedding(embedding: list[float] | None) -> str | None:
    if embedding is None:
        return None
    try:
        return json.dumps(embedding)
    except (TypeError, ValueError):
        return None


def _build_structural_text(row: "PremiumStructuralInterval") -> str:
    parts: list[str] = []
    for label, value in [
        ("Hook strength score", row.hook_strength_score),
        ("Hook strength justification", row.hook_strength_justification),
        ("Cuts per 20s", row.stimulation_cuts_per_20s),
        ("Camera variation", row.stimulation_camera_variation),
        ("Motion intensity", row.stimulation_motion_intensity),
        ("Stimulation justification", row.stimulation_justification),
        ("Escalation intensity increase", row.escalation_intensity_increase),
        ("Escalation stakes raised", row.escalation_stakes_raised),
        ("Escalation justification", row.escalation_justification),
        ("Information rate", row.cognitive_information_rate),
        ("Over explanation risk", row.cognitive_over_explanation_risk),
        ("Cognitive justification", row.cognitive_justification),
        ("Drop risk score percent", row.drop_risk_score_percent),
        ("Drop risk justification", row.drop_risk_justification),
    ]:
        if value is not None and str(value).strip():
            parts.append(f"{label}: {value}")
    return "\n".join(parts).strip()


def _build_psychological_text(row: "PremiumPsychologicalInterval") -> str:
    parts: list[str] = []
    for label, value in [
        ("Primary trigger type", row.primary_trigger_type),
        ("Primary trigger justification", row.primary_trigger_justification),
        ("Trigger intensity score", row.trigger_intensity_score),
        ("Trigger intensity justification", row.trigger_intensity_justification),
        ("Emotional arc pattern type", row.emotional_arc_pattern_type),
        ("Emotional arc justification", row.emotional_arc_justification),
        ("Attention sustainability type", row.attention_sustainability_type),
        ("Attention sustainability justification", row.attention_sustainability_justification),
        ("Viewer momentum score", row.viewer_momentum_score),
        ("Viewer momentum justification", row.viewer_momentum_justification),
    ]:
        if value is not None and str(value).strip():
            parts.append(f"{label}: {value}")
    return "\n".join(parts).strip()


def _build_performance_text(row: "PremiumPerformanceInterval") -> str:
    parts: list[str] = []
    for label, value in [
        ("Retention strength score", row.retention_strength_score),
        ("Retention strength justification", row.retention_strength_justification),
        ("Competitive density score", row.competitive_density_score),
        ("Competitive density justification", row.competitive_density_justification),
        ("TikTok score", row.platform_tiktok_score),
        ("TikTok justification", row.platform_tiktok_justification),
        ("Instagram Reels score", row.platform_instagram_reels_score),
        ("Instagram Reels justification", row.platform_instagram_reels_justification),
        ("YouTube Shorts score", row.platform_youtube_shorts_score),
        ("YouTube Shorts justification", row.platform_youtube_shorts_justification),
        ("Conversion leverage score", row.conversion_leverage_score),
        ("Conversion leverage justification", row.conversion_leverage_justification),
        ("Total performance index score", row.total_performance_index_score),
        ("Total performance index justification", row.total_performance_index_justification),
        ("Structural weakness priority JSON", row.structural_weakness_priority_json),
        ("Highest leverage target", row.highest_leverage_target),
        ("Highest leverage justification", row.highest_leverage_justification),
    ]:
        if value is not None and str(value).strip():
            parts.append(f"{label}: {value}")
    return "\n".join(parts).strip()


def _build_transcript_text(row: "PremiumTranscriptInterval") -> str:
    text = (row.transcript_text or "").strip()
    if not text:
        return ""
    return f"Transcript text: {text}"


def _build_verification_text(row: "PremiumVerificationInterval") -> str:
    parts: list[str] = []
    for label, value in [
        ("Question type", row.question_type),
        ("Timestamp reference", row.timestamp_reference),
        ("Visual evidence summary", row.visual_evidence_summary),
        ("Verification status", row.verification_status),
        ("Answer", row.answer),
    ]:
        if value is not None and str(value).strip():
            parts.append(f"{label}: {value}")
    return "\n".join(parts).strip()


def _parse_timestamp_seconds(timestamp_ref: object) -> Optional[int]:
    if not isinstance(timestamp_ref, str):
        return None
    cleaned = timestamp_ref.strip().replace("–", "-").replace("—", "-")
    match = re.match(r"^\s*(\d{1,2}):(\d{2})", cleaned)
    if not match:
        return None
    minutes = int(match.group(1))
    seconds = int(match.group(2))
    return minutes * 60 + seconds


async def _embed_texts(texts: list[str], *, chunk_size: int = 64) -> list[list[float] | None]:
    """
    Generate embeddings for a list of texts.
    Returns list aligned with `texts`, using None for failed items.
    """
    if not texts:
        return []

    from ..gemini_backend.gemini_client import client as _gemini_client  # lazy

    loop = asyncio.get_running_loop()
    all_embeddings: list[list[float] | None] = []

    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i + chunk_size]
        try:
            result = await loop.run_in_executor(
                None,
                lambda: _gemini_client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=chunk,
                ),
            )
        except Exception as exc:
            logger.warning("[PremiumAnalysis] Embedding generation failed: %s", exc)
            all_embeddings.extend([None] * len(chunk))
            continue

        chunk_embeddings: list[list[float] | None] = []
        if getattr(result, "embeddings", None):
            for emb in result.embeddings:
                values = getattr(emb, "values", None)
                chunk_embeddings.append(list(values) if values else None)

        if len(chunk_embeddings) < len(chunk):
            chunk_embeddings.extend([None] * (len(chunk) - len(chunk_embeddings)))

        all_embeddings.extend(chunk_embeddings)

    return all_embeddings


async def _call_with_retry(
    *,
    cached_content_name: str,
    prompt: str,
    max_retries: int,
) -> str:
    from ..gemini_backend.gemini_client import call_gemini_with_cached_video

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return await call_gemini_with_cached_video(
                cached_content_name=cached_content_name,
                prompt=prompt,
                response_mime_type="application/json",
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "[PremiumAnalysis] Gemini call failed (attempt %d/%d): %s",
                attempt,
                max_retries,
                exc,
            )
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
    raise RuntimeError(
        f"Gemini call failed after {max_retries} attempts: {last_error}"
    )


async def generate_premium_analysis_for_project(
    project_id: int,
    *,
    prompt_1: Optional[str] = None,
    prompt_2: Optional[str] = None,
    prompt_3: Optional[str] = None,
    prompt_4: Optional[str] = None,
    prompt_5: Optional[str] = None,
    max_retries: int = 3,
) -> None:
    """
    Background coroutine: generate premium 5-pass analysis for the given project.

    Flow:
      1. Load project and validate cached video exists.
      2. Mark project + premium analysis record as 'pending'.
      3. Run 5 sequential prompts:
         - Pass 1: Structural mechanics extraction (cached video).
         - Pass 2: Psychological leverage analysis (Pass 1 input).
         - Pass 3: Performance modeling (Pass 1 + Pass 2 inputs).
         - Pass 4: Transcript extraction (cached video + prior passes context).
         - Pass 5: Visual verification (cached video + prior passes context).
      4. Store outputs and mark 'completed' (or 'failed' on error).
    """
    from ..database import SessionLocal
    from ..models import (
        Project,
        ProjectPremiumAnalysis,
        PremiumIntervalAnalysis,
        PremiumStructuralInterval,
        PremiumStructuralIntervalEmbedding,
        PremiumPsychologicalInterval,
        PremiumPsychologicalIntervalEmbedding,
        PremiumPerformanceInterval,
        PremiumPerformanceIntervalEmbedding,
        PremiumTranscriptInterval,
        PremiumTranscriptIntervalEmbedding,
        PremiumVerificationInterval,
        PremiumVerificationIntervalEmbedding,
        VideoInterval,
    )
    from .unified_analysis_storage import (
        upsert_analysis_embedding,
        upsert_analysis_interval,
        upsert_analysis_record,
    )

    p1 = prompt_1 or PREMIUM_PROMPT_1
    p2 = prompt_2 or PREMIUM_PROMPT_2
    p3 = prompt_3 or PREMIUM_PROMPT_3
    p4 = prompt_4 or PREMIUM_PROMPT_4
    p5 = prompt_5 or PREMIUM_PROMPT_5

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(
                "[PremiumAnalysis] Project %s not found - aborting.", project_id
            )
            return

        if not project.gemini_cached_content_name:
            logger.warning(
                "[PremiumAnalysis] Project %s has no cached content - cannot run.",
                project_id,
            )
            project.premium_analysis_status = "failed"
            project.premium_analysis_error = (
                "No Gemini cached content available for this project."
            )
            db.commit()
            return

        analysis = (
            db.query(ProjectPremiumAnalysis)
            .filter(ProjectPremiumAnalysis.project_id == project_id)
            .first()
        )
        if not analysis:
            analysis = ProjectPremiumAnalysis(
                project_id=project_id,
                status="pending",
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)

        analysis.status = "pending"
        analysis.error = None

        project.premium_analysis_status = "pending"
        project.premium_analysis_started_at = datetime.utcnow()
        project.premium_analysis_error = None
        db.commit()

        logger.info("[PremiumAnalysis] Starting analysis for project %s.", project_id)

        # Pass 1: Structural mechanics
        pass_1_output = await _call_with_retry(
            cached_content_name=project.gemini_cached_content_name,
            prompt=p1,
            max_retries=max_retries,
        )

        # Pass 2: Psychological leverage
        pass_2_prompt = f"{p2}\n\nSTRUCTURAL MECHANICS OUTPUT:\n{pass_1_output}"
        pass_2_output = await _call_with_retry(
            cached_content_name=project.gemini_cached_content_name,
            prompt=pass_2_prompt,
            max_retries=max_retries,
        )

        # Pass 3: Performance modeling
        pass_3_prompt = (
            f"{p3}\n\nSTRUCTURAL MECHANICS OUTPUT:\n{pass_1_output}"
            f"\n\nPSYCHOLOGICAL LEVERAGE OUTPUT:\n{pass_2_output}"
        )
        pass_3_output = await _call_with_retry(
            cached_content_name=project.gemini_cached_content_name,
            prompt=pass_3_prompt,
            max_retries=max_retries,
        )

        # Pass 4: Transcript extraction
        pass_4_prompt = (
            f"{p4}\n\nSTRUCTURAL MECHANICS OUTPUT:\n{pass_1_output}"
            f"\n\nPSYCHOLOGICAL LEVERAGE OUTPUT:\n{pass_2_output}"
            f"\n\nPERFORMANCE MODELING OUTPUT:\n{pass_3_output}"
        )
        pass_4_output = await _call_with_retry(
            cached_content_name=project.gemini_cached_content_name,
            prompt=pass_4_prompt,
            max_retries=max_retries,
        )

        # Pass 5: Visual verification
        pass_5_prompt = (
            f"{p5}\n\nSTRUCTURAL MECHANICS OUTPUT:\n{pass_1_output}"
            f"\n\nPSYCHOLOGICAL LEVERAGE OUTPUT:\n{pass_2_output}"
            f"\n\nPERFORMANCE MODELING OUTPUT:\n{pass_3_output}"
            f"\n\nTRANSCRIPT OUTPUT:\n{pass_4_output}"
        )
        pass_5_output = await _call_with_retry(
            cached_content_name=project.gemini_cached_content_name,
            prompt=pass_5_prompt,
            max_retries=max_retries,
        )

        def _intervals_from(data: dict) -> list[dict]:
            intervals = data.get("intervals")
            if isinstance(intervals, list):
                return intervals
            return []

        # Parse JSON outputs for interval storage
        pass_1_json = _parse_json_with_fallbacks(pass_1_output)
        pass_2_json = _parse_json_with_fallbacks(pass_2_output)
        pass_3_json = _parse_json_with_fallbacks(pass_3_output)
        pass_4_json = _parse_json_with_fallbacks(pass_4_output)
        pass_5_json = _parse_json_with_fallbacks(pass_5_output)

        pass_1_intervals = _intervals_from(pass_1_json)
        pass_2_intervals = _intervals_from(pass_2_json)
        pass_3_intervals = _intervals_from(pass_3_json)
        pass_4_intervals = _intervals_from(pass_4_json)
        pass_5_intervals = _intervals_from(pass_5_json)

        # Build interval lookup by index from DB (authoritative timeline)
        db_intervals = (
            db.query(VideoInterval)
            .filter(VideoInterval.video_id == project.video_id)
            .all()
        )
        interval_by_index = {i.interval_index: i for i in db_intervals}

        if not pass_5_intervals and isinstance(pass_5_json, dict):
            inferred_index: int | None = None
            ts_start = _parse_timestamp_seconds(pass_5_json.get("timestamp_reference"))
            if ts_start is not None:
                inferred_index = ts_start // 20
            if inferred_index is None or inferred_index not in interval_by_index:
                inferred_index = 0 if 0 in interval_by_index else None
            if inferred_index is not None:
                pass_5_item = dict(pass_5_json)
                pass_5_item["interval_index"] = inferred_index
                pass_5_intervals = [pass_5_item]

        def _normalize_yes_no(value: object) -> Optional[int]:
            if isinstance(value, bool):
                return 1 if value else 0
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in ("yes", "true", "1"):
                    return 1
                if lowered in ("no", "false", "0"):
                    return 0
            return None

        def _upsert_interval(
            interval_index: int,
            *,
            pass_1: dict | None = None,
            pass_2: dict | None = None,
            pass_3: dict | None = None,
            pass_4: dict | None = None,
            pass_5: dict | None = None,
        ) -> None:
            interval = interval_by_index.get(interval_index)
            if not interval:
                return

            if pass_1 is not None:
                s_record = (
                    db.query(PremiumStructuralInterval)
                    .filter(
                        PremiumStructuralInterval.project_id == project_id,
                        PremiumStructuralInterval.interval_id == interval.id,
                    )
                    .first()
                )
                if not s_record:
                    s_record = PremiumStructuralInterval(
                        project_id=project_id,
                        video_id=project.video_id,
                        interval_id=interval.id,
                        interval_index=interval.interval_index,
                        start_time_seconds=interval.start_time_seconds,
                        end_time_seconds=interval.end_time_seconds,
                    )
                    db.add(s_record)
                    db.flush()

                hook = pass_1.get("hook_strength", {})
                stim = pass_1.get("stimulation_density", {})
                esc = pass_1.get("escalation_signal", {})
                cog = pass_1.get("cognitive_load", {})
                drop = pass_1.get("drop_risk_probability", {})

                s_record.hook_strength_score = hook.get("score")
                s_record.hook_strength_justification = hook.get("justification_50_words")

                s_record.stimulation_cuts_per_20s = stim.get("cuts_per_20s")
                s_record.stimulation_camera_variation = stim.get("camera_variation")
                s_record.stimulation_motion_intensity = stim.get("motion_intensity")
                s_record.stimulation_justification = stim.get("justification_50_words")

                s_record.escalation_intensity_increase = _normalize_yes_no(
                    esc.get("intensity_increase")
                )
                s_record.escalation_stakes_raised = _normalize_yes_no(
                    esc.get("stakes_raised")
                )
                s_record.escalation_justification = esc.get("justification_50_words")

                s_record.cognitive_information_rate = cog.get("information_rate")
                s_record.cognitive_over_explanation_risk = _normalize_yes_no(
                    cog.get("over_explanation_risk")
                )
                s_record.cognitive_justification = cog.get("justification_50_words")

                s_record.drop_risk_score_percent = drop.get("score_percent")
                s_record.drop_risk_justification = drop.get("justification_50_words")

            if pass_2 is not None:
                p_record = (
                    db.query(PremiumPsychologicalInterval)
                    .filter(
                        PremiumPsychologicalInterval.project_id == project_id,
                        PremiumPsychologicalInterval.interval_id == interval.id,
                    )
                    .first()
                )
                if not p_record:
                    p_record = PremiumPsychologicalInterval(
                        project_id=project_id,
                        video_id=project.video_id,
                        interval_id=interval.id,
                        interval_index=interval.interval_index,
                        start_time_seconds=interval.start_time_seconds,
                        end_time_seconds=interval.end_time_seconds,
                    )
                    db.add(p_record)
                    db.flush()

                primary = pass_2.get("primary_trigger", {})
                trig = pass_2.get("trigger_intensity", {})
                arc = pass_2.get("emotional_arc_pattern", {})
                attention = pass_2.get("attention_sustainability_model", {})
                momentum = pass_2.get("viewer_momentum_score", {})

                p_record.primary_trigger_type = primary.get("type")
                p_record.primary_trigger_justification = primary.get("justification_50_words")

                p_record.trigger_intensity_score = trig.get("score")
                p_record.trigger_intensity_justification = trig.get("justification_50_words")

                p_record.emotional_arc_pattern_type = arc.get("type")
                p_record.emotional_arc_justification = arc.get("justification_50_words")

                p_record.attention_sustainability_type = attention.get("type")
                p_record.attention_sustainability_justification = attention.get("justification_50_words")

                p_record.viewer_momentum_score = momentum.get("score")
                p_record.viewer_momentum_justification = momentum.get("justification_50_words")

            if pass_3 is not None:
                perf_record = (
                    db.query(PremiumPerformanceInterval)
                    .filter(
                        PremiumPerformanceInterval.project_id == project_id,
                        PremiumPerformanceInterval.interval_id == interval.id,
                    )
                    .first()
                )
                if not perf_record:
                    perf_record = PremiumPerformanceInterval(
                        project_id=project_id,
                        video_id=project.video_id,
                        interval_id=interval.id,
                        interval_index=interval.interval_index,
                        start_time_seconds=interval.start_time_seconds,
                        end_time_seconds=interval.end_time_seconds,
                    )
                    db.add(perf_record)
                    db.flush()

                retention = pass_3.get("retention_strength", {})
                competitive = pass_3.get("competitive_density_rating", {})
                platform = pass_3.get("platform_distribution_readiness", {})
                conv = pass_3.get("conversion_leverage_score", {})
                total = pass_3.get("total_performance_index", {})
                weaknesses = pass_3.get("structural_weakness_priority", [])
                highest = pass_3.get("highest_leverage_optimization_target", {})

                perf_record.retention_strength_score = retention.get("score")
                perf_record.retention_strength_justification = retention.get("justification_50_words")

                perf_record.competitive_density_score = competitive.get("score")
                perf_record.competitive_density_justification = competitive.get("justification_50_words")

                tiktok = platform.get("tiktok", {}) if isinstance(platform, dict) else {}
                insta = platform.get("instagram_reels", {}) if isinstance(platform, dict) else {}
                yt = platform.get("youtube_shorts", {}) if isinstance(platform, dict) else {}

                perf_record.platform_tiktok_score = tiktok.get("score")
                perf_record.platform_tiktok_justification = tiktok.get("justification_50_words")
                perf_record.platform_instagram_reels_score = insta.get("score")
                perf_record.platform_instagram_reels_justification = insta.get("justification_50_words")
                perf_record.platform_youtube_shorts_score = yt.get("score")
                perf_record.platform_youtube_shorts_justification = yt.get("justification_50_words")

                perf_record.conversion_leverage_score = conv.get("score")
                perf_record.conversion_leverage_justification = conv.get("justification_50_words")

                perf_record.total_performance_index_score = total.get("score")
                perf_record.total_performance_index_justification = total.get("justification_50_words")

                if isinstance(weaknesses, list):
                    perf_record.structural_weakness_priority_json = json.dumps(weaknesses)
                perf_record.highest_leverage_target = highest.get("target")
                perf_record.highest_leverage_justification = highest.get("justification_50_words")

            if pass_4 is not None:
                transcript_record = (
                    db.query(PremiumTranscriptInterval)
                    .filter(
                        PremiumTranscriptInterval.project_id == project_id,
                        PremiumTranscriptInterval.interval_id == interval.id,
                    )
                    .first()
                )
                if not transcript_record:
                    transcript_record = PremiumTranscriptInterval(
                        project_id=project_id,
                        video_id=project.video_id,
                        interval_id=interval.id,
                        interval_index=interval.interval_index,
                        start_time_seconds=interval.start_time_seconds,
                        end_time_seconds=interval.end_time_seconds,
                    )
                    db.add(transcript_record)
                    db.flush()

                transcript_record.transcript_text = pass_4.get("transcript_text")

            if pass_5 is not None:
                verification_record = (
                    db.query(PremiumVerificationInterval)
                    .filter(
                        PremiumVerificationInterval.project_id == project_id,
                        PremiumVerificationInterval.interval_id == interval.id,
                    )
                    .first()
                )
                if not verification_record:
                    verification_record = PremiumVerificationInterval(
                        project_id=project_id,
                        video_id=project.video_id,
                        interval_id=interval.id,
                        interval_index=interval.interval_index,
                        start_time_seconds=interval.start_time_seconds,
                        end_time_seconds=interval.end_time_seconds,
                    )
                    db.add(verification_record)
                    db.flush()

                verification_record.question_type = pass_5.get("question_type")
                verification_record.timestamp_reference = pass_5.get("timestamp_reference")
                verification_record.visual_evidence_summary = pass_5.get("visual_evidence_summary")
                verification_record.verification_status = pass_5.get("verification_status")
                verification_record.answer = pass_5.get("answer")

            # Keep legacy JSON blobs for compatibility (optional)
            if (
                pass_1 is not None
                or pass_2 is not None
                or pass_3 is not None
                or pass_4 is not None
                or pass_5 is not None
            ):
                record = (
                    db.query(PremiumIntervalAnalysis)
                    .filter(
                        PremiumIntervalAnalysis.project_id == project_id,
                        PremiumIntervalAnalysis.interval_id == interval.id,
                    )
                    .first()
                )
                if not record:
                    record = PremiumIntervalAnalysis(
                        project_id=project_id,
                        video_id=project.video_id,
                        interval_id=interval.id,
                        interval_index=interval.interval_index,
                        start_time_seconds=interval.start_time_seconds,
                        end_time_seconds=interval.end_time_seconds,
                    )
                    db.add(record)
                    db.flush()
                if pass_1 is not None:
                    record.pass_1_json = json.dumps(pass_1)
                if pass_2 is not None:
                    record.pass_2_json = json.dumps(pass_2)
                if pass_3 is not None:
                    record.pass_3_json = json.dumps(pass_3)
                if pass_4 is not None:
                    record.pass_4_json = json.dumps(pass_4)
                if pass_5 is not None:
                    record.pass_5_json = json.dumps(pass_5)

        for item in pass_1_intervals:
            idx = int(item.get("interval_index", -1))
            if idx >= 0:
                _upsert_interval(idx, pass_1=item)

        for item in pass_2_intervals:
            idx = int(item.get("interval_index", -1))
            if idx >= 0:
                _upsert_interval(idx, pass_2=item)

        for item in pass_3_intervals:
            idx = int(item.get("interval_index", -1))
            if idx >= 0:
                _upsert_interval(idx, pass_3=item)

        for item in pass_4_intervals:
            idx = int(item.get("interval_index", -1))
            if idx >= 0:
                _upsert_interval(idx, pass_4=item)

        for item in pass_5_intervals:
            idx = int(item.get("interval_index", -1))
            if idx >= 0:
                _upsert_interval(idx, pass_5=item)

        db.flush()

        # Build and store embeddings for premium interval tables
        structural_rows = (
            db.query(PremiumStructuralInterval)
            .filter(PremiumStructuralInterval.project_id == project_id)
            .all()
        )
        psychological_rows = (
            db.query(PremiumPsychologicalInterval)
            .filter(PremiumPsychologicalInterval.project_id == project_id)
            .all()
        )
        performance_rows = (
            db.query(PremiumPerformanceInterval)
            .filter(PremiumPerformanceInterval.project_id == project_id)
            .all()
        )
        transcript_rows = (
            db.query(PremiumTranscriptInterval)
            .filter(PremiumTranscriptInterval.project_id == project_id)
            .all()
        )
        verification_rows = (
            db.query(PremiumVerificationInterval)
            .filter(PremiumVerificationInterval.project_id == project_id)
            .all()
        )

        structural_texts = [_build_structural_text(r) for r in structural_rows]
        psychological_texts = [_build_psychological_text(r) for r in psychological_rows]
        performance_texts = [_build_performance_text(r) for r in performance_rows]
        transcript_texts = [_build_transcript_text(r) for r in transcript_rows]
        verification_texts = [_build_verification_text(r) for r in verification_rows]

        structural_embeddings = await _embed_texts(structural_texts)
        psychological_embeddings = await _embed_texts(psychological_texts)
        performance_embeddings = await _embed_texts(performance_texts)
        transcript_embeddings = await _embed_texts(transcript_texts)
        verification_embeddings = await _embed_texts(verification_texts)

        def _model_payload(row: object) -> dict:
            payload: dict[str, object] = {}
            for col in row.__table__.columns:  # type: ignore[attr-defined]
                value = getattr(row, col.name)
                if isinstance(value, datetime):
                    payload[col.name] = value.isoformat()
                else:
                    payload[col.name] = value
            return payload

        def _upsert_unified_premium(
            *,
            row: object,
            analysis_type: str,
            source_pass: int,
            text: str,
            emb: list[float] | None,
        ) -> None:
            unified_interval = upsert_analysis_interval(
                db,
                project_id=project_id,
                video_id=project.video_id,
                granularity="interval",
                interval_index=getattr(row, "interval_index", -1) or -1,
                sub_index=-1,
                start_time_seconds=int(getattr(row, "start_time_seconds", 0) or 0),
                end_time_seconds=int(getattr(row, "end_time_seconds", 0) or 0),
            )
            unified_record = upsert_analysis_record(
                db,
                project_id=project_id,
                video_id=project.video_id,
                interval_id=unified_interval.id,
                analysis_type=analysis_type,
                source_pass=source_pass,
                status="completed",
                summary_text=text or None,
                payload=_model_payload(row),
            )
            upsert_analysis_embedding(
                db,
                analysis_record_id=unified_record.id,
                embedding=emb,
            )

        for row, text, emb in zip(structural_rows, structural_texts, structural_embeddings):
            embedding_record = (
                db.query(PremiumStructuralIntervalEmbedding)
                .filter(
                    PremiumStructuralIntervalEmbedding.structural_interval_id == row.id
                )
                .first()
            )
            if not embedding_record:
                embedding_record = PremiumStructuralIntervalEmbedding(
                    structural_interval_id=row.id,
                )
                db.add(embedding_record)
            embedding_record.combined_text = text or None
            embedding_record.embedding = _serialize_embedding(emb)
            _upsert_unified_premium(
                row=row,
                analysis_type="premium_structural",
                source_pass=1,
                text=text,
                emb=emb,
            )

        for row, text, emb in zip(psychological_rows, psychological_texts, psychological_embeddings):
            embedding_record = (
                db.query(PremiumPsychologicalIntervalEmbedding)
                .filter(
                    PremiumPsychologicalIntervalEmbedding.psychological_interval_id == row.id
                )
                .first()
            )
            if not embedding_record:
                embedding_record = PremiumPsychologicalIntervalEmbedding(
                    psychological_interval_id=row.id,
                )
                db.add(embedding_record)
            embedding_record.combined_text = text or None
            embedding_record.embedding = _serialize_embedding(emb)
            _upsert_unified_premium(
                row=row,
                analysis_type="premium_psychological",
                source_pass=2,
                text=text,
                emb=emb,
            )

        for row, text, emb in zip(performance_rows, performance_texts, performance_embeddings):
            embedding_record = (
                db.query(PremiumPerformanceIntervalEmbedding)
                .filter(
                    PremiumPerformanceIntervalEmbedding.performance_interval_id == row.id
                )
                .first()
            )
            if not embedding_record:
                embedding_record = PremiumPerformanceIntervalEmbedding(
                    performance_interval_id=row.id,
                )
                db.add(embedding_record)
            embedding_record.combined_text = text or None
            embedding_record.embedding = _serialize_embedding(emb)
            _upsert_unified_premium(
                row=row,
                analysis_type="premium_performance",
                source_pass=3,
                text=text,
                emb=emb,
            )

        for row, text, emb in zip(transcript_rows, transcript_texts, transcript_embeddings):
            embedding_record = (
                db.query(PremiumTranscriptIntervalEmbedding)
                .filter(
                    PremiumTranscriptIntervalEmbedding.transcript_interval_id == row.id
                )
                .first()
            )
            if not embedding_record:
                embedding_record = PremiumTranscriptIntervalEmbedding(
                    transcript_interval_id=row.id,
                )
                db.add(embedding_record)
            embedding_record.combined_text = text or None
            embedding_record.embedding = _serialize_embedding(emb)
            _upsert_unified_premium(
                row=row,
                analysis_type="premium_transcript",
                source_pass=4,
                text=text,
                emb=emb,
            )

        for row, text, emb in zip(verification_rows, verification_texts, verification_embeddings):
            embedding_record = (
                db.query(PremiumVerificationIntervalEmbedding)
                .filter(
                    PremiumVerificationIntervalEmbedding.verification_interval_id == row.id
                )
                .first()
            )
            if not embedding_record:
                embedding_record = PremiumVerificationIntervalEmbedding(
                    verification_interval_id=row.id,
                )
                db.add(embedding_record)
            embedding_record.combined_text = text or None
            embedding_record.embedding = _serialize_embedding(emb)
            _upsert_unified_premium(
                row=row,
                analysis_type="premium_verification",
                source_pass=5,
                text=text,
                emb=emb,
            )

        analysis.pass_1_output = pass_1_output
        analysis.pass_2_output = pass_2_output
        analysis.pass_3_output = pass_3_output
        analysis.pass_4_output = pass_4_output
        analysis.pass_5_output = pass_5_output
        analysis.status = "completed"
        analysis.generated_at = datetime.utcnow()
        analysis.error = None
        db.commit()

        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.premium_analysis_status = "completed"
            project.premium_analysis_completed_at = datetime.utcnow()
            project.premium_analysis_error = None
            db.commit()

        logger.info(
            "[PremiumAnalysis] Completed analysis for project %s.", project_id
        )

    except Exception as exc:
        logger.error(
            "[PremiumAnalysis] Analysis failed for project %s: %s",
            project_id,
            exc,
        )
        try:
            db.rollback()
        except Exception:
            pass
        try:
            analysis = (
                db.query(ProjectPremiumAnalysis)
                .filter(ProjectPremiumAnalysis.project_id == project_id)
                .first()
            )
            if analysis:
                analysis.status = "failed"
                analysis.error = str(exc)
                db.commit()

            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.premium_analysis_status = "failed"
                project.premium_analysis_error = str(exc)
                db.commit()
        except Exception as inner_exc:
            logger.error(
                "[PremiumAnalysis] Could not update failure status for project %s: %s",
                project_id,
                inner_exc,
            )
    finally:
        try:
            db.close()
        except Exception:
            pass
