from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from google import genai
from google.genai import types

from ..gemini_backend.gemini_client import call_gemini_with_cached_video
from .content_features.parsing import parse_json_object
logger = logging.getLogger(__name__)


class ProjectOverviewGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    def _read_analysis_content(self, analysis_file_path: str) -> str:
        analysis_path = Path(analysis_file_path)
        if not analysis_path.exists():
            raise FileNotFoundError(f"Analysis file not found: {analysis_file_path}")

        analysis_content = analysis_path.read_text(encoding="utf-8")
        if len(analysis_content) > 50000:
            logger.warning("Analysis content truncated for Gemini processing")
            analysis_content = analysis_content[:50000] + "\n\n[Content truncated...]"
        return analysis_content

    def _generate_content(self, prompt: str) -> str:
        # #region agent log
        try:
            import json as _agent_json, time as _agent_time  # type: ignore
            with open(
                r"d:\web_dev\v0-social\.cursor\debug.log",
                "a",
                encoding="utf-8",
            ) as _agent_f:
                _agent_f.write(
                    _agent_json.dumps(
                        {
                            "id": f"overview_pre_{int(_agent_time.time() * 1000)}",
                            "timestamp": int(_agent_time.time() * 1000),
                            "runId": "initial",
                            "hypothesisId": "H1-H4",
                            "location": "backend/services/project_overview_generator.py:_generate_content",
                            "message": "Calling Gemini generate_content",
                            "data": {
                                "model": self.model,
                                "prompt_length": len(prompt) if isinstance(prompt, str) else None,
                            },
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass
        # #endregion agent log

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    response_mime_type="application/json",
                ),
            )
        except Exception as e:
            # #region agent log
            try:
                import json as _agent_json, time as _agent_time  # type: ignore
                with open(
                    r"d:\web_dev\v0-social\.cursor\debug.log",
                    "a",
                    encoding="utf-8",
                ) as _agent_f:
                    _agent_f.write(
                        _agent_json.dumps(
                            {
                                "id": f"overview_err_{int(_agent_time.time() * 1000)}",
                                "timestamp": int(_agent_time.time() * 1000),
                                "runId": "initial",
                                "hypothesisId": "H1-H4",
                                "location": "backend/services/project_overview_generator.py:_generate_content",
                                "message": "Gemini generate_content failed",
                                "data": {
                                    "model": self.model,
                                    "error_type": type(e).__name__,
                                    "error_str": str(e),
                                },
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion agent log
            raise

        response_text = (response.text or "").strip()
        if not response_text:
            raise ValueError("Empty response from Gemini")
        return response_text

    def _sanitize_response_text(self, response_text: str) -> str:
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(
                lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            ).strip()
        return response_text

    def _parse_json(self, response_text: str) -> dict[str, Any]:
        try:
            return parse_json_object(response_text)
        except Exception as e:
            logger.error("Failed to parse Gemini response as JSON: %s", e)
            logger.error("Response text (first 500 chars): %s", response_text[:500])
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")

    def _create_prompt(self, video_url: str, project_name: str,duration_seconds: str) -> str:
        template = f"""
ROLE

You are a high-performance short-form video analyst.

Task: Analyze a single continuous video and extract only measurable, observable elements 
that affect virality, retention, engagement, and platform compatibility.

You are not a storyteller, summarizer, or fan. Evaluate content mechanics only.

------------------------------------------
CORE OBJECTIVE
------------------------------------------

Extract performance-relevant signals for:

• Hook strength
• Retention patterns
• Emotional triggers
• Shareability
• Platform algorithm fit
• Authority perception
• Production quality
• Competitive positioning

------------------------------------------
OBSERVATION RULES
------------------------------------------

• Base analysis only on visible and audible content.
• Identify hook mechanics, pattern interrupts, pacing shifts, and drop-risk moments.
• Quantify only when directly observable.
• Do NOT assume viewer psychology, algorithm outcomes, or use vague language.

------------------------------------------
OUTPUT STRUCTURE
------------------------------------------

1. ATTENTION & HOOK
   - Opening impact
   - Curiosity triggers
   - Scroll-stopping moments

2. PACING & EDITING
   - Cuts and transitions
   - Camera movement
   - Dead space duration
   - Pattern interrupts

3. VISUAL & AUDIO QUALITY
   - Lighting, framing, audio clarity
   - Background distractions
   - Overall polish

4. EMOTIONAL TRIGGERS
   - Facial, voice, gesture intensity
   - Emotional shifts

5. INFORMATION DENSITY
   - Number of distinct ideas
   - Repetition frequency
   - Cognitive load

6. RETENTION RISK
   - Low-stimulation moments
   - Predictable sequences
   - Engagement drop points

7. COMPETITIVE INTENSITY
   - Visual uniqueness
   - Delivery style
   - Platform-native format usage

------------------------------------------
POST-VIDEO EVALUATION
------------------------------------------

• Hook effectiveness
• Retention structure
• Emotional impact
• Shareability factors
• Platform compatibility
• Key mechanical improvements for hook, retention, emotion, shareability, and platform fit

End output after improvement section.
"""
        return f"""You are a content writer and analyst. Use the following video analysis data to generate a concise Video Overview.

VIDEO INFO:
- URL: {video_url}
- Project: {project_name}


use the following template to genrate the markdown blog:
{template}

Return ONLY valid JSON matching this EXACT schema (no markdown code fences, no explanations):

{{
  \"version\": 1,
  \"blog\": {{
    \"title\": \"string\",
    \"markdown\": \"string\"
  }},
  \"summary\": \"string\",
  \"insights\": {{
    \"situation\": \"string\",
    \"pain\": [\"string\"],
    \"impact\": [\"string\"],
    \"critical_event\": \"string\",
    \"decision\": \"string\"
  }}
}}

RULES:
- Return ONLY valid JSON
- blog.markdown must be Markdown (no HTML)
- Keep blog.markdown reasonably sized (roughly 400–900 words)
- Make insights specific and actionable, but grounded in the provided analysis/comments
"""


    async def _generate_overview_from_cached_video(
        self,
        *,
        cached_content_name: str,
        duration_seconds: float,
        video_url: str,
        project_name: str,
    ) -> Dict[str, Any]:
        """
        Generate blog + summary + insights directly from cached video in a single call.

        Output schema matches the current overview JSON contract:
          {
            "version": 1,
            "blog": {"title": "...", "markdown": "..."},
            "summary": "...",
            "insights": {
              "situation": "...",
              "pain": ["..."],
              "impact": ["..."],
              "critical_event": "...",
              "decision": "..."
            }
          }
        """
        prompt = self._create_prompt(
            video_url=video_url,
            project_name=project_name,
            duration_seconds=duration_seconds,
        )

        text = await call_gemini_with_cached_video(
            cached_content_name=cached_content_name,
            prompt=prompt,
        )

        try:
            data = parse_json_object(text)
        except Exception as first_error:
            retry_prompt = (
                f"{prompt}\n\n"
                "IMPORTANT: Your previous response was not valid JSON. "
                "Return strictly valid JSON matching the schema. "
                "No markdown, no extra text."
            )
            retry_text = await call_gemini_with_cached_video(
                cached_content_name=cached_content_name,
                prompt=retry_prompt,
            )
            try:
                data = parse_json_object(retry_text)
            except Exception as retry_error:
                raise ValueError(
                    "Invalid overview JSON from Gemini after retry. "
                    f"first_error={first_error}; retry_error={retry_error}\n"
                    f"Response: {retry_text[:500]}"
                )

        if not isinstance(data, dict):
            raise ValueError("Overview JSON must be an object")

        return data

    async def generate_overview(
        self,
        *,
        analysis_file_path: str,
        video_url: str,
        project_name: str,
        project_id: int,
        job_id: str | None = None,
        cached_content_name: str | None = None,
        video_duration_seconds: float | None = None,
    ) -> dict[str, Any]:
        logger.info("Generating overview for project %s", project_id)

        # Prefer cost-optimized path using cached video content when available
        if cached_content_name:
            overview = await self._generate_overview_from_cached_video(
                cached_content_name=cached_content_name,
                duration_seconds=float(video_duration_seconds or 0),
                video_url=video_url,
                project_name=project_name,
            )
        else:
            # Legacy path: read large analysis file and create a text-based prompt
            analysis_content = self._read_analysis_content(analysis_file_path)
            prompt = self._create_prompt(video_url, project_name, str(video_duration_seconds or 0))
            response_text = self._generate_content(prompt)
            response_text = self._sanitize_response_text(response_text)
            overview = self._parse_json(response_text)

        overview["project_id"] = project_id
        overview["generated_at"] = datetime.utcnow().isoformat()
        overview["source"] = {
            "analysis_file_path": str(analysis_file_path),
            "video_url": video_url,
            "job_id": job_id,
            "cached_content_name": cached_content_name,
            "video_duration_seconds": video_duration_seconds,
        }
        return overview

    def validate_overview(self, overview: dict[str, Any]) -> bool:
        if "blog" not in overview or not isinstance(overview["blog"], dict):
            return False
        if "markdown" not in overview["blog"]:
            return False
        if "summary" not in overview:
            return False
        if "insights" not in overview or not isinstance(overview["insights"], dict):
            return False
        return True
