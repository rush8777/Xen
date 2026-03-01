from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FeatureId = Literal["clips", "subtitles", "chapters", "moments"]

FEATURE_IDS: tuple[FeatureId, ...] = ("clips", "subtitles", "chapters", "moments")
MIN_LONGFORM_SECONDS = 181

DEFAULT_GEMINI_MODEL = "models/gemini-2.5-flash"
DEFAULT_RESPONSE_MIME_TYPE = "application/json"
MAX_GEMINI_RETRIES = 3
MAX_PARALLEL_LLM_CALLS = 2


@dataclass(frozen=True)
class FeatureGenerationContext:
    project_id: int
    project_name: str
    video_url: str
    duration_seconds: int
    cached_content_name: str
    overview_summary: str | None = None
