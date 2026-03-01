from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..gemini_backend.statistics_generator import statistics_generator as optimized_statistics_generator
from ..gemini_backend.gemini_client import (
    generate_statistics_from_cached_video,
)

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
        cached_content_name: str | None = None,
        video_duration_seconds: float | None = None,
    ) -> dict[str, Any]:
        logger.info("Generating statistics for project %s", project_id)

        async def _run() -> dict[str, Any]:
            # Prefer cost-optimized path using cached video content when available
            if cached_content_name and video_duration_seconds and video_duration_seconds > 0:
                raw = await generate_statistics_from_cached_video(
                    cached_content_name=cached_content_name,
                    duration_seconds=video_duration_seconds,
                    video_url=video_url,
                    project_name=project_name,
                )
            else:
                # Legacy path: read full analysis text file and use the optimized statistics generator
                analysis_content = self._read_analysis_content(analysis_file_path)
                raw = await optimized_statistics_generator.generate_all_statistics(
                    project_id=str(project_id),
                    analysis_content=analysis_content,
                    video_url=video_url,
                    project_name=project_name,
                    duration_seconds=video_duration_seconds,
                    use_cache=True,
                )

            raw = self._normalize_timeline_components(
                raw=raw,
                duration_seconds=video_duration_seconds,
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
                "engagement_trend_curve": raw.get("engagement_trend_curve", []),
                "_meta": component_meta,
            }

            stats_data["project_id"] = project_id
            stats_data["generated_at"] = datetime.utcnow().isoformat()
            stats_data["source"] = {
                "analysis_file_path": str(analysis_file_path),
                "video_url": video_url,
                "job_id": job_id,
                "cached_content_name": cached_content_name,
                "video_duration_seconds": video_duration_seconds,
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
            "engagement_trend_curve",
        ]
        return all(key in stats for key in required_keys)

    def _get_cadence_seconds(self, duration_seconds: float | None) -> int:
        if duration_seconds and duration_seconds > 0 and duration_seconds <= 600:
            return 2
        return 3

    def _parse_time_to_seconds(self, value: Any) -> int:
        raw = str(value or "").strip()
        parts = raw.split(":")
        if len(parts) not in (2, 3):
            return -1
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            return -1
        if any(n < 0 for n in nums):
            return -1
        if len(nums) == 3:
            return nums[0] * 3600 + nums[1] * 60 + nums[2]
        return nums[0] * 60 + nums[1]

    def _format_seconds_to_time(self, seconds: int) -> str:
        s = max(0, int(seconds))
        hh = s // 3600
        mm = (s % 3600) // 60
        ss = s % 60
        if hh > 0:
            return f"{hh}:{mm:02d}:{ss:02d}"
        return f"{mm:02d}:{ss:02d}"

    def _interpolate_numeric(
        self,
        points: list[tuple[int, dict[str, Any]]],
        target_second: int,
        key: str,
        default_value: float,
    ) -> float:
        left: tuple[int, dict[str, Any]] | None = None
        right: tuple[int, dict[str, Any]] | None = None
        for second, payload in points:
            value = payload.get(key)
            if not isinstance(value, (int, float)):
                continue
            if second <= target_second:
                left = (second, payload)
            if second >= target_second:
                right = (second, payload)
                break

        if left and right:
            ls, lp = left
            rs, rp = right
            lv = float(lp.get(key, default_value))
            rv = float(rp.get(key, default_value))
            if rs == ls:
                return lv
            ratio = (target_second - ls) / (rs - ls)
            return lv + (rv - lv) * ratio
        if left:
            return float(left[1].get(key, default_value))
        if right:
            return float(right[1].get(key, default_value))
        return default_value

    def _nearest_label_value(
        self,
        points: list[tuple[int, dict[str, Any]]],
        target_second: int,
        key: str,
        default_value: str,
    ) -> str:
        best_value = default_value
        best_distance = float("inf")
        for second, payload in points:
            value = payload.get(key)
            if not isinstance(value, str) or not value:
                continue
            distance = abs(second - target_second)
            if distance < best_distance:
                best_distance = distance
                best_value = value
        return best_value

    def _normalize_timeline_component(
        self,
        payload: Any,
        *,
        duration_seconds: float | None,
        numeric_fields: list[str],
        clamps: dict[str, tuple[int, int]],
        label_fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        if not isinstance(payload, list):
            return []

        cleaned: list[tuple[int, dict[str, Any]]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            second = self._parse_time_to_seconds(item.get("time"))
            if second < 0:
                continue
            cleaned.append((second, item))

        if not cleaned:
            return []

        cleaned.sort(key=lambda pair: pair[0])
        cadence = self._get_cadence_seconds(duration_seconds)
        start_second = 0
        if duration_seconds and duration_seconds > 0:
            end_second = int(max(start_second, round(duration_seconds)))
        else:
            end_second = cleaned[-1][0]
        if end_second < start_second:
            end_second = start_second

        targets = list(range(start_second, end_second + 1, cadence))
        if targets[-1] != end_second:
            targets.append(end_second)

        label_fields = label_fields or []
        dense: list[dict[str, Any]] = []
        for target in targets:
            row: dict[str, Any] = {"time": self._format_seconds_to_time(target)}
            for field in numeric_fields:
                fallback = 0.0
                if field == "pace":
                    fallback = 120.0
                value = self._interpolate_numeric(cleaned, target, field, fallback)
                lo, hi = clamps.get(field, (0, 100))
                row[field] = int(max(lo, min(hi, round(value))))
            for field in label_fields:
                row[field] = self._nearest_label_value(cleaned, target, field, "neutral")
            dense.append(row)
        return dense

    def _normalize_timeline_components(
        self,
        *,
        raw: dict[str, Any],
        duration_seconds: float | None,
    ) -> dict[str, Any]:
        normalized = dict(raw or {})
        normalized["sentiment_pulse"] = self._normalize_timeline_component(
            normalized.get("sentiment_pulse", []),
            duration_seconds=duration_seconds,
            numeric_fields=["positive", "negative"],
            clamps={"positive": (0, 100), "negative": (0, 100)},
        )
        normalized["emotional_intensity_timeline"] = self._normalize_timeline_component(
            normalized.get("emotional_intensity_timeline", []),
            duration_seconds=duration_seconds,
            numeric_fields=["intensity"],
            clamps={"intensity": (0, 100)},
            label_fields=["emotion"],
        )
        normalized["engagement_trend_curve"] = self._normalize_timeline_component(
            normalized.get("engagement_trend_curve", []),
            duration_seconds=duration_seconds,
            numeric_fields=["engagement", "speech_energy", "pace", "key_moment_boost"],
            clamps={
                "engagement": (0, 100),
                "speech_energy": (0, 100),
                "pace": (60, 220),
                "key_moment_boost": (0, 100),
            },
        )
        return normalized
