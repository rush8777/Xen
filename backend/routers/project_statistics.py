from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..dependencies import get_db
from ..gemini_backend.config import GEMINI_API_KEY
from ..models import Project, ProjectStatistics
from ..services.project_statistics_generator import ProjectStatisticsGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["project-statistics"])

stats_generator = ProjectStatisticsGenerator(api_key=GEMINI_API_KEY)


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


def _generate_statistics_sync(project_id: int) -> None:
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error("Project %s not found for statistics generation", project_id)
            return

        stats_record = (
            db.query(ProjectStatistics)
            .filter(ProjectStatistics.project_id == project_id)
            .first()
        )
        if not stats_record:
            stats_record = ProjectStatistics(project_id=project_id, stats_json="{}", status="pending")
            db.add(stats_record)
            db.commit()
            db.refresh(stats_record)

        stats_record.status = "pending"
        stats_record.error = None
        db.commit()

        try:
            stats_data = stats_generator.generate_statistics(
                analysis_file_path=project.analysis_file_path or "",
                video_url=project.video_url or "",
                project_name=project.name,
                project_id=project.id,
                job_id=project.job_id,
            )

            stats_record.stats_json = json.dumps(stats_data)
            stats_record.status = "completed"
            stats_record.generated_at = datetime.utcnow()
            stats_record.error = None
            db.commit()
            logger.info("Statistics generation completed for project %s", project_id)
        except Exception as e:
            logger.error("Statistics generation failed for project %s: %s", project_id, e)
            stats_record.status = "failed"
            stats_record.error = str(e)
            db.commit()
    finally:
        db.close()


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> StatisticsStatusResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.analysis_file_path:
        raise HTTPException(status_code=400, detail="Project has no analysis file. Cannot generate statistics.")

    stats = (
        db.query(ProjectStatistics)
        .filter(ProjectStatistics.project_id == project_id)
        .first()
    )

    if not stats:
        stats = ProjectStatistics(project_id=project_id, stats_json="{}", status="pending")
        db.add(stats)
        db.commit()
        db.refresh(stats)
    else:
        stats.status = "pending"
        stats.error = None
        db.commit()

    background_tasks.add_task(_generate_statistics_sync, project_id)

    return StatisticsStatusResponse(
        project_id=project_id,
        status="pending",
        generated_at=None,
        version=stats.version,
        error=None,
    )
