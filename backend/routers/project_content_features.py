from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Project, ProjectContentFeatures
from ..services.content_features_generator import FEATURE_IDS, ProjectContentFeaturesGenerator

router = APIRouter(prefix="/api/projects", tags=["project-content-features"])

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
    db.commit()
    db.refresh(record)
    return record


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

    asyncio.create_task(generator.generate_all(project_id, force=payload.force))
    return GenerateContentFeaturesResponse(
        project_id=project_id,
        triggered=True,
        status="loading",
        message="Content feature generation started in background.",
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
