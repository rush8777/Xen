from __future__ import annotations

import json
import logging
from datetime import datetime

from ..database import SessionLocal
from ..models import (
    AnalysisRun,
    PremiumTranscriptInterval,
    Project,
    ProjectPsychologyAnalysis,
)
from .project_psychology_generator import ProjectPsychologyGenerator

logger = logging.getLogger(__name__)

RUN_TYPE_PSYCHOLOGY = "psychology"

_psychology_generator = ProjectPsychologyGenerator()


def ensure_psychology_pending(*, project_id: int) -> ProjectPsychologyAnalysis:
    db = SessionLocal()
    try:
        return ensure_psychology_pending_with_db(project_id=project_id, db=db)
    finally:
        db.close()


def ensure_psychology_pending_with_db(
    *,
    project_id: int,
    db,
) -> ProjectPsychologyAnalysis:
    record = (
        db.query(ProjectPsychologyAnalysis)
        .filter(ProjectPsychologyAnalysis.project_id == project_id)
        .first()
    )
    if not record:
        record = ProjectPsychologyAnalysis(
            project_id=project_id,
            psychology_json="{}",
            status="pending",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    record.status = "pending"
    record.error = None
    db.commit()
    db.refresh(record)
    return record


def create_psychology_run_with_db(
    *,
    project_id: int,
    db,
) -> AnalysisRun:
    run = AnalysisRun(
        project_id=project_id,
        run_type=RUN_TYPE_PSYCHOLOGY,
        status="pending",
        started_at=None,
        completed_at=None,
        error=None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def create_psychology_run(*, project_id: int) -> AnalysisRun:
    db = SessionLocal()
    try:
        return create_psychology_run_with_db(project_id=project_id, db=db)
    finally:
        db.close()


def update_psychology_run_status(
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


def execute_psychology_generation(
    *,
    project_id: int,
    run_id: int | None = None,
    interval_seconds: int = 5,
) -> None:
    db = SessionLocal()
    try:
        safe_interval_seconds = 2 if interval_seconds == 2 else 5
        update_psychology_run_status(run_id=run_id, status="running", started=True)

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error("Project %s not found for psychology generation", project_id)
            update_psychology_run_status(run_id=run_id, status="failed", error="Project not found", completed=True)
            return

        record = (
            db.query(ProjectPsychologyAnalysis)
            .filter(ProjectPsychologyAnalysis.project_id == project_id)
            .first()
        )
        if not record:
            record = ProjectPsychologyAnalysis(project_id=project_id, psychology_json="{}", status="pending")
            db.add(record)
            db.commit()
            db.refresh(record)

        record.status = "pending"
        record.error = None
        db.commit()

        if not project.gemini_cached_content_name:
            raise RuntimeError("No Gemini cached video found for this project.")

        transcript_rows = (
            db.query(PremiumTranscriptInterval)
            .filter(PremiumTranscriptInterval.project_id == project_id)
            .order_by(PremiumTranscriptInterval.interval_index.asc())
            .all()
        )
        transcript_parts = [str(row.transcript_text or "").strip() for row in transcript_rows]
        transcript_passage = "\n\n".join(part for part in transcript_parts if part)

        psychology_payload = _psychology_generator.generate_psychology(
            cached_content_name=project.gemini_cached_content_name,
            project_name=project.name or "",
            video_url=project.video_url or "",
            video_duration_seconds=project.video_duration_seconds,
            transcript_passage=transcript_passage,
            interval_seconds=safe_interval_seconds,
        )

        try:
            existing_json = json.loads(record.psychology_json or "{}")
        except Exception:
            existing_json = {}
        if not isinstance(existing_json, dict):
            existing_json = {}
        variants = existing_json.get("variants")
        if not isinstance(variants, dict):
            variants = {}
        variants[str(safe_interval_seconds)] = psychology_payload

        record.psychology_json = json.dumps(
            {
                "variants": variants,
                "latest_interval_seconds": safe_interval_seconds,
            }
        )
        record.status = "completed"
        record.generated_at = datetime.utcnow()
        record.error = None
        record.version = _psychology_generator.schema_version
        db.commit()

        update_psychology_run_status(run_id=run_id, status="completed", completed=True)
        logger.info("Psychology generation completed for project %s (run_id=%s)", project_id, run_id)
    except Exception as exc:
        logger.error("Psychology generation failed for project %s: %s", project_id, exc)
        try:
            record = (
                db.query(ProjectPsychologyAnalysis)
                .filter(ProjectPsychologyAnalysis.project_id == project_id)
                .first()
            )
            if record:
                record.status = "failed"
                record.error = str(exc)
                db.commit()
        except Exception:
            pass
        update_psychology_run_status(
            run_id=run_id,
            status="failed",
            error=str(exc),
            completed=True,
        )
    finally:
        db.close()
