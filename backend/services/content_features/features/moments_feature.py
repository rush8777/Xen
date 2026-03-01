from __future__ import annotations

from typing import Any

from ..constants import FeatureGenerationContext
from ..gemini_feature_client import GeminiFeatureClient
from ..parsing import clamp_int, clamp_time_range

PROMPT_VERSION = "moments-v1"
ALLOWED_CATEGORIES = {"emotional", "informative", "hook", "question", "surprise"}


def build_prompt(context: FeatureGenerationContext) -> str:
    overview_note = (context.overview_summary or "").strip()
    return f"""
You are generating key moments from a cached video.

PROJECT:
- Name: {context.project_name}
- URL: {context.video_url}
- Duration seconds: {context.duration_seconds}
- Optional overview summary: {overview_note or "N/A"}

Return ONLY valid JSON (no markdown) with this exact shape:
{{
  "moments": [
    {{
      "id": "moment_1",
      "label": "string",
      "category": "emotional|informative|hook|question|surprise",
      "start_time_seconds": 0,
      "end_time_seconds": 20,
      "importance_score": 0,
      "rationale": "string"
    }}
  ]
}}

Rules:
- Generate 3 to 8 moments.
- Keep timestamps in [0, {context.duration_seconds}] with start < end.
- Categories must be one of the allowed enum values.
- Importance score must be an integer between 0 and 100.
- Labels should be concise and specific.
""".strip()


async def generate_moments_payload(
    context: FeatureGenerationContext,
    client: GeminiFeatureClient,
) -> dict[str, Any]:
    raw = await client.generate_json(
        cached_content_name=context.cached_content_name,
        prompt=build_prompt(context),
        feature_id="moments",
    )
    moments = raw.get("moments")
    if not isinstance(moments, list):
        raise ValueError("Invalid moments response shape")

    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(moments, start=1):
        if not isinstance(item, dict):
            continue
        start, end = clamp_time_range(
            item.get("start_time_seconds"),
            item.get("end_time_seconds"),
            context.duration_seconds,
        )
        category = str(item.get("category") or "").strip().lower()
        if category not in ALLOWED_CATEGORIES:
            category = "informative"
        normalized.append(
            {
                "id": str(item.get("id") or f"moment_{idx}"),
                "label": str(item.get("label") or f"Moment {idx}").strip(),
                "category": category,
                "start_time_seconds": start,
                "end_time_seconds": end,
                "importance_score": clamp_int(item.get("importance_score"), 0, 100, 70),
                "rationale": str(
                    item.get("rationale") or "High-value moment identified from pacing and message impact."
                ).strip(),
            }
        )

    normalized.sort(key=lambda x: (x["start_time_seconds"], x["end_time_seconds"]))
    if not normalized:
        raise ValueError("No valid moments returned by model")
    return {"moments": normalized}
