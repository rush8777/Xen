from __future__ import annotations

from typing import Any

from ..constants import FeatureGenerationContext
from ..gemini_feature_client import GeminiFeatureClient
from ..parsing import clamp_time_range

PROMPT_VERSION = "chapters-v2-structural"

ALLOWED_CHAPTER_TYPES = {
    "Hook",
    "Context Build",
    "Education",
    "Demonstration",
    "Escalation",
    "Social Proof",
    "CTA",
    "Resolution",
}

CHAPTER_TYPE_ALIASES = {
    "hook": "Hook",
    "context": "Context Build",
    "context build": "Context Build",
    "education": "Education",
    "demonstration": "Demonstration",
    "escalation": "Escalation",
    "social proof": "Social Proof",
    "cta": "CTA",
    "call to action": "CTA",
    "resolution": "Resolution",
}

ALLOWED_PSYCHOLOGICAL_INTENTS = {
    "build_tension",
    "deliver_proof",
    "educate",
    "escalate",
    "cta",
    "resolve",
    "other",
}


def build_prompt(context: FeatureGenerationContext) -> str:
    overview_note = (context.overview_summary or "").strip()
    return f"""
Using the cached Gemini video transcript and scene context, analyze the full video structure.

PROJECT:
- Name: {context.project_name}
- URL: {context.video_url}
- Duration seconds: {context.duration_seconds}
- Optional overview summary: {overview_note or "N/A"}

Return ONLY valid JSON (no markdown) with this exact shape:
{{
  "totalChapters": 4,
  "chapters": [
    {{
      "id": "chapter_1",
      "title": "string",
      "start_time_seconds": 0,
      "end_time_seconds": 60,
      "duration_seconds": 60,
      "summary": "40-70 word analytical summary",
      "psychological_intent": "build_tension | deliver_proof | educate | escalate | cta | resolve | other",
      "chapter_type": "Hook | Context Build | Education | Demonstration | Escalation | Social Proof | CTA | Resolution",
      "subchapters": [
        {{
          "id": "chapter_1_sub_1",
          "title": "string",
          "start_time_seconds": 0,
          "end_time_seconds": 25,
          "duration_seconds": 25,
          "summary": "20-40 word analytical summary"
        }}
      ]
    }}
  ]
}}

Rules:
- Extract chapters from real structural transitions (topic, intent, or narrative shift), not equal time slicing.
- Produce 3 to 8 coherent chapters.
- Every chapter must have start < end and stay within [0, {context.duration_seconds}].
- Chapter titles should be concise and analytical.
- Each chapter summary should be 40 to 70 words.
- Each chapter must include 2 to 4 subchapters.
- Each subchapter summary should be 20 to 40 words.
- Do not hallucinate events not present in the transcript or scene context.
""".strip()


def _coerce_int(value: Any, fallback: int) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return int(fallback)


def _word_count(text: str) -> int:
    return len([part for part in text.strip().split() if part])


def _normalize_psychological_intent(value: Any) -> str:
    raw = str(value or "").strip().lower().replace(" ", "_")
    return raw if raw in ALLOWED_PSYCHOLOGICAL_INTENTS else "other"


def _normalize_chapter_type(value: Any) -> str:
    raw = str(value or "").strip()
    if raw in ALLOWED_CHAPTER_TYPES:
        return raw
    mapped = CHAPTER_TYPE_ALIASES.get(raw.lower())
    return mapped or "Education"


def _normalize_summary(value: Any, fallback: str, min_words: int) -> str:
    summary = str(value or "").strip()
    if _word_count(summary) < min_words:
        return fallback
    return summary


def _normalize_subchapter_range(
    item: dict[str, Any],
    *,
    chapter_start: int,
    chapter_end: int,
    video_duration_seconds: int,
) -> tuple[int, int]:
    chapter_duration = max(1, chapter_end - chapter_start)
    raw_start = _coerce_int(item.get("start_time_seconds"), chapter_start)
    raw_end = _coerce_int(item.get("end_time_seconds"), chapter_start + 1)

    is_relative = (
        chapter_start > 0
        and 0 <= raw_start < raw_end <= chapter_duration + 1
        and not (chapter_start <= raw_start < raw_end <= chapter_end)
    )

    if is_relative:
        rel_start, rel_end = clamp_time_range(raw_start, raw_end, chapter_duration)
        start = chapter_start + rel_start
        end = chapter_start + rel_end
    else:
        start, end = clamp_time_range(raw_start, raw_end, video_duration_seconds)

    start = max(chapter_start, min(chapter_end - 1, start))
    end = min(chapter_end, max(start + 1, end))
    if end <= start:
        end = min(chapter_end, start + 1)
        if end <= start:
            start = max(chapter_start, chapter_end - 1)
            end = chapter_end
    return start, end


def _synthesize_subchapters(
    *,
    chapter_idx: int,
    chapter_start: int,
    chapter_end: int,
) -> list[dict[str, Any]]:
    span = max(2, chapter_end - chapter_start)
    split = chapter_start + max(1, span // 2)
    split = min(chapter_end - 1, max(chapter_start + 1, split))

    first_end = split
    second_start = split
    second_end = chapter_end

    return [
        {
            "id": f"chapter_{chapter_idx}_sub_1",
            "title": "Subchapter 1",
            "start_time_seconds": chapter_start,
            "end_time_seconds": first_end,
            "duration_seconds": max(1, first_end - chapter_start),
            "summary": "This segment establishes the chapter context, framing the key transition and preparing the viewer for the core narrative movement that follows.",
        },
        {
            "id": f"chapter_{chapter_idx}_sub_2",
            "title": "Subchapter 2",
            "start_time_seconds": second_start,
            "end_time_seconds": second_end,
            "duration_seconds": max(1, second_end - second_start),
            "summary": "This segment advances the chapter objective, consolidating evidence or explanation and moving the narrative toward a clear structural takeaway for the viewer.",
        },
    ]


async def generate_chapters_payload(
    context: FeatureGenerationContext,
    client: GeminiFeatureClient,
) -> dict[str, Any]:
    raw = await client.generate_json(
        cached_content_name=context.cached_content_name,
        prompt=build_prompt(context),
        feature_id="chapters",
    )
    chapters = raw.get("chapters")
    if not isinstance(chapters, list):
        raise ValueError("Invalid chapters response shape")

    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(chapters, start=1):
        if not isinstance(item, dict):
            continue
        start, end = clamp_time_range(
            item.get("start_time_seconds"),
            item.get("end_time_seconds"),
            context.duration_seconds,
        )
        title = str(item.get("title") or f"Chapter {idx}").strip()
        summary_fallback = (
            "This chapter develops a meaningful narrative transition, organizing the core ideas and evidence into a clear structural step within the video flow."
        )
        summary = _normalize_summary(item.get("summary"), summary_fallback, min_words=8)

        raw_subchapters = item.get("subchapters")
        subchapters: list[dict[str, Any]] = []
        if isinstance(raw_subchapters, list):
            for sub_idx, raw_subchapter in enumerate(raw_subchapters, start=1):
                if not isinstance(raw_subchapter, dict):
                    continue
                sub_start, sub_end = _normalize_subchapter_range(
                    raw_subchapter,
                    chapter_start=start,
                    chapter_end=end,
                    video_duration_seconds=context.duration_seconds,
                )
                sub_summary_fallback = (
                    "This subchapter marks a focused progression point within the broader chapter, clarifying the local shift in content and intent."
                )
                sub_summary = _normalize_summary(
                    raw_subchapter.get("summary"),
                    sub_summary_fallback,
                    min_words=5,
                )
                subchapters.append(
                    {
                        "id": str(raw_subchapter.get("id") or f"chapter_{idx}_sub_{sub_idx}"),
                        "title": str(raw_subchapter.get("title") or f"Subchapter {sub_idx}").strip(),
                        "start_time_seconds": sub_start,
                        "end_time_seconds": sub_end,
                        "duration_seconds": max(1, sub_end - sub_start),
                        "summary": sub_summary,
                    }
                )

        subchapters.sort(key=lambda x: (x["start_time_seconds"], x["end_time_seconds"]))
        if len(subchapters) > 4:
            subchapters = subchapters[:4]
        if len(subchapters) < 2:
            subchapters = _synthesize_subchapters(
                chapter_idx=idx,
                chapter_start=start,
                chapter_end=end,
            )

        normalized.append(
            {
                "id": str(item.get("id") or f"chapter_{idx}"),
                "title": title,
                "start_time_seconds": start,
                "end_time_seconds": end,
                "duration_seconds": max(1, end - start),
                "summary": summary,
                "psychological_intent": _normalize_psychological_intent(item.get("psychological_intent")),
                "chapter_type": _normalize_chapter_type(item.get("chapter_type")),
                "subchapters": subchapters,
            }
        )

    normalized.sort(key=lambda x: (x["start_time_seconds"], x["end_time_seconds"]))
    if not normalized:
        raise ValueError("No valid chapters returned by model")
    total_chapters = _coerce_int(raw.get("totalChapters"), len(normalized))
    if total_chapters <= 0:
        total_chapters = len(normalized)
    return {
        "totalChapters": total_chapters,
        "chapters": normalized,
    }
