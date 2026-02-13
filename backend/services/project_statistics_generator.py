from __future__ import annotations

import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from ..gemini_backend import config as gemini_config
from ..gemini_backend.statistics_cache_manager import statistics_cache_manager

logger = logging.getLogger(__name__)


class ProjectStatisticsGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        self.schema_version = 1
        self.prompt_version = "v1"

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
                            "id": f"stats_pre_{int(_agent_time.time() * 1000)}",
                            "timestamp": int(_agent_time.time() * 1000),
                            "runId": "initial",
                            "hypothesisId": "H1-H4",
                            "location": "backend/services/project_statistics_generator.py:_generate_content",
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
                    temperature=0.1,
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
                                "id": f"stats_err_{int(_agent_time.time() * 1000)}",
                                "timestamp": int(_agent_time.time() * 1000),
                                "runId": "initial",
                                "hypothesisId": "H1-H4",
                                "location": "backend/services/project_statistics_generator.py:_generate_content",
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

    def _parse_stats_json(self, response_text: str) -> Any:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini response as JSON: %s", e)
            logger.error("Response text (first 500 chars): %s", response_text[:500])
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")

    def _read_json_file(self, path: Path) -> dict[str, Any] | list[Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _get_outputs_dir(self, project_id: int) -> Path:
        base = gemini_config.OUTPUT_DIR / str(project_id) / "statistics"
        base.mkdir(parents=True, exist_ok=True)
        return base

    def _timestamp_slug(self) -> str:
        return datetime.utcnow().replace(microsecond=0).isoformat().replace(":", "-") + "Z"

    def _get_component_output_path(self, outputs_dir: Path, component_name: str) -> Path:
        ts = self._timestamp_slug()
        safe_component = component_name.replace("/", "_")
        return outputs_dir / f"{safe_component}.v{self.schema_version}.{ts}.json"

    def _load_cached_component(
        self,
        *,
        analysis_content: str,
        video_url: str,
        project_name: str,
        component_name: str,
    ) -> dict[str, Any] | list[Any] | None:
        cache_key = statistics_cache_manager.calculate_component_hash(
            analysis_content=analysis_content,
            video_url=video_url,
            project_name=project_name,
            component_name=component_name,
            schema_version=self.schema_version,
            prompt_version=self.prompt_version,
        )
        entry = statistics_cache_manager.get_cached_component(cache_key)
        if not entry:
            return None

        output_path = Path(entry["output_path"])
        try:
            return self._read_json_file(output_path)
        except Exception:
            return None

    def _save_component_output_and_cache(
        self,
        *,
        outputs_dir: Path,
        analysis_content: str,
        video_url: str,
        project_name: str,
        component_name: str,
        payload: dict[str, Any] | list[Any],
    ) -> Path:
        output_path = self._get_component_output_path(outputs_dir, component_name)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        cache_key = statistics_cache_manager.calculate_component_hash(
            analysis_content=analysis_content,
            video_url=video_url,
            project_name=project_name,
            component_name=component_name,
            schema_version=self.schema_version,
            prompt_version=self.prompt_version,
        )
        statistics_cache_manager.save_cached_component(
            cache_key,
            component_name=component_name,
            output_path=output_path,
            schema_version=self.schema_version,
            prompt_version=self.prompt_version,
        )

        return output_path

    def _enrich_stats(
        self,
        stats_data: dict[str, Any],
        *,
        analysis_file_path: str,
        video_url: str,
        project_id: int,
        job_id: str | None,
    ) -> dict[str, Any]:
        stats_data["project_id"] = project_id
        stats_data["generated_at"] = datetime.utcnow().isoformat()
        stats_data["source"] = {
            "analysis_file_path": str(analysis_file_path),
            "video_url": video_url,
            "job_id": job_id,
        }
        return stats_data

    def _create_prompt_video_metrics_grid(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are an advanced forensic data extraction engine.
You are NOT an analyst.
You are NOT allowed to estimate.
You are NOT allowed to infer.
You are NOT allowed to fabricate missing values.
You are NOT allowed to smooth, interpolate, or approximate.

You must ONLY extract values that can be DIRECTLY computed from explicit
numerical evidence inside ANALYSIS DATA.

If ANY required metric cannot be calculated with strict mathematical
certainty from the provided data, return an EMPTY JSON object: {{}}

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

ANALYSIS DATA:
{analysis_content}

REQUIRED OUTPUT SCHEMA (RETURN ONLY VALID JSON, NO MARKDOWN):
{{
  "net_sentiment_score": <integer 0-100>,
  "net_sentiment_delta_vs_last": <integer -100 to 100>,
  "engagement_velocity_comments_per_hour": <integer>,
  "toxicity_alert_bots_detected": <integer>,
  "question_density_percent": <integer 0-100>
}}

STRICT EXTRACTION RULES:
1. All numbers MUST be integers.
2. You may compute values ONLY if all required inputs are explicitly present.
3. If historical comparison data is missing, you MUST return {{}}.
4. If comment timestamps are missing, you MUST return {{}}.
5. If toxicity classification data is missing, you MUST return {{}}.
6. If question detection data is missing, you MUST return {{}}.
7. DO NOT guess platform averages.
8. DO NOT assume prior performance.
9. DO NOT fill with 0 unless 0 is explicitly supported.
10. Output ONLY JSON.
"""

    def _create_prompt_sentiment_pulse(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are a strict time-series sentiment extractor.
You must extract ONLY explicitly time-stamped sentiment signals.

You are forbidden from:
- Creating synthetic time points
- Evenly distributing sentiment
- Interpolating between segments
- Guessing sentiment trends

If time-segmented sentiment data is not explicitly present,
return an EMPTY ARRAY: []

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

ANALYSIS DATA:
{analysis_content}

REQUIRED OUTPUT SCHEMA (RETURN ONLY JSON):
[
  {{ "time": "MM:SS", "positive": <integer 0-100>, "negative": <integer 0-100> }}
]

STRICT RULES:
1. Use ONLY explicitly time-labeled sentiment values.
2. Each object must correspond to real time evidence.
3. Percentages must be directly supported by counts.
4. All numbers must be integers.
5. If insufficient data exists -> return [].
6. No commentary. No explanation. JSON only.
"""

    def _create_prompt_emotion_radar(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are a categorical emotion distribution extractor.

You must ONLY compute emotion distribution if:
- Explicit emotion labels exist
- Or explicit categorized counts exist

If categorical emotional counts are not explicitly available,
return an EMPTY ARRAY: []

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

ANALYSIS DATA:
{analysis_content}

REQUIRED OUTPUT (JSON ONLY):
[
  {{ "subject": "Hype", "value": <integer 0-100> }},
  {{ "subject": "Confusion", "value": <integer 0-100> }},
  {{ "subject": "Excitement", "value": <integer 0-100> }},
  {{ "subject": "Criticism", "value": <integer 0-100> }},
  {{ "subject": "Support", "value": <integer 0-100> }}
]

STRICT RULES:
1. Do NOT invent emotional categories.
2. Do NOT assign default weights.
3. Do NOT normalize unless raw counts are provided.
4. If total counts are unknown -> return [].
5. All values must be integers.
6. Output ONLY JSON.
"""

    def _create_prompt_emotional_intensity_timeline(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are a strict emotional intensity time extractor.

You must extract ONLY explicitly time-stamped emotional intensity signals.

If no time-indexed emotional intensity data exists,
return an EMPTY ARRAY: []

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

ANALYSIS DATA:
{analysis_content}

REQUIRED OUTPUT (JSON ONLY):
[
  {{ "time": "MM:SS", "intensity": <integer 0-100>, "emotion": "neutral|excited|confused|critical" }}
]

STRICT RULES:
1. Time must match explicit timestamps.
2. Intensity must be derived from measurable signals.
3. No smoothing.
4. No interpolation.
5. No invented emotion states.
6. If insufficient data -> return [].
7. JSON only.
"""

    def _create_prompt_audience_age_distribution(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are a demographic extractor.

You must ONLY extract explicitly stated age distribution statistics.

You are forbidden from:
- Inferring age from language
- Inferring from emojis
- Inferring from platform norms
- Using global averages

If no age statistics exist in ANALYSIS DATA,
return an EMPTY ARRAY: []

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

ANALYSIS DATA:
{analysis_content}

REQUIRED OUTPUT (JSON ONLY):
[
  {{ "label": "13–17", "value": <integer 0-100> }},
  {{ "label": "18–24", "value": <integer 0-100> }},
  {{ "label": "25–34", "value": <integer 0-100> }},
  {{ "label": "35–44", "value": <integer 0-100> }},
  {{ "label": "45+", "value": <integer 0-100> }}
]

STRICT RULES:
1. Use ONLY explicit numeric demographic reports.
2. Values must match provided statistics exactly.
3. Do NOT force sum to 100 unless source does.
4. If partial distribution only -> return [].
5. JSON only.
"""

    def _create_prompt_audience_gender_distribution(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are a demographic extractor.

Extract gender distribution ONLY if explicitly provided.

You are strictly forbidden from:
- Inferring gender from names
- Inferring from avatars
- Inferring from writing style

If no structured gender statistics exist,
return an EMPTY ARRAY: []

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

ANALYSIS DATA:
{analysis_content}

REQUIRED OUTPUT (JSON ONLY):
[
  {{ "label": "Male", "value": <integer 0-100> }},
  {{ "label": "Female", "value": <integer 0-100> }},
  {{ "label": "Other / Unknown", "value": <integer 0-100> }}
]

STRICT RULES:
1. Values must directly match explicit statistics.
2. No assumptions.
3. If incomplete distribution -> return [].
4. JSON only.
"""

    def _create_prompt_audience_top_locations(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are a geographic statistics extractor.

Extract audience location distribution ONLY if explicitly provided.

You must NOT:
- Infer location from language
- Infer from timezone
- Infer from usernames

If no structured location statistics exist,
return an EMPTY ARRAY: []

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

ANALYSIS DATA:
{analysis_content}

REQUIRED OUTPUT (JSON ONLY):
[
  {{ "label": "Country/Region", "value": <integer 0-100> }}
]

STRICT RULES:
1. Use only explicit geographic statistics.
2. No ranking unless source provides ranking.
3. No estimation.
4. If insufficient data -> return [].
5. JSON only.
"""

    def _create_prompt_audience_interests(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are an interest extraction engine.

Extract audience interests ONLY if supported by measurable clustering
or explicit categorization inside ANALYSIS DATA.

You must NOT:
- Generalize from video topic
- Infer from hashtags
- Assume platform-level audience behavior

If no structured interest signals exist,
return an EMPTY ARRAY: []

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

ANALYSIS DATA:
{analysis_content}

REQUIRED OUTPUT (JSON ONLY):
[
  "Interest1",
  "Interest2"
]

STRICT RULES:
1. Only include interests supported by data.
2. No invented categories.
3. If insufficient evidence -> return [].
4. JSON only.
"""

    def _create_prompt_top_comments(self, analysis_content: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are a comment extraction engine.

You must ONLY extract comments explicitly present in ANALYSIS DATA.

You must NOT:
- Fabricate comments
- Generate synthetic IDs
- Create fake like counts
- Rewrite comment text

If no real comments are present,
return an EMPTY ARRAY: []

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

ANALYSIS DATA:
{analysis_content}

REQUIRED OUTPUT (JSON ONLY):
[
  {{
    "id": "string",
    "author": "string",
    "avatar": "2 letters",
    "content": "exact original comment text",
    "likes": <integer>,
    "intent": "positive|criticism|question"
  }}
]

STRICT RULES:
1. Comment text must match EXACTLY.
2. Likes must match explicit values.
3. Intent must be directly classifiable from text.
4. If any required field is missing -> exclude that comment.
5. If no complete comments exist -> return [].
6. JSON only.
"""

    def _build_prompt(self, component_name: str, analysis_content: str, video_url: str, project_name: str) -> str:
        if component_name == "video_metrics_grid":
            return self._create_prompt_video_metrics_grid(analysis_content, video_url, project_name)
        if component_name == "sentiment_pulse":
            return self._create_prompt_sentiment_pulse(analysis_content, video_url, project_name)
        if component_name == "emotion_radar":
            return self._create_prompt_emotion_radar(analysis_content, video_url, project_name)
        if component_name == "emotional_intensity_timeline":
            return self._create_prompt_emotional_intensity_timeline(analysis_content, video_url, project_name)
        if component_name == "audience_demographics.age_distribution":
            return self._create_prompt_audience_age_distribution(analysis_content, video_url, project_name)
        if component_name == "audience_demographics.gender_distribution":
            return self._create_prompt_audience_gender_distribution(analysis_content, video_url, project_name)
        if component_name == "audience_demographics.top_locations":
            return self._create_prompt_audience_top_locations(analysis_content, video_url, project_name)
        if component_name == "audience_demographics.audience_interests":
            return self._create_prompt_audience_interests(analysis_content, video_url, project_name)
        if component_name == "top_comments":
            return self._create_prompt_top_comments(analysis_content, video_url, project_name)

        raise ValueError(f"Unknown statistics component: {component_name}")

    def _default_component_payload(self, component_name: str) -> dict[str, Any] | list[Any]:
        if component_name == "video_metrics_grid":
            return {
                "net_sentiment_score": 0,
                "net_sentiment_delta_vs_last": 0,
                "engagement_velocity_comments_per_hour": 0,
                "toxicity_alert_bots_detected": 0,
                "question_density_percent": 0,
            }
        return []

    def _generate_component(
        self,
        *,
        outputs_dir: Path,
        analysis_content: str,
        video_url: str,
        project_name: str,
        component_name: str,
    ) -> tuple[str, dict[str, Any] | list[Any], dict[str, Any]]:
        meta: dict[str, Any] = {
            "status": "pending",
            "error": None,
            "cache_hit": False,
            "output_path": None,
        }

        cached = self._load_cached_component(
            analysis_content=analysis_content,
            video_url=video_url,
            project_name=project_name,
            component_name=component_name,
        )
        if cached is not None:
            meta["status"] = "completed"
            meta["cache_hit"] = True
            return component_name, cached, meta

        try:
            prompt = self._build_prompt(component_name, analysis_content, video_url, project_name)
            response_text = self._generate_content(prompt)
            response_text = self._sanitize_response_text(response_text)
            payload = self._parse_stats_json(response_text)

            output_path = self._save_component_output_and_cache(
                outputs_dir=outputs_dir,
                analysis_content=analysis_content,
                video_url=video_url,
                project_name=project_name,
                component_name=component_name,
                payload=payload,
            )
            meta["status"] = "completed"
            meta["output_path"] = str(output_path)
            return component_name, payload, meta
        except Exception as e:
            meta["status"] = "failed"
            meta["error"] = str(e)
            return component_name, self._default_component_payload(component_name), meta

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
        outputs_dir = self._get_outputs_dir(project_id)

        components = [
            "video_metrics_grid",
            "sentiment_pulse",
            "emotion_radar",
            "emotional_intensity_timeline",
            "audience_demographics.age_distribution",
            "audience_demographics.gender_distribution",
            "audience_demographics.top_locations",
            "audience_demographics.audience_interests",
            "top_comments",
        ]

        component_meta: dict[str, Any] = {
            "schema_version": self.schema_version,
            "prompt_version": self.prompt_version,
            "components": {},
        }

        results: dict[str, Any] = {}

        max_workers = min(8, max(1, len(components)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._generate_component,
                    outputs_dir=outputs_dir,
                    analysis_content=analysis_content,
                    video_url=video_url,
                    project_name=project_name,
                    component_name=name,
                ): name
                for name in components
            }

            for future in as_completed(futures):
                component_name = futures[future]
                try:
                    name, payload, meta = future.result()
                except Exception as e:
                    name = component_name
                    payload = self._default_component_payload(component_name)
                    meta = {"status": "failed", "error": str(e), "cache_hit": False, "output_path": None}

                results[name] = payload
                component_meta["components"][name] = meta

        stats_data: dict[str, Any] = {
            "version": self.schema_version,
            "video_metrics_grid": results.get("video_metrics_grid", self._default_component_payload("video_metrics_grid")),
            "sentiment_pulse": results.get("sentiment_pulse", []),
            "emotion_radar": results.get("emotion_radar", []),
            "emotional_intensity_timeline": results.get("emotional_intensity_timeline", []),
            "audience_demographics": {
                "age_distribution": results.get("audience_demographics.age_distribution", []),
                "gender_distribution": results.get("audience_demographics.gender_distribution", []),
                "top_locations": results.get("audience_demographics.top_locations", []),
                "audience_interests": results.get("audience_demographics.audience_interests", []),
            },
            "top_comments": results.get("top_comments", []),
            "_meta": component_meta,
        }

        return self._enrich_stats(
            stats_data,
            analysis_file_path=analysis_file_path,
            video_url=video_url,
            project_id=project_id,
            job_id=job_id,
        )

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
