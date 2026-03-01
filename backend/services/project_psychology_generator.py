from __future__ import annotations

import asyncio
import concurrent.futures
import json
import re
from typing import Any

from ..gemini_backend.gemini_client import call_gemini_with_cached_video
from .psychology_prompts import build_psychology_extraction_prompt


class ProjectPsychologyGenerator:
    def __init__(self):
        self.schema_version = 1

    def generate_psychology(
        self,
        *,
        cached_content_name: str,
        project_name: str,
        video_url: str,
        video_duration_seconds: int | None,
        transcript_passage: str,
        interval_seconds: int = 5,
    ) -> dict[str, Any]:
        safe_interval_seconds = 2 if interval_seconds == 2 else 5
        prompt = (
            f"PROJECT: {project_name}\n"
            f"VIDEO_URL: {video_url}\n"
            f"VIDEO_DURATION_SECONDS: {int(video_duration_seconds or 0)}\n\n"
            f"TRANSCRIPT_CONTEXT:\n{transcript_passage[:12000]}\n\n"
            f"{build_psychology_extraction_prompt(safe_interval_seconds)}"
        )

        async def _run() -> dict[str, Any]:
            raw = await call_gemini_with_cached_video(
                cached_content_name=cached_content_name,
                prompt=prompt,
                response_mime_type="application/json",
            )
            parsed = self._parse_json_with_fallbacks(raw)
            normalized = self._normalize_payload(
                parsed,
                duration_seconds=video_duration_seconds or 0,
                interval_seconds=safe_interval_seconds,
            )
            normalized["source"] = {
                "video_url": video_url,
                "project_name": project_name,
                "video_duration_seconds": int(video_duration_seconds or 0),
                "transcript_chars_used": len(transcript_passage[:12000]),
                "generation_note": "Generated using Gemini video context and structured psychological extraction.",
            }
            return normalized

        coro = _run()
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()

    def _parse_json_with_fallbacks(self, text: str) -> dict[str, Any]:
        candidate = (text or "").strip()
        if candidate.startswith("```"):
            lines = candidate.split("\n")
            inner = lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
            candidate = "\n".join(inner).strip()

        candidates = [candidate]
        first_open = candidate.find("{")
        last_close = candidate.rfind("}")
        if first_open != -1 and last_close > first_open:
            candidates.append(candidate[first_open:last_close + 1])

        for raw in candidates:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                fixed = re.sub(r",(\s*[}\]])", r"\1", raw)
                try:
                    parsed = json.loads(fixed)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    continue

        raise ValueError("Unable to parse psychology model output as JSON object")

    def _clamp_int(self, value: Any, lo: int = 0, hi: int = 100) -> int:
        try:
            n = int(round(float(value)))
        except Exception:
            return lo
        return max(lo, min(hi, n))

    def _norm_time(self, value: Any, duration_seconds: int) -> int:
        try:
            n = int(round(float(value)))
        except Exception:
            return 0
        if duration_seconds > 0:
            return max(0, min(duration_seconds, n))
        return max(0, n)

    def _normalize_point_list(
        self,
        items: Any,
        *,
        key: str,
        duration_seconds: int,
    ) -> list[dict[str, int]]:
        if not isinstance(items, list):
            return []
        out: list[dict[str, int]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            out.append(
                {
                    "time": self._norm_time(item.get("time"), duration_seconds),
                    key: self._clamp_int(item.get(key)),
                }
            )
        out.sort(key=lambda x: x["time"])
        return out

    def _normalize_text_markers(self, items: Any, duration_seconds: int) -> list[dict[str, Any]]:
        if not isinstance(items, list):
            return []
        out: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            out.append(
                {
                    "time": self._norm_time(item.get("time"), duration_seconds),
                    "text": str(item.get("text") or "").strip(),
                }
            )
        out.sort(key=lambda x: x["time"])
        return out

    def _normalize_payload(
        self,
        payload: dict[str, Any],
        *,
        duration_seconds: int,
        interval_seconds: int,
    ) -> dict[str, Any]:
        curiosity_raw = payload.get("curiosity") if isinstance(payload.get("curiosity"), dict) else {}
        emotional_raw = payload.get("emotional_arc") if isinstance(payload.get("emotional_arc"), dict) else {}
        tension_raw = payload.get("tension_release") if isinstance(payload.get("tension_release"), dict) else {}
        persuasion_raw = payload.get("persuasion_signals") if isinstance(payload.get("persuasion_signals"), dict) else {}
        cognitive_raw = payload.get("cognitive_load") if isinstance(payload.get("cognitive_load"), dict) else {}

        emotional_timeline = self._normalize_point_list(
            emotional_raw.get("emotionalTimeline"),
            key="intensity",
            duration_seconds=duration_seconds,
        )
        tension_curve = self._normalize_point_list(
            tension_raw.get("tensionCurve"),
            key="value",
            duration_seconds=duration_seconds,
        )
        release_curve = self._normalize_point_list(
            tension_raw.get("releaseCurve"),
            key="value",
            duration_seconds=duration_seconds,
        )
        density_timeline = self._normalize_point_list(
            cognitive_raw.get("densityTimeline"),
            key="density",
            duration_seconds=duration_seconds,
        )

        if not emotional_timeline:
            emotional_timeline = [{"time": 0, "intensity": 0}]
        if not tension_curve:
            tension_curve = [{"time": 0, "value": 0}]
        if not release_curve:
            release_curve = [{"time": 0, "value": 0}]
        if not density_timeline:
            density_timeline = [{"time": 0, "density": 0}]

        overload_from_density = any(point["density"] > 75 for point in density_timeline)
        overload_detected = cognitive_raw.get("overloadDetected")
        overload_value = bool(overload_detected) if isinstance(overload_detected, bool) else overload_from_density

        curiosity_narrative_raw = (
            payload.get("curiosity_narrative")
            if isinstance(payload.get("curiosity_narrative"), dict)
            else {}
        )
        persuasion_narrative_raw = (
            payload.get("persuasion_narrative")
            if isinstance(payload.get("persuasion_narrative"), dict)
            else {}
        )

        def _word_count(text: str) -> int:
            return len([w for w in re.split(r"\s+", text.strip()) if w])

        def _fallback_interval_narrative(kind: str, start: int, end: int) -> str:
            if kind == "curiosity":
                return (
                    "This segment presents incremental curiosity pressure through unresolved framing and partial disclosure. "
                    "The message withholds full context while signaling forthcoming clarity, sustaining anticipation without immediate payoff. "
                    "Viewer expectation remains active as the narrative arc continues."
                )
            return (
                "This interval emphasizes a dominant influence frame by combining assertive language with implied credibility cues. "
                "The persuasion approach reinforces interpretive certainty while narrowing alternatives, which can increase compliance readiness "
                "for viewers already aligned with the message context."
            )

        def _normalize_curiosity_narrative_intervals(items: Any, fallback_step: int) -> list[dict[str, Any]]:
            if not isinstance(items, list):
                items = []
            out: list[dict[str, Any]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                start = self._norm_time(item.get("start"), duration_seconds)
                default_end = start + fallback_step
                end = self._norm_time(item.get("end", default_end), duration_seconds)
                if end <= start:
                    end = min(duration_seconds if duration_seconds > 0 else start + fallback_step, start + fallback_step)
                narrative = str(item.get("narrative") or "").strip()
                if _word_count(narrative) < 30 or _word_count(narrative) > 50:
                    narrative = _fallback_interval_narrative("curiosity", start, end)
                out.append(
                    {
                        "start": start,
                        "end": end,
                        "narrative": narrative,
                        "intensity": self._clamp_int(item.get("intensity")),
                    }
                )
            if not out:
                step = fallback_step
                end = min(duration_seconds if duration_seconds > 0 else step, step)
                out = [
                    {
                        "start": 0,
                        "end": end,
                        "narrative": _fallback_interval_narrative("curiosity", 0, end),
                        "intensity": 0,
                    }
                ]
            out.sort(key=lambda x: x["start"])
            return out

        def _normalize_persuasion_narrative_intervals(items: Any, fallback_step: int) -> list[dict[str, Any]]:
            allowed = {"Authority", "Urgency", "Social Proof", "Certainty", "Scarcity", "None"}
            if not isinstance(items, list):
                items = []
            out: list[dict[str, Any]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                start = self._norm_time(item.get("start"), duration_seconds)
                default_end = start + fallback_step
                end = self._norm_time(item.get("end", default_end), duration_seconds)
                if end <= start:
                    end = min(duration_seconds if duration_seconds > 0 else start + fallback_step, start + fallback_step)
                narrative = str(item.get("narrative") or "").strip()
                if _word_count(narrative) < 30 or _word_count(narrative) > 50:
                    narrative = _fallback_interval_narrative("persuasion", start, end)
                dominant = str(item.get("dominantSignal") or "None").strip()
                if dominant not in allowed:
                    dominant = "None"
                out.append(
                    {
                        "start": start,
                        "end": end,
                        "narrative": narrative,
                        "dominantSignal": dominant,
                        "intensity": self._clamp_int(item.get("intensity")),
                    }
                )
            if not out:
                step = fallback_step
                end = min(duration_seconds if duration_seconds > 0 else step, step)
                out = [
                    {
                        "start": 0,
                        "end": end,
                        "narrative": _fallback_interval_narrative("persuasion", 0, end),
                        "dominantSignal": "None",
                        "intensity": 0,
                    }
                ]
            out.sort(key=lambda x: x["start"])
            return out

        fallback_step = 2 if interval_seconds == 2 else 5
        curiosity_narrative = {
            "interval_seconds": fallback_step,
            "curiosityScore": self._clamp_int(curiosity_narrative_raw.get("curiosityScore", curiosity_raw.get("curiosityScore"))),
            "totalOpenLoops": max(0, int(curiosity_narrative_raw.get("totalOpenLoops") or 0)),
            "avgLoopDuration": max(0, int(round(float(curiosity_narrative_raw.get("avgLoopDuration") or 0)))),
            "intervals": _normalize_curiosity_narrative_intervals(curiosity_narrative_raw.get("intervals"), fallback_step),
        }
        dominant_signal = str(persuasion_narrative_raw.get("dominantSignal") or "None").strip()
        if dominant_signal not in {"Authority", "Urgency", "Social Proof", "Certainty", "Scarcity", "None"}:
            dominant_signal = "None"
        persuasion_narrative = {
            "interval_seconds": fallback_step,
            "persuasionScore": self._clamp_int(persuasion_narrative_raw.get("persuasionScore")),
            "dominantSignal": dominant_signal,
            "intervals": _normalize_persuasion_narrative_intervals(persuasion_narrative_raw.get("intervals"), fallback_step),
        }

        return {
            "curiosity": {
                "curiosityScore": self._clamp_int(curiosity_raw.get("curiosityScore")),
                "spikes": self._normalize_point_list(curiosity_raw.get("spikes"), key="intensity", duration_seconds=duration_seconds),
                "openLoops": self._normalize_text_markers(curiosity_raw.get("openLoops"), duration_seconds),
                "closedLoops": self._normalize_text_markers(curiosity_raw.get("closedLoops"), duration_seconds),
            },
            "curiosity_narrative": curiosity_narrative,
            "emotional_arc": {
                "emotionalTimeline": emotional_timeline,
                "highestPeak": {
                    "time": self._norm_time((emotional_raw.get("highestPeak") or {}).get("time"), duration_seconds),
                    "value": self._clamp_int((emotional_raw.get("highestPeak") or {}).get("value")),
                },
                "strongestDrop": {
                    "time": self._norm_time((emotional_raw.get("strongestDrop") or {}).get("time"), duration_seconds),
                    "value": self._clamp_int((emotional_raw.get("strongestDrop") or {}).get("value")),
                },
                "volatilityScore": self._clamp_int(emotional_raw.get("volatilityScore")),
            },
            "tension_release": {
                "tensionCurve": tension_curve,
                "releaseCurve": release_curve,
                "totalCycles": max(0, int(tension_raw.get("totalCycles") or 0)),
                "avgBuildDuration": max(0, int(round(float(tension_raw.get("avgBuildDuration") or 0)))),
                "unresolvedCount": max(0, int(tension_raw.get("unresolvedCount") or 0)),
            },
            "persuasion_signals": {
                "authority": self._clamp_int(persuasion_raw.get("authority")),
                "urgency": self._clamp_int(persuasion_raw.get("urgency")),
                "socialProof": self._clamp_int(persuasion_raw.get("socialProof")),
                "certainty": self._clamp_int(persuasion_raw.get("certainty")),
                "scarcity": self._clamp_int(persuasion_raw.get("scarcity")),
            },
            "persuasion_narrative": persuasion_narrative,
            "cognitive_load": {
                "cognitiveScore": self._clamp_int(cognitive_raw.get("cognitiveScore")),
                "densityTimeline": density_timeline,
                "overloadDetected": overload_value,
            },
        }
