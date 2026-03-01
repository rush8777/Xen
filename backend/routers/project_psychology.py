from __future__ import annotations

import json
import logging
from threading import Thread

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_db
from ..models import Project, ProjectPsychologyAnalysis
from ..services.psychology_tasks import (
    create_psychology_run_with_db,
    execute_psychology_generation,
    ensure_psychology_pending_with_db,
    update_psychology_run_status,
)
from ..services.task_queue import (
    QueueConfigurationError,
    enqueue_psychology_generation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["project-psychology"])


class PsychologyStatusResponse(BaseModel):
    project_id: int
    status: str
    generated_at: str | None
    version: int | None
    error: str | None


class PsychologyResponse(BaseModel):
    project_id: int
    psychology: dict
    generated_at: str
    version: int
    status: str


class PsychologyRegenerateRequest(BaseModel):
    interval_seconds: int = 5


def _normalize_interval_seconds(interval_seconds: int) -> int:
    if interval_seconds not in (2, 5):
        raise HTTPException(status_code=422, detail="interval_seconds must be 2 or 5")
    return interval_seconds


@router.get("/{project_id}/psychology/status", response_model=PsychologyStatusResponse)
def get_project_psychology_status(
    project_id: int,
    db: Session = Depends(get_db),
) -> PsychologyStatusResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    record = (
        db.query(ProjectPsychologyAnalysis)
        .filter(ProjectPsychologyAnalysis.project_id == project_id)
        .first()
    )
    if not record:
        return PsychologyStatusResponse(
            project_id=project_id,
            status="not_started",
            generated_at=None,
            version=None,
            error=None,
        )

    return PsychologyStatusResponse(
        project_id=project_id,
        status=record.status,
        generated_at=record.generated_at.isoformat() if record.generated_at else None,
        version=record.version,
        error=record.error,
    )


@router.post("/{project_id}/psychology/regenerate", response_model=PsychologyStatusResponse)
def regenerate_project_psychology(
    project_id: int,
    payload: PsychologyRegenerateRequest | None = Body(default=None),
    db: Session = Depends(get_db),
) -> PsychologyStatusResponse:
    interval_seconds = _normalize_interval_seconds((payload.interval_seconds if payload else 5))
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    record = (
        db.query(ProjectPsychologyAnalysis)
        .filter(ProjectPsychologyAnalysis.project_id == project_id)
        .first()
    )
    if record and record.status == "pending":
        return PsychologyStatusResponse(
            project_id=project_id,
            status="pending",
            generated_at=None,
            version=record.version,
            error=None,
        )

    record = ensure_psychology_pending_with_db(project_id=project_id, db=db)
    run = create_psychology_run_with_db(project_id=project_id, db=db)

    if settings.TASKS_MODE == "cloud_tasks":
        try:
            enqueue_psychology_generation(
                project_id=project_id,
                run_id=run.id,
                interval_seconds=interval_seconds,
            )
        except QueueConfigurationError as exc:
            logger.warning(
                "Cloud Tasks unavailable for psychology project %s; falling back to local thread: %s",
                project_id,
                exc,
            )
            Thread(
                target=execute_psychology_generation,
                kwargs={
                    "project_id": project_id,
                    "run_id": run.id,
                    "interval_seconds": interval_seconds,
                },
                daemon=True,
            ).start()
        except Exception as exc:
            logger.exception("Failed to enqueue psychology task for project %s", project_id)
            update_psychology_run_status(run_id=run.id, status="failed", error=str(exc), completed=True)
            raise HTTPException(status_code=500, detail=f"Failed to enqueue psychology task: {exc}")
    else:
        Thread(
            target=execute_psychology_generation,
            kwargs={
                "project_id": project_id,
                "run_id": run.id,
                "interval_seconds": interval_seconds,
            },
            daemon=True,
        ).start()

    return PsychologyStatusResponse(
        project_id=project_id,
        status="pending",
        generated_at=None,
        version=record.version,
        error=None,
    )


@router.get("/{project_id}/psychology", response_model=PsychologyResponse)
def get_project_psychology(
    project_id: int,
    interval_seconds: int = Query(default=5),
    db: Session = Depends(get_db),
) -> PsychologyResponse:
    selected_interval = _normalize_interval_seconds(interval_seconds)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    record = (
        db.query(ProjectPsychologyAnalysis)
        .filter(ProjectPsychologyAnalysis.project_id == project_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Psychology analysis not found. Try generating it first.")
    if record.status != "completed":
        raise HTTPException(status_code=400, detail=f"Psychology analysis not ready. Current status: {record.status}")

    try:
        payload = json.loads(record.psychology_json or "{}")
    except Exception:
        payload = {}

    selected_payload = payload
    if isinstance(payload, dict) and isinstance(payload.get("variants"), dict):
        variants = payload.get("variants") or {}
        selected_payload = variants.get(str(selected_interval))
        if not isinstance(selected_payload, dict):
            if variants:
                raise HTTPException(
                    status_code=400,
                    detail=f"Variant not generated for interval_seconds={selected_interval}",
                )
            selected_payload = {}

    return PsychologyResponse(
        project_id=project_id,
        psychology=selected_payload if isinstance(selected_payload, dict) else {},
        generated_at=record.generated_at.isoformat() if record.generated_at else "",
        version=record.version,
        status=record.status,
    )
