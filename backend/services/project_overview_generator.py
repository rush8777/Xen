from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

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
                    temperature=0.2,
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
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini response as JSON: %s", e)
            logger.error("Response text (first 500 chars): %s", response_text[:500])
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")

    def _create_prompt(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""You are a content writer and analyst. Use the following video analysis data to generate a concise Video Overview.

VIDEO INFO:
- URL: {video_url}
- Project: {project_name}

ANALYSIS DATA:
{analysis_content}

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

    def generate_overview(
        self,
        *,
        analysis_file_path: str,
        video_url: str,
        project_name: str,
        project_id: int,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        logger.info("Generating overview for project %s", project_id)

        analysis_content = self._read_analysis_content(analysis_file_path)
        prompt = self._create_prompt(analysis_content, video_url, project_name)
        response_text = self._generate_content(prompt)
        response_text = self._sanitize_response_text(response_text)
        overview = self._parse_json(response_text)

        overview["project_id"] = project_id
        overview["generated_at"] = datetime.utcnow().isoformat()
        overview["source"] = {
            "analysis_file_path": str(analysis_file_path),
            "video_url": video_url,
            "job_id": job_id,
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
