from __future__ import annotations

import json
import logging
from threading import Thread
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_db
from ..models import PremiumTranscriptInterval, Project, ProjectContentFeatures
from ..services.content_features_generator import FEATURE_IDS, ProjectContentFeaturesGenerator
from ..services.task_queue import QueueConfigurationError, enqueue_content_features_generation
from ..services.worker_tasks import run_content_features_task

router = APIRouter(prefix="/api/projects", tags=["project-content-features"])
logger = logging.getLogger(__name__)

generator = ProjectContentFeaturesGenerator()


FeatureStatus = Literal["not_started", "loading", "processing", "completed", "error"]
FeatureId = Literal["clips", "subtitles", "chapters", "moments"]


class FeatureStateResponse(BaseModel):
    status: FeatureStatus
    progress: int
    error: str | None
    updated_at: str | None


class ContentFeaturesStatusResponse(BaseModel):
    project_id: int
    features: dict[str, FeatureStateResponse]
    started_at: str | None
    completed_at: str | None


class GenerateContentFeaturesRequest(BaseModel):
    force: bool = False


class GenerateContentFeatureRequest(BaseModel):
    force: bool = False


class GenerateContentFeaturesResponse(BaseModel):
    project_id: int
    triggered: bool
    status: str
    message: str


class FeaturePayloadResponse(BaseModel):
    project_id: int
    feature_id: FeatureId
    payload: dict[str, Any]
    status: FeatureStatus


class SubtitleExportRequest(BaseModel):
    format: Literal["srt", "vtt"]
    language: str | None = None


class SubtitleExportResponse(BaseModel):
    filename: str
    content: str
    mime_type: str


class TranscriptSegment(BaseModel):
    start_time_seconds: int
    end_time_seconds: int
    text: str


class TranscriptPassageResponse(BaseModel):
    project_id: int
    source: str
    passage: str
    segments: list[TranscriptSegment]


def _ensure_project(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_or_init_record(project_id: int, db: Session) -> ProjectContentFeatures:
    record = (
        db.query(ProjectContentFeatures)
        .filter(ProjectContentFeatures.project_id == project_id)
        .first()
    )
    if record:
        return record
    record = ProjectContentFeatures(project_id=project_id)
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError:
        # Concurrent request inserted the same project_id first.
        db.rollback()
        existing = (
            db.query(ProjectContentFeatures)
            .filter(ProjectContentFeatures.project_id == project_id)
            .first()
        )
        if existing:
            return existing
        raise


def _feature_state(record: ProjectContentFeatures, feature_id: str) -> FeatureStateResponse:
    return FeatureStateResponse(
        status=getattr(record, f"{feature_id}_status") or "not_started",
        progress=int(getattr(record, f"{feature_id}_progress") or 0),
        error=getattr(record, f"{feature_id}_error"),
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
    )


@router.get("/{project_id}/content-features/status", response_model=ContentFeaturesStatusResponse)
def get_content_features_status(project_id: int, db: Session = Depends(get_db)) -> ContentFeaturesStatusResponse:
    _ensure_project(project_id, db)
    record = _get_or_init_record(project_id, db)
    return ContentFeaturesStatusResponse(
        project_id=project_id,
        features={feature_id: _feature_state(record, feature_id) for feature_id in FEATURE_IDS},
        started_at=record.started_at.isoformat() if record.started_at else None,
        completed_at=record.completed_at.isoformat() if record.completed_at else None,
    )


@router.post("/{project_id}/content-features/generate", response_model=GenerateContentFeaturesResponse)
async def generate_content_features(
    project_id: int,
    payload: GenerateContentFeaturesRequest,
    db: Session = Depends(get_db),
) -> GenerateContentFeaturesResponse:
    _ensure_project(project_id, db)
    record = _get_or_init_record(project_id, db)
    current_statuses = [getattr(record, f"{feature_id}_status") for feature_id in FEATURE_IDS]
    if not payload.force and any(status in {"loading", "processing"} for status in current_statuses):
        return GenerateContentFeaturesResponse(
            project_id=project_id,
            triggered=False,
            status=record.status or "processing",
            message="Content feature generation is already in progress.",
        )

    if settings.TASKS_MODE == "cloud_tasks":
        try:
            enqueue_content_features_generation(project_id=project_id, feature_id=None, force=payload.force)
        except QueueConfigurationError as exc:
            logger.warning(
                "Cloud Tasks unavailable for content features project %s; falling back to local thread: %s",
                project_id,
                exc,
            )
            Thread(
                target=run_content_features_task,
                kwargs={"project_id": project_id, "feature_id": None, "force": payload.force},
                daemon=True,
            ).start()
        except Exception as exc:
            logger.exception("Failed to enqueue content features task for project %s", project_id)
            raise HTTPException(status_code=500, detail=f"Failed to enqueue content features task: {exc}")
    else:
        Thread(
            target=run_content_features_task,
            kwargs={"project_id": project_id, "feature_id": None, "force": payload.force},
            daemon=True,
        ).start()
    return GenerateContentFeaturesResponse(
        project_id=project_id,
        triggered=True,
        status="loading",
        message="Content feature generation started in background.",
    )


@router.post("/{project_id}/content-features/{feature_id}/generate", response_model=GenerateContentFeaturesResponse)
async def generate_content_feature(
    project_id: int,
    feature_id: FeatureId,
    payload: GenerateContentFeatureRequest,
    db: Session = Depends(get_db),
) -> GenerateContentFeaturesResponse:
    _ensure_project(project_id, db)
    if feature_id not in FEATURE_IDS:
        raise HTTPException(status_code=400, detail=f"Unsupported feature: {feature_id}")
    record = _get_or_init_record(project_id, db)
    current_status = getattr(record, f"{feature_id}_status") or "not_started"
    if not payload.force and current_status in {"loading", "processing"}:
        return GenerateContentFeaturesResponse(
            project_id=project_id,
            triggered=False,
            status=current_status,
            message=f"Feature '{feature_id}' generation is already in progress.",
        )

    if settings.TASKS_MODE == "cloud_tasks":
        try:
            enqueue_content_features_generation(project_id=project_id, feature_id=feature_id, force=payload.force)
        except QueueConfigurationError as exc:
            logger.warning(
                "Cloud Tasks unavailable for content feature project %s; falling back to local thread: %s",
                project_id,
                exc,
            )
            Thread(
                target=run_content_features_task,
                kwargs={"project_id": project_id, "feature_id": feature_id, "force": payload.force},
                daemon=True,
            ).start()
        except Exception as exc:
            logger.exception("Failed to enqueue content feature task for project %s", project_id)
            raise HTTPException(status_code=500, detail=f"Failed to enqueue content feature task: {exc}")
    else:
        Thread(
            target=run_content_features_task,
            kwargs={"project_id": project_id, "feature_id": feature_id, "force": payload.force},
            daemon=True,
        ).start()
    return GenerateContentFeaturesResponse(
        project_id=project_id,
        triggered=True,
        status="loading",
        message=f"Feature '{feature_id}' generation started in background.",
    )


@router.get("/{project_id}/content-features/{feature_id}", response_model=FeaturePayloadResponse)
def get_feature_payload(
    project_id: int,
    feature_id: FeatureId,
    db: Session = Depends(get_db),
) -> FeaturePayloadResponse:
    _ensure_project(project_id, db)
    if feature_id not in FEATURE_IDS:
        raise HTTPException(status_code=400, detail=f"Unsupported feature: {feature_id}")
    record = _get_or_init_record(project_id, db)
    feature_status = getattr(record, f"{feature_id}_status") or "not_started"
    if feature_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Feature '{feature_id}' not ready. Current status: {feature_status}",
        )

    raw = getattr(record, f"{feature_id}_json") or "{}"
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {}
    return FeaturePayloadResponse(
        project_id=project_id,
        feature_id=feature_id,
        payload=payload if isinstance(payload, dict) else {},
        status=feature_status,
    )


@router.post("/{project_id}/content-features/subtitles/export", response_model=SubtitleExportResponse)
def export_subtitles(
    project_id: int,
    payload: SubtitleExportRequest,
    db: Session = Depends(get_db),
) -> SubtitleExportResponse:
    _ensure_project(project_id, db)
    record = _get_or_init_record(project_id, db)
    subtitle_status = record.subtitles_status or "not_started"
    if subtitle_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Subtitles not ready. Current status: {subtitle_status}",
        )
    try:
        subtitle_json = json.loads(record.subtitles_json or "{}")
    except Exception:
        subtitle_json = {}
    try:
        filename, content, mime_type = generator.export_subtitles(subtitle_json, payload.format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return SubtitleExportResponse(filename=filename, content=content, mime_type=mime_type)


@router.get("/{project_id}/transcript-passage", response_model=TranscriptPassageResponse)
def get_transcript_passage(
    project_id: int,
    db: Session = Depends(get_db),
) -> TranscriptPassageResponse:
    _ensure_project(project_id, db)

    premium_rows = (
        db.query(PremiumTranscriptInterval)
        .filter(PremiumTranscriptInterval.project_id == project_id)
        .order_by(
            PremiumTranscriptInterval.interval_index.asc(),
            PremiumTranscriptInterval.start_time_seconds.asc(),
            PremiumTranscriptInterval.id.asc(),
        )
        .all()
    )

    premium_segments: list[TranscriptSegment] = []
    for row in premium_rows:
        text = (row.transcript_text or "").strip()
        if not text:
            continue
        premium_segments.append(
            TranscriptSegment(
                start_time_seconds=int(row.start_time_seconds or 0),
                end_time_seconds=int(row.end_time_seconds or 0),
                text=text,
            )
        )

    if premium_segments:
        return TranscriptPassageResponse(
            project_id=project_id,
            source="premium_transcript_table",
            passage="\n\n".join(segment.text for segment in premium_segments),
            segments=premium_segments,
        )

    record = _get_or_init_record(project_id, db)
    subtitle_segments: list[TranscriptSegment] = []
    try:
        subtitles_payload = json.loads(record.subtitles_json or "{}")
    except Exception:
        subtitles_payload = {}

    raw_segments = subtitles_payload.get("segments") if isinstance(subtitles_payload, dict) else None
    if isinstance(raw_segments, list):
        for item in raw_segments:
            if not isinstance(item, dict):
                continue
            lines = item.get("lines")
            text = ""
            if isinstance(lines, list) and lines:
                text = " ".join(str(line).strip() for line in lines if str(line).strip())
            if not text:
                text = str(item.get("text") or "").strip()
            if not text:
                continue
            subtitle_segments.append(
                TranscriptSegment(
                    start_time_seconds=int(item.get("start_time_seconds") or 0),
                    end_time_seconds=int(item.get("end_time_seconds") or 0),
                    text=text,
                )
            )

    if subtitle_segments:
        return TranscriptPassageResponse(
            project_id=project_id,
            source="content_feature_subtitles",
            passage="\n\n".join(segment.text for segment in subtitle_segments),
            segments=subtitle_segments,
        )

    return TranscriptPassageResponse(
        project_id=project_id,
        source="none",
        passage="",
        segments=[],
    )
