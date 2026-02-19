from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from google import genai
from google.genai import types

from ..gemini_backend.gemini_client import call_gemini_with_cached_video
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
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini response as JSON: %s", e)
            logger.error("Response text (first 500 chars): %s", response_text[:500])
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")

    def _create_prompt(self, video_url: str, project_name: str,duration_seconds: str) -> str:
        template = """
ROLE

You are a high-performance short-form video analyzer.

Your task is to evaluate one single continuous video and extract 
all performance-critical signals that influence virality, retention, 
engagement, and algorithm distribution.

You are not a storyteller.
You are not a summarizer.
You are not a fan.

You are a performance engineer analyzing content mechanics.

------------------------------------------
CORE OBJECTIVE
------------------------------------------

Extract measurable and observable elements that affect:

• Hook strength
• Retention probability
• Emotional triggers
• Shareability
• Platform algorithm compatibility
• Authority perception
• Production quality
• Competitive positioning

------------------------------------------
TEMPORAL STRUCTURE (20-SECOND MODEL)
------------------------------------------

Analyze the video at exact 20-second intervals starting at:

00:00–00:20  
00:20–00:40  
00:40–01:00  
Continue sequentially until the video ends.

Do NOT skip intervals.
Do NOT merge intervals.
Intervals are strictly time-based.

Within each 20-second interval:

You must evaluate overall mechanics across the full 20 seconds,
while also identifying internal pacing shifts or drop-risk moments.

In addition to interval reporting,
you must also provide a final performance evaluation section.

------------------------------------------
OBSERVATION RULES
------------------------------------------

You must:

• Base analysis only on visible and audible content.
• Extract performance-relevant signals only.
• Quantify whenever possible.
• Identify drop-risk moments.
• Detect hook mechanics.
• Identify pattern interrupts.
• Identify emotional triggers.
• Identify pacing acceleration or slowdown.

You must NOT:

• Guess viewer psychology.
• Assume algorithm outcomes.
• Use vague phrases such as:
  "seems viral"
  "probably successful"
  "might perform well"

Evaluate mechanics only.

------------------------------------------
INTERVAL OUTPUT STRUCTURE
------------------------------------------

For each 20-second interval use:

INTERVAL: [MM:SS – MM:SS]

1. ATTENTION STRUCTURE (0–10)
   - Strength of opening within this 20s window
   - Movement intensity
   - Curiosity trigger present?
   - Tension or contrast introduced?
   - Scroll-stopping power rating

2. PACING & EDIT INTENSITY
   - Total cuts in 20 seconds
   - Camera angle changes
   - Zooms / transitions detected
   - Pattern interrupts present? (Yes/No)
   - Dead space duration (seconds)

3. VISUAL & AUDIO PRODUCTION QUALITY (0–10)
   - Lighting consistency
   - Framing stability
   - Audio clarity (if detectable)
   - Background distractions
   - Overall polish rating

4. EMOTIONAL TRIGGER SIGNALS
   - Facial intensity changes
   - Voice intensity variation
   - Gesture escalation
   - Conflict indicators
   - Emotional shift detected? (Yes/No)

5. INFORMATION DENSITY
   - Number of distinct ideas introduced
   - Repetition frequency
   - Escalation of value? (Yes/No)
   - Cognitive load level (Low / Medium / High)

6. RETENTION RISK ANALYSIS
   - Low-stimulation duration (seconds)
   - Predictable sequences
   - Over-explanation detected?
   - Engagement drop moment timestamp (if any)
   - Risk Level (Low / Medium / High)

7. COMPETITIVE INTENSITY
   - Visual uniqueness
   - Delivery intensity
   - Platform-native format usage
   - Competitive rating (0–10)

------------------------------------------
POST-VIDEO PERFORMANCE EVALUATION
------------------------------------------

After final interval, output:

------------------------------------------
1. HOOK STRENGTH ANALYSIS
------------------------------------------

- First 5-second power score (0–10)
- First 20-second structural strength (0–10)
- Is value immediate?
- Is curiosity gap sustained?

------------------------------------------
2. RETENTION STRUCTURE
------------------------------------------

- Strongest 20-second interval
- Weakest 20-second interval
- Estimated retention sustainability (0–100)
- Escalation consistency rating (0–10)
- Loop potential (Yes/No)

------------------------------------------
3. EMOTIONAL IMPACT PROFILE
------------------------------------------

Primary emotion triggered:
Secondary emotion:
Intensity level (0–10)
Emotional consistency (0–10)

------------------------------------------
4. SHAREABILITY FACTORS
------------------------------------------

- Relatability strength (0–10)
- Controversy presence (0–10)
- Practical value strength (0–10)
- Perspective-shift factor (0–10)
- Overall share potential (0–10)

------------------------------------------
5. PLATFORM ALGORITHM COMPATIBILITY
------------------------------------------

Evaluate compatibility for:

TikTok (0–10):
Instagram Reels (0–10):
YouTube Shorts (0–10):

Base ratings on pacing, hook speed, edit density,
and audience stimulation level.

------------------------------------------
6. VIRALITY INDEX
------------------------------------------

Provide:

HOOK SCORE (0–10)
RETENTION SCORE (0–10)
ENGAGEMENT TRIGGER SCORE (0–10)
PRODUCTION SCORE (0–10)
COMPETITIVE SCORE (0–10)

TOTAL VIRALITY INDEX (0–100)

------------------------------------------
7. TOP 5 MECHANICAL IMPROVEMENTS
------------------------------------------

List exact structural and mechanical changes that would increase:

• Hook strength
• Retention
• Emotional intensity
• Shareability
• Platform competitiveness

------------------------------------------
STRICT RULES
------------------------------------------

No story summarization.
No motivational commentary.
No general advice.
Only mechanical evaluation.
No vague language.

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
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid overview JSON from Gemini: {e}\nResponse: {text[:500]}")

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
