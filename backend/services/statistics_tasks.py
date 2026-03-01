from __future__ import annotations

import json
import logging
from datetime import datetime

from ..database import SessionLocal
from ..gemini_backend.config import GEMINI_API_KEY
from ..models import AnalysisRun, Project, ProjectStatistics
from .project_statistics_generator import ProjectStatisticsGenerator

logger = logging.getLogger(__name__)

RUN_TYPE_STATISTICS = "statistics"

_stats_generator = ProjectStatisticsGenerator(api_key=GEMINI_API_KEY)


def ensure_statistics_pending(*, project_id: int) -> ProjectStatistics:
    db = SessionLocal()
    try:
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
            return stats

        stats.status = "pending"
        stats.error = None
        db.commit()
        db.refresh(stats)
        return stats
    finally:
        db.close()


def create_statistics_run(*, project_id: int) -> AnalysisRun:
    db = SessionLocal()
    try:
        run = AnalysisRun(
            project_id=project_id,
            run_type=RUN_TYPE_STATISTICS,
            status="pending",
            started_at=None,
            completed_at=None,
            error=None,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    finally:
        db.close()


def update_run_status(
    *,
    run_id: int | None,
    status: str,
    error: str | None = None,
    started: bool = False,
    completed: bool = False,
) -> None:
    if not run_id:
        return
    db = SessionLocal()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not run:
            return
        run.status = status
        run.error = error
        if started:
            run.started_at = datetime.utcnow()
        if completed:
            run.completed_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def execute_statistics_generation(*, project_id: int, run_id: int | None = None) -> None:
    db = SessionLocal()
    try:
        update_run_status(run_id=run_id, status="running", started=True)

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error("Project %s not found for statistics generation", project_id)
            update_run_status(run_id=run_id, status="failed", error="Project not found", completed=True)
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
            stats_data = _stats_generator.generate_statistics(
                analysis_file_path=project.analysis_file_path or "",
                video_url=project.video_url or "",
                project_name=project.name,
                project_id=project.id,
                job_id=project.job_id,
                cached_content_name=project.gemini_cached_content_name,
                video_duration_seconds=project.video_duration_seconds,
            )

            stats_record.stats_json = json.dumps(stats_data)
            stats_record.status = "completed"
            stats_record.generated_at = datetime.utcnow()
            stats_record.error = None
            db.commit()

            update_run_status(run_id=run_id, status="completed", completed=True)
            logger.info("Statistics generation completed for project %s (run_id=%s)", project_id, run_id)
        except Exception as exc:
            logger.error("Statistics generation failed for project %s: %s", project_id, exc)
            stats_record.status = "failed"
            stats_record.error = str(exc)
            db.commit()
            update_run_status(run_id=run_id, status="failed", error=str(exc), completed=True)
    finally:
        db.close()

