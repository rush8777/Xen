from __future__ import annotations

from typing import Any

from ..constants import FeatureGenerationContext
from ..gemini_feature_client import GeminiFeatureClient
from ..parsing import clamp_int, clamp_time_range

PROMPT_VERSION = "clips-key-moments-v2"


def build_prompt(context: FeatureGenerationContext) -> str:
    overview_note = (context.overview_summary or "").strip()
    return f"""
You are extracting analytical key moments from a single video.

PROJECT CONTEXT
- Name: {context.project_name}
- URL: {context.video_url}
- Duration seconds: {context.duration_seconds}
- Overview summary: {overview_note or "N/A"}

OBJECTIVE
- Identify the most meaningful moments that matter to understanding the video.
- Prefer substance over virality.

ALLOWED CATEGORIES (strict enum)
- critical_insight
- emotional_peak
- decision_point
- problem_solution
- authority_statement
- call_to_action

ALLOWED IMPACT LEVELS (strict enum)
- high
- medium
- low

RULES
- Return 5 to 10 moments depending on video length and content density.
- Target duration per moment: 15 to 90 seconds.
- Use exact timestamp ranges from available content.
- Avoid overlaps where possible.
- Every moment must include a concrete justification, not generic filler.
- If no meaningful moments exist, return an empty array.

Return ONLY valid JSON (no markdown) in this exact shape:
{{
  "key_moments": [
    {{
      "id": "moment_1",
      "title": "string",
      "category": "critical_insight|emotional_peak|decision_point|problem_solution|authority_statement|call_to_action",
      "start_time_seconds": 0,
      "end_time_seconds": 20,
      "duration_seconds": 20,
      "justification": "2-3 sentence explanation of why this moment matters in context.",
      "impact_level": "high|medium|low",
      "context": "Brief lead-in context that sets this moment up.",
      "key_quote": "Exact quote if clear, otherwise concise paraphrase."
    }}
  ]
}}
""".strip()


async def generate_clips_payload(
    context: FeatureGenerationContext,
    client: GeminiFeatureClient,
) -> dict[str, Any]:
    raw = await client.generate_json(
        cached_content_name=context.cached_content_name,
        prompt=build_prompt(context),
        feature_id="clips",
    )
    key_moments = raw.get("key_moments")
    if not isinstance(key_moments, list):
        raise ValueError("Invalid key moments response shape")

    allowed_categories = {
        "critical_insight",
        "emotional_peak",
        "decision_point",
        "problem_solution",
        "authority_statement",
        "call_to_action",
    }
    allowed_impact = {"high", "medium", "low"}

    normalized: list[dict[str, Any]] = []
    clips_alias: list[dict[str, Any]] = []
    seen_ranges: list[tuple[int, int]] = []

    for idx, item in enumerate(key_moments):
        if not isinstance(item, dict):
            continue

        start, end = clamp_time_range(
            item.get("start_time_seconds"),
            item.get("end_time_seconds"),
            context.duration_seconds,
        )
        target_duration = clamp_int(item.get("duration_seconds"), 15, 90, max(15, min(90, end - start)))
        if context.duration_seconds > 0:
            end = min(context.duration_seconds, start + target_duration)
        else:
            end = start + target_duration

        if end <= start:
            end = start + 15
        duration_seconds = max(15, min(90, end - start))
        end = start + duration_seconds
        if context.duration_seconds > 0:
            end = min(context.duration_seconds, end)
            duration_seconds = max(1, end - start)

        if any(_overlap_ratio(start, end, a, b) >= 0.65 for a, b in seen_ranges):
            continue
        if (start, end) in seen_ranges:
            continue
        seen_ranges.append((start, end))

        moment_id = str(item.get("id") or f"moment_{idx + 1}").strip() or f"moment_{idx + 1}"
        title = str(item.get("title") or "").strip()[:120] or f"Key Moment {idx + 1}"

        category = str(item.get("category") or "").strip().lower()
        if category not in allowed_categories:
            category = "critical_insight"

        impact_level = str(item.get("impact_level") or "").strip().lower()
        if impact_level not in allowed_impact:
            impact_level = "medium"

        justification = str(item.get("justification") or "").strip()[:420]
        if not _is_meaningful_justification(justification):
            continue

        context_note = str(item.get("context") or "").strip()[:240]
        key_quote = str(item.get("key_quote") or "").strip()[:240]

        moment = {
            "id": moment_id,
            "title": title,
            "category": category,
            "start_time_seconds": start,
            "end_time_seconds": end,
            "duration_seconds": duration_seconds,
            "justification": justification,
            "impact_level": impact_level,
            "context": context_note or "Context not provided.",
            "key_quote": key_quote or "No key quote captured.",
        }
        normalized.append(moment)

        # Backward-compatible alias while UI migrates from legacy clip cards.
        clips_alias.append(
            {
                "id": moment_id,
                "title": title,
                "start_time_seconds": start,
                "end_time_seconds": end,
                "duration_seconds": duration_seconds,
                "viral_score": 0,
                "platform_fit": {"shorts": 0, "reels": 0, "tiktok": 0},
                "suggested_caption": justification,
                "moment_type": category,
                "standalone_viability": impact_level.capitalize(),
                "justification": justification,
                "impact_level": impact_level,
            }
        )

    normalized.sort(key=lambda x: (x["start_time_seconds"], x["end_time_seconds"]))
    clips_alias.sort(key=lambda x: (x["start_time_seconds"], x["end_time_seconds"]))
    return {
        "key_moments": normalized,
        "clips": clips_alias,
        "raw_model_output": raw,
    }


def _is_meaningful_justification(text: str) -> bool:
    value = text.strip().lower()
    if len(value) < 24:
        return False
    generic = {
        "important moment",
        "key moment",
        "this is important",
        "high impact moment",
        "significant moment",
    }
    return value not in generic


def _overlap_ratio(start_a: int, end_a: int, start_b: int, end_b: int) -> float:
    overlap = max(0, min(end_a, end_b) - max(start_a, start_b))
    if overlap <= 0:
        return 0.0
    len_a = max(1, end_a - start_a)
    len_b = max(1, end_b - start_b)
    return overlap / float(min(len_a, len_b))
