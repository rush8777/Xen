from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.exc import OperationalError

from ..database import SessionLocal
from ..models import Project, ProjectContentFeatures, ProjectOverview
from .content_features.constants import FEATURE_IDS, MIN_LONGFORM_SECONDS, FeatureGenerationContext
from .content_features.features.chapters_feature import PROMPT_VERSION as CHAPTERS_PROMPT_VERSION
from .content_features.features.chapters_feature import generate_chapters_payload
from .content_features.features.clips_feature import PROMPT_VERSION as CLIPS_PROMPT_VERSION
from .content_features.features.clips_feature import generate_clips_payload
from .content_features.features.moments_feature import PROMPT_VERSION as MOMENTS_PROMPT_VERSION
from .content_features.features.moments_feature import generate_moments_payload
from .content_features.features.subtitles_feature import PROMPT_VERSION as SUBTITLES_PROMPT_VERSION
from .content_features.features.subtitles_feature import generate_subtitles_payload
from .content_features.gemini_feature_client import GeminiFeatureClient

logger = logging.getLogger(__name__)


class ProjectContentFeaturesGenerator:
    def __init__(self) -> None:
        self._gemini_client = GeminiFeatureClient()

    async def generate_all(self, project_id: int, *, force: bool = False) -> None:
        try:
            self._ensure_record(project_id, reset=force)
            self._set_overall(project_id, status="loading", error=None, started=True)
            self._set_feature_state("clips", project_id, status="loading", progress=5, error=None)
            self._set_feature_state("subtitles", project_id, status="loading", progress=5, error=None)
            self._set_feature_state("chapters", project_id, status="loading", progress=5, error=None)
            self._set_feature_state("moments", project_id, status="loading", progress=5, error=None)

            clip_result = await asyncio.gather(
                self._generate_clips(project_id),
                return_exceptions=True,
            )
            results = clip_result + await asyncio.gather(
                self._generate_subtitles(project_id),
                self._generate_chapters(project_id),
                self._generate_moments(project_id),
                return_exceptions=True,
            )
            errors: list[str] = []
            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    errors.append(f"{FEATURE_IDS[idx]}: {res}")

            status = self._compute_overall_status(project_id)
            self._set_overall(
                project_id,
                status=status,
                error="; ".join(errors) if errors else None,
                completed=self._all_features_finished(project_id),
            )
        except Exception as exc:
            logger.exception(
                "Project content feature generation failed for project_id=%s",
                project_id,
            )
            try:
                self._set_overall(project_id, status="error", error=str(exc), completed=True)
            except Exception:
                logger.exception(
                    "Failed to persist content feature failure state for project_id=%s",
                    project_id,
                )

    async def generate_feature(self, project_id: int, feature_id: str, *, force: bool = False) -> None:
        if feature_id not in FEATURE_IDS:
            raise ValueError(f"Unsupported feature_id: {feature_id}")
        try:
            self._ensure_record(project_id, reset=False)
            if force:
                self._reset_feature(project_id, feature_id)

            self._set_overall(project_id, status="processing", error=None, started=True)
            self._set_feature_state(feature_id, project_id, status="loading", progress=5, error=None)
            await self._run_feature(project_id, feature_id)
            status = self._compute_overall_status(project_id)
            self._set_overall(
                project_id,
                status=status,
                error=None,
                completed=self._all_features_finished(project_id),
            )
        except Exception as exc:
            logger.exception(
                "Project content feature generation failed for project_id=%s feature_id=%s",
                project_id,
                feature_id,
            )
            self._set_feature_state(feature_id, project_id, status="error", progress=100, error=str(exc))
            status = self._compute_overall_status(project_id)
            self._set_overall(project_id, status=status, error=str(exc), completed=self._all_features_finished(project_id))

    def _commit_with_retry(self, db, *, retries: int = 5, sleep_seconds: float = 0.15) -> None:
        for attempt in range(retries + 1):
            try:
                db.commit()
                return
            except OperationalError as exc:
                db.rollback()
                message = str(exc).lower()
                is_locked = "database is locked" in message or "database table is locked" in message
                if not is_locked or attempt >= retries:
                    raise
                time.sleep(sleep_seconds * (attempt + 1))

    def _ensure_record(self, project_id: int, *, reset: bool = False) -> None:
        db = SessionLocal()
        try:
            record = (
                db.query(ProjectContentFeatures)
                .filter(ProjectContentFeatures.project_id == project_id)
                .first()
            )
            if not record:
                record = ProjectContentFeatures(project_id=project_id)
                db.add(record)
                self._commit_with_retry(db)
                return
            if reset:
                record.status = "not_started"
                record.started_at = None
                record.completed_at = None
                record.error = None
                for feature in FEATURE_IDS:
                    setattr(record, f"{feature}_status", "not_started")
                    setattr(record, f"{feature}_progress", 0)
                    setattr(record, f"{feature}_json", "{}")
                    setattr(record, f"{feature}_error", None)
                record.version = int(record.version or 1) + 1
                self._commit_with_retry(db)
        finally:
            db.close()

    def _set_overall(
        self,
        project_id: int,
        *,
        status: str,
        error: str | None = None,
        started: bool = False,
        completed: bool = False,
    ) -> None:
        db = SessionLocal()
        try:
            record = (
                db.query(ProjectContentFeatures)
                .filter(ProjectContentFeatures.project_id == project_id)
                .first()
            )
            if not record:
                return
            record.status = status
            record.error = error
            if started:
                record.started_at = datetime.utcnow()
                record.completed_at = None
            if completed:
                record.completed_at = datetime.utcnow()
            self._commit_with_retry(db)
        finally:
            db.close()

    def _set_feature_state(
        self,
        feature_id: str,
        project_id: int,
        *,
        status: str,
        progress: int | None = None,
        payload: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        db = SessionLocal()
        try:
            record = (
                db.query(ProjectContentFeatures)
                .filter(ProjectContentFeatures.project_id == project_id)
                .first()
            )
            if not record:
                return
            setattr(record, f"{feature_id}_status", status)
            if progress is not None:
                setattr(record, f"{feature_id}_progress", max(0, min(100, int(progress))))
            if payload is not None:
                setattr(record, f"{feature_id}_json", json.dumps(payload))
            setattr(record, f"{feature_id}_error", error)
            self._commit_with_retry(db)
        finally:
            db.close()

    def _reset_feature(self, project_id: int, feature_id: str) -> None:
        db = SessionLocal()
        try:
            record = (
                db.query(ProjectContentFeatures)
                .filter(ProjectContentFeatures.project_id == project_id)
                .first()
            )
            if not record:
                return
            setattr(record, f"{feature_id}_status", "not_started")
            setattr(record, f"{feature_id}_progress", 0)
            setattr(record, f"{feature_id}_json", "{}")
            setattr(record, f"{feature_id}_error", None)
            record.version = int(record.version or 1) + 1
            self._commit_with_retry(db)
        finally:
            db.close()

    def _compute_overall_status(self, project_id: int) -> str:
        db = SessionLocal()
        try:
            record = (
                db.query(ProjectContentFeatures)
                .filter(ProjectContentFeatures.project_id == project_id)
                .first()
            )
            if not record:
                return "error"
            statuses = [getattr(record, f"{f}_status") for f in FEATURE_IDS]
            if all(s == "not_started" for s in statuses):
                return "not_started"
            if all(s == "completed" for s in statuses):
                return "completed"
            if any(s == "error" for s in statuses):
                return "error"
            if any(s in {"loading", "processing"} for s in statuses):
                return "processing"
            if any(s == "completed" for s in statuses):
                return "processing"
            return "not_started"
        finally:
            db.close()

    def _all_features_finished(self, project_id: int) -> bool:
        db = SessionLocal()
        try:
            record = (
                db.query(ProjectContentFeatures)
                .filter(ProjectContentFeatures.project_id == project_id)
                .first()
            )
            if not record:
                return False
            statuses = [getattr(record, f"{f}_status") for f in FEATURE_IDS]
            return all(s in {"completed", "error"} for s in statuses)
        finally:
            db.close()

    def _load_context(self, project_id: int) -> FeatureGenerationContext:
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError("Project not found")
            cached_content_name = (project.gemini_cached_content_name or "").strip()
            if not cached_content_name:
                raise ValueError(
                    "No Gemini cached content available for this project. Re-run analysis to cache the video."
                )
            overview = (
                db.query(ProjectOverview)
                .filter(ProjectOverview.project_id == project_id)
                .first()
            )
            return FeatureGenerationContext(
                project_id=project.id,
                project_name=project.name or f"Project {project.id}",
                video_url=project.video_url or "",
                duration_seconds=int(project.video_duration_seconds or 0),
                cached_content_name=cached_content_name,
                overview_summary=(overview.summary if overview else None),
            )
        finally:
            db.close()

    def _attach_meta(self, payload: dict[str, Any], *, prompt_version: str) -> dict[str, Any]:
        output = dict(payload)
        output["_meta"] = {
            "model": self._gemini_client.model,
            "prompt_version": prompt_version,
            "generated_at": datetime.utcnow().isoformat(),
            "source": "cached_video",
        }
        return output

    async def _run_feature(self, project_id: int, feature_id: str) -> None:
        if feature_id == "clips":
            await self._generate_clips(project_id)
            return
        if feature_id == "subtitles":
            await self._generate_subtitles(project_id)
            return
        if feature_id == "chapters":
            await self._generate_chapters(project_id)
            return
        if feature_id == "moments":
            await self._generate_moments(project_id)
            return
        raise ValueError(f"Unsupported feature_id: {feature_id}")

    async def _generate_clips(self, project_id: int) -> None:
        self._set_feature_state("clips", project_id, status="processing", progress=20, error=None)
        try:
            context = self._load_context(project_id)
            duration = context.duration_seconds
            if duration < MIN_LONGFORM_SECONDS:
                payload = {
                    "key_moments": [],
                    "clips": [],
                    "generation_skipped": True,
                    "skip_reason": "Clip Generator requires videos longer than 3 minutes.",
                    "min_duration_seconds": MIN_LONGFORM_SECONDS,
                    "video_duration_seconds": max(0, duration),
                }
                self._set_feature_state("clips", project_id, status="completed", progress=100, payload=payload, error=None)
                return

            payload = await generate_clips_payload(context, self._gemini_client)
            payload = self._attach_meta(payload, prompt_version=CLIPS_PROMPT_VERSION)
            self._set_feature_state("clips", project_id, status="completed", progress=100, payload=payload, error=None)
        except Exception as exc:
            self._set_feature_state("clips", project_id, status="error", progress=100, error=str(exc))

    async def _generate_subtitles(self, project_id: int) -> None:
        self._set_feature_state("subtitles", project_id, status="processing", progress=15, error=None)
        try:
            context = self._load_context(project_id)
            payload = await generate_subtitles_payload(context, self._gemini_client)
            payload = self._attach_meta(payload, prompt_version=SUBTITLES_PROMPT_VERSION)
            self._set_feature_state("subtitles", project_id, status="completed", progress=100, payload=payload, error=None)
        except Exception as exc:
            self._set_feature_state("subtitles", project_id, status="error", progress=100, error=str(exc))

    async def _generate_chapters(self, project_id: int) -> None:
        self._set_feature_state("chapters", project_id, status="processing", progress=30, error=None)
        try:
            context = self._load_context(project_id)
            payload = await generate_chapters_payload(context, self._gemini_client)
            payload = self._attach_meta(payload, prompt_version=CHAPTERS_PROMPT_VERSION)
            self._set_feature_state(
                "chapters",
                project_id,
                status="completed",
                progress=100,
                payload=payload,
                error=None,
            )
        except Exception as exc:
            self._set_feature_state("chapters", project_id, status="error", progress=100, error=str(exc))

    async def _generate_moments(self, project_id: int) -> None:
        self._set_feature_state("moments", project_id, status="processing", progress=25, error=None)
        try:
            context = self._load_context(project_id)
            duration = context.duration_seconds
            if duration < MIN_LONGFORM_SECONDS:
                payload = {
                    "moments": [],
                    "generation_skipped": True,
                    "skip_reason": "Key Moments require videos longer than 3 minutes.",
                    "min_duration_seconds": MIN_LONGFORM_SECONDS,
                    "video_duration_seconds": max(0, duration),
                }
                self._set_feature_state("moments", project_id, status="completed", progress=100, payload=payload, error=None)
                return

            payload = await generate_moments_payload(context, self._gemini_client)
            payload = self._attach_meta(payload, prompt_version=MOMENTS_PROMPT_VERSION)
            self._set_feature_state("moments", project_id, status="completed", progress=100, payload=payload, error=None)
        except Exception as exc:
            self._set_feature_state("moments", project_id, status="error", progress=100, error=str(exc))

    def export_subtitles(self, subtitle_payload: dict[str, Any], fmt: str) -> tuple[str, str, str]:
        segments = subtitle_payload.get("segments")
        if not isinstance(segments, list):
            raise ValueError("Invalid subtitles payload")

        def ts(total_seconds: int, *, vtt: bool) -> str:
            total_seconds = max(0, int(total_seconds))
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            ms = 0
            if vtt:
                return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        is_vtt = fmt == "vtt"
        lines: list[str] = []
        if is_vtt:
            lines.append("WEBVTT")
            lines.append("")

        for idx, segment in enumerate(segments, start=1):
            start = int(segment.get("start_time_seconds", 0) or 0)
            end = int(segment.get("end_time_seconds", start + 1) or (start + 1))
            text_lines = segment.get("lines")
            if not isinstance(text_lines, list) or not text_lines:
                text_lines = [str(segment.get("text") or "").strip()]
            text_lines = [str(t).strip() for t in text_lines if str(t).strip()]
            if not text_lines:
                continue
            if not is_vtt:
                lines.append(str(idx))
            lines.append(f"{ts(start, vtt=is_vtt)} --> {ts(end, vtt=is_vtt)}")
            lines.extend(text_lines[:2])
            lines.append("")

        content = "\n".join(lines).strip() + "\n"
        ext = "vtt" if is_vtt else "srt"
        filename = f"subtitles_{uuid.uuid4().hex[:8]}.{ext}"
        mime = "text/vtt" if is_vtt else "application/x-subrip"
        return filename, content, mime
