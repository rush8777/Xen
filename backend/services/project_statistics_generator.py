from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..gemini_backend.statistics_generator import statistics_generator as optimized_statistics_generator

logger = logging.getLogger(__name__)


class ProjectStatisticsGenerator:
    def __init__(self, api_key: str):
        self.schema_version = int(getattr(optimized_statistics_generator, "SCHEMA_VERSION", 1))
        self.prompt_version = str(getattr(optimized_statistics_generator, "PROMPT_VERSION", "v2.0-optimized"))

    def _read_analysis_content(self, analysis_file_path: str) -> str:
        analysis_path = Path(analysis_file_path)
        if not analysis_path.exists():
            raise FileNotFoundError(f"Analysis file not found: {analysis_file_path}")

        analysis_content = analysis_path.read_text(encoding="utf-8")
        return analysis_content

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

        analysis_content = self._read_analysis_content(analysis_file_path)

        async def _run() -> dict[str, Any]:
            raw = await optimized_statistics_generator.generate_all_statistics(
                project_id=str(project_id),
                analysis_content=analysis_content,
                video_url=video_url,
                project_name=project_name,
                use_cache=True,
            )

            component_meta: dict[str, Any] = {
                "schema_version": self.schema_version,
                "prompt_version": self.prompt_version,
                "components": {},
            }

            stats_data: dict[str, Any] = {
                "version": self.schema_version,
                "video_metrics_grid": raw.get(
                    "video_metrics_grid",
                    {
                        "net_sentiment_score": 50,
                        "net_sentiment_delta_vs_last": 0,
                        "engagement_velocity_comments_per_hour": 10,
                        "toxicity_alert_bots_detected": 0,
                        "question_density_percent": 0,
                    },
                ),
                "sentiment_pulse": raw.get("sentiment_pulse", []),
                "emotion_radar": raw.get("emotion_radar", []),
                "emotional_intensity_timeline": raw.get("emotional_intensity_timeline", []),
                "audience_demographics": {
                    "age_distribution": raw.get("audience_demographics.age_distribution", []),
                    "gender_distribution": raw.get("audience_demographics.gender_distribution", []),
                    "top_locations": raw.get("audience_demographics.top_locations", []),
                    "audience_interests": raw.get("audience_demographics.audience_interests", []),
                },
                "top_comments": raw.get("top_comments", []),
                "_meta": component_meta,
            }

            stats_data["project_id"] = project_id
            stats_data["generated_at"] = datetime.utcnow().isoformat()
            stats_data["source"] = {
                "analysis_file_path": str(analysis_file_path),
                "video_url": video_url,
                "job_id": job_id,
            }

            return stats_data

        coro = _run()
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()

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
