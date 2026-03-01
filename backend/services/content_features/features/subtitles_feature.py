from __future__ import annotations

from typing import Any

from ..constants import FeatureGenerationContext
from ..gemini_feature_client import GeminiFeatureClient
from ..parsing import break_subtitle_lines, clamp_time_range, to_int

PROMPT_VERSION = "subtitles-v1"


def build_prompt(context: FeatureGenerationContext) -> str:
    return f"""
You are generating subtitle segments from a cached video.

PROJECT:
- Name: {context.project_name}
- Duration seconds: {context.duration_seconds}

Return ONLY valid JSON (no markdown) with this exact shape:
{{
  "language": "en",
  "style": {{
    "font": "DM Sans",
    "size": 28,
    "position": "bottom",
    "color": "#ffffff",
    "background": "rgba(0,0,0,0.55)"
  }},
  "segments": [
    {{
      "start_time_seconds": 0,
      "end_time_seconds": 3,
      "text": "string",
      "lines": ["string", "string"]
    }}
  ]
}}

Rules:
- Timestamps must be monotonic and within [0, {context.duration_seconds}].
- Use clear subtitle chunks suitable for readability.
- Maximum 2 lines per segment, roughly <= 42 chars per line.
- Do not return empty segments.
""".strip()


async def generate_subtitles_payload(
    context: FeatureGenerationContext,
    client: GeminiFeatureClient,
) -> dict[str, Any]:
    raw = await client.generate_json(
        cached_content_name=context.cached_content_name,
        prompt=build_prompt(context),
        feature_id="subtitles",
    )
    segments = raw.get("segments")
    if not isinstance(segments, list):
        raise ValueError("Invalid subtitles response shape")

    style = raw.get("style")
    if not isinstance(style, dict):
        style = {}

    out_segments: list[dict[str, Any]] = []
    last_end = 0

    for item in segments:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue

        start, end = clamp_time_range(
            item.get("start_time_seconds"),
            item.get("end_time_seconds"),
            context.duration_seconds,
        )
        start = max(start, last_end)
        end = max(start + 1, end)
        last_end = end

        lines_raw = item.get("lines")
        if isinstance(lines_raw, list):
            lines = [str(line).strip() for line in lines_raw if str(line).strip()]
        else:
            lines = []
        if not lines:
            lines = break_subtitle_lines(text, max_chars=42)

        normalized_lines: list[str] = []
        for line in lines[:2]:
            normalized_lines.extend(break_subtitle_lines(line, max_chars=42))
            if len(normalized_lines) >= 2:
                break

        out_segments.append(
            {
                "start_time_seconds": start,
                "end_time_seconds": end,
                "text": text,
                "lines": normalized_lines[:2] or break_subtitle_lines(text, max_chars=42),
            }
        )

    if not out_segments:
        raise ValueError("No valid subtitle segments returned by model")

    return {
        "language": str(raw.get("language") or "en"),
        "style": {
            "font": str(style.get("font") or "DM Sans"),
            "size": to_int(style.get("size"), default=28),
            "position": str(style.get("position") or "bottom"),
            "color": str(style.get("color") or "#ffffff"),
            "background": str(style.get("background") or "rgba(0,0,0,0.55)"),
        },
        "segments": out_segments,
    }
