from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class ProjectStatisticsGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    def _create_prompt(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""You are a video analytics expert. Analyze the following video analysis data and generate structured statistics in JSON format.

VIDEO INFO:
- URL: {video_url}
- Project: {project_name}

ANALYSIS DATA:
{analysis_content}

Generate ONLY valid JSON matching this EXACT schema (no markdown, no explanations):

{{
  \"version\": 1,
  \"video_metrics_grid\": {{
    \"net_sentiment_score\": <integer 0-100>,
    \"net_sentiment_delta_vs_last\": <integer -100 to 100>,
    \"engagement_velocity_comments_per_hour\": <integer>,
    \"toxicity_alert_bots_detected\": <integer>,
    \"question_density_percent\": <integer 0-100>
  }},
  \"sentiment_pulse\": [
    {{ \"time\": \"0:00\", \"positive\": <integer 0-100>, \"negative\": <integer 0-100> }},
    {{ \"time\": \"5:00\", \"positive\": <integer 0-100>, \"negative\": <integer 0-100> }}
  ],
  \"emotion_radar\": [
    {{ \"subject\": \"Hype\", \"value\": <integer 0-100> }},
    {{ \"subject\": \"Confusion\", \"value\": <integer 0-100> }},
    {{ \"subject\": \"Excitement\", \"value\": <integer 0-100> }},
    {{ \"subject\": \"Criticism\", \"value\": <integer 0-100> }},
    {{ \"subject\": \"Support\", \"value\": <integer 0-100> }}
  ],
  \"emotional_intensity_timeline\": [
    {{ \"time\": \"00:00\", \"intensity\": <integer 0-100>, \"emotion\": \"neutral|excited|confused|critical\" }}
  ],
  \"audience_demographics\": {{
    \"age_distribution\": [
      {{ \"label\": \"18–24\", \"value\": <integer 0-100> }},
      {{ \"label\": \"25–34\", \"value\": <integer 0-100> }},
      {{ \"label\": \"35–44\", \"value\": <integer 0-100> }},
      {{ \"label\": \"45+\", \"value\": <integer 0-100> }}
    ],
    \"gender_distribution\": [
      {{ \"label\": \"Male\", \"value\": <integer 0-100> }},
      {{ \"label\": \"Female\", \"value\": <integer 0-100> }},
      {{ \"label\": \"Other\", \"value\": <integer 0-100> }}
    ],
    \"top_locations\": [
      {{ \"label\": \"Country/Region\", \"value\": <integer 0-100> }}
    ],
    \"audience_interests\": [\"Interest1\", \"Interest2\", \"Interest3\"]
  }},
  \"top_comments\": [
    {{
      \"id\": \"1\",
      \"author\": \"string or 'Unknown'\",
      \"avatar\": \"2 letters\",
      \"content\": \"comment text\",
      \"likes\": <integer>,
      \"intent\": \"positive|criticism|question\"
    }}
  ]
}}

RULES:
- Return ONLY valid JSON, no markdown code blocks
- All numeric values must be integers
- Make realistic estimations based on the analysis data
- If comments are available, use actual comment data
- If data is missing, provide reasonable estimates
- sentiment_pulse should have 5-10 time points across the video
- emotional_intensity_timeline should match video duration
"""

    def generate_statistics(
        self,
        *,
        analysis_file_path: str,
        video_url: str,
        project_name: str,
        project_id: int,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        logger.info("Generating statistics for project %s", project_id)

        analysis_path = Path(analysis_file_path)
        if not analysis_path.exists():
            raise FileNotFoundError(f"Analysis file not found: {analysis_file_path}")

        analysis_content = analysis_path.read_text(encoding="utf-8")
        if len(analysis_content) > 50000:
            logger.warning("Analysis content truncated for Gemini processing")
            analysis_content = analysis_content[:50000] + "\n\n[Content truncated...]"

        prompt = self._create_prompt(analysis_content, video_url, project_name)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        response_text = (response.text or "").strip()
        if not response_text:
            raise ValueError("Empty response from Gemini")

        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

        try:
            stats_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini response as JSON: %s", e)
            logger.error("Response text (first 500 chars): %s", response_text[:500])
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")

        stats_data["project_id"] = project_id
        stats_data["generated_at"] = datetime.utcnow().isoformat()
        stats_data["source"] = {
            "analysis_file_path": str(analysis_file_path),
            "video_url": video_url,
            "job_id": job_id,
        }

        return stats_data

    def validate_statistics(self, stats: dict[str, Any]) -> bool:
        required_keys = [
            "version",
            "video_metrics_grid",
            "sentiment_pulse",
            "emotion_radar",
            "emotional_intensity_timeline",
            "audience_demographics",
            "top_comments",
        ]
        return all(key in stats for key in required_keys)
