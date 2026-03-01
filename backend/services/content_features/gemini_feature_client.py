from __future__ import annotations

import asyncio
import logging
from typing import Any

from ...gemini_backend.gemini_client import call_gemini_with_cached_video
from .constants import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_RESPONSE_MIME_TYPE,
    MAX_GEMINI_RETRIES,
    MAX_PARALLEL_LLM_CALLS,
)
from .parsing import parse_json_object

logger = logging.getLogger(__name__)


class GeminiFeatureClient:
    _semaphore = asyncio.Semaphore(MAX_PARALLEL_LLM_CALLS)

    def __init__(
        self,
        *,
        model: str = DEFAULT_GEMINI_MODEL,
        response_mime_type: str = DEFAULT_RESPONSE_MIME_TYPE,
        max_retries: int = MAX_GEMINI_RETRIES,
    ) -> None:
        self.model = model
        self.response_mime_type = response_mime_type
        self.max_retries = max(1, int(max_retries))

    async def generate_json(
        self,
        *,
        cached_content_name: str,
        prompt: str,
        feature_id: str,
    ) -> dict[str, Any]:
        if not cached_content_name:
            raise ValueError("Missing cached content name.")

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with self._semaphore:
                    text = await call_gemini_with_cached_video(
                        cached_content_name=cached_content_name,
                        prompt=prompt,
                        model=self.model,
                        response_mime_type=self.response_mime_type,
                    )
                return parse_json_object(text)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "[ContentFeatures] Gemini %s call failed (attempt %d/%d): %s",
                    feature_id,
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(2**attempt)

        raise RuntimeError(
            f"Gemini {feature_id} generation failed after {self.max_retries} attempts: {last_error}"
        )
