from __future__ import annotations

import json
import logging
from threading import Thread

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_db
from ..models import Project, ProjectStatistics
from ..services.statistics_tasks import (
    create_statistics_run,
    ensure_statistics_pending,
    execute_statistics_generation,
    update_run_status,
)
from ..services.task_queue import QueueConfigurationError, enqueue_statistics_generation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["project-statistics"])


class StatisticsStatusResponse(BaseModel):
    project_id: int
    status: str
    generated_at: str | None
    version: int | None
    error: str | None


class StatisticsResponse(BaseModel):
    project_id: int
    stats: dict
    generated_at: str
    version: int
    status: str


@router.get("/{project_id}/statistics", response_model=StatisticsResponse)
def get_project_statistics(project_id: int, db: Session = Depends(get_db)) -> StatisticsResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stats = (
        db.query(ProjectStatistics)
        .filter(ProjectStatistics.project_id == project_id)
        .first()
    )

    if not stats:
        raise HTTPException(status_code=404, detail="Statistics not found. Try generating them first.")

    if stats.status != "completed":
        raise HTTPException(status_code=400, detail=f"Statistics not ready. Current status: {stats.status}")

    return StatisticsResponse(
        project_id=project_id,
        stats=json.loads(stats.stats_json),
        generated_at=stats.generated_at.isoformat() if stats.generated_at else "",
        version=stats.version,
        status=stats.status,
    )


@router.get("/{project_id}/statistics/status", response_model=StatisticsStatusResponse)
def get_statistics_status(project_id: int, db: Session = Depends(get_db)) -> StatisticsStatusResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stats = (
        db.query(ProjectStatistics)
        .filter(ProjectStatistics.project_id == project_id)
        .first()
    )

    if not stats:
        return StatisticsStatusResponse(
            project_id=project_id,
            status="not_started",
            generated_at=None,
            version=None,
            error=None,
        )

    return StatisticsStatusResponse(
        project_id=project_id,
        status=stats.status,
        generated_at=stats.generated_at.isoformat() if stats.generated_at else None,
        version=stats.version,
        error=stats.error,
    )


@router.post("/{project_id}/statistics/regenerate", response_model=StatisticsStatusResponse)
def regenerate_project_statistics(
    project_id: int,
    db: Session = Depends(get_db),
) -> StatisticsStatusResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stats = (
        db.query(ProjectStatistics)
        .filter(ProjectStatistics.project_id == project_id)
        .first()
    )

    stats = ensure_statistics_pending(project_id=project_id)
    run = create_statistics_run(project_id=project_id)

    if settings.TASKS_MODE == "cloud_tasks":
        try:
            enqueue_statistics_generation(project_id=project_id, run_id=run.id)
        except QueueConfigurationError as exc:
            logger.warning(
                "Cloud Tasks unavailable for statistics project %s; falling back to local thread: %s",
                project_id,
                exc,
            )
            Thread(
                target=execute_statistics_generation,
                kwargs={"project_id": project_id, "run_id": run.id},
                daemon=True,
            ).start()
        except Exception as exc:
            logger.exception("Failed to enqueue statistics task for project %s", project_id)
            update_run_status(run_id=run.id, status="failed", error=str(exc), completed=True)
            raise HTTPException(status_code=500, detail=f"Failed to enqueue statistics task: {exc}")
    else:
        # Local/dev fallback: execute in detached thread to keep API responsive.
        Thread(
            target=execute_statistics_generation,
            kwargs={"project_id": project_id, "run_id": run.id},
            daemon=True,
        ).start()

    return StatisticsStatusResponse(
        project_id=project_id,
        status="pending",
        generated_at=None,
        version=stats.version,
        error=None,
    )
