from __future__ import annotations

from datetime import datetime

from ..database import SessionLocal
from ..models import PipelineJob, PipelineJobEvent


def create_pipeline_job(
    *,
    job_id: str,
    project_id: int | None,
    job_type: str,
    status: str = "queued",
    step: int = 0,
    message: str = "Queued",
) -> PipelineJob:
    db = SessionLocal()
    try:
        existing = db.query(PipelineJob).filter(PipelineJob.job_id == job_id).first()
        if existing:
            return existing

        row = PipelineJob(
            job_id=job_id,
            project_id=project_id,
            job_type=job_type,
            status=status,
            step=step,
            message=message,
            started_at=datetime.utcnow() if status == "running" else None,
            completed_at=datetime.utcnow() if status in {"completed", "failed"} else None,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        _append_event(
            db=db,
            job_id=job_id,
            status=row.status,
            step=row.step,
            message=row.message,
            error=row.error,
        )
        db.commit()
        return row
    finally:
        db.close()


def update_pipeline_job(
    *,
    job_id: str,
    status: str | None = None,
    step: int | None = None,
    message: str | None = None,
    project_id: int | None = None,
    error: str | None = None,
) -> PipelineJob | None:
    db = SessionLocal()
    try:
        row = db.query(PipelineJob).filter(PipelineJob.job_id == job_id).first()
        if not row:
            return None

        if status is not None:
            row.status = status
        if step is not None:
            row.step = step
        if message is not None:
            row.message = message
        if project_id is not None:
            row.project_id = project_id
        if error is not None:
            row.error = error
        if row.status == "running" and row.started_at is None:
            row.started_at = datetime.utcnow()
        if row.status in {"completed", "failed"}:
            row.completed_at = datetime.utcnow()

        _append_event(
            db=db,
            job_id=row.job_id,
            status=row.status,
            step=row.step,
            message=row.message,
            error=row.error,
        )
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()


def get_pipeline_job(job_id: str) -> PipelineJob | None:
    db = SessionLocal()
    try:
        return db.query(PipelineJob).filter(PipelineJob.job_id == job_id).first()
    finally:
        db.close()


def _append_event(
    *,
    db,
    job_id: str,
    status: str,
    step: int,
    message: str,
    error: str | None,
) -> None:
    db.add(
        PipelineJobEvent(
            job_id=job_id,
            status=status,
            step=step,
            message=message,
            error=error,
        )
    )
