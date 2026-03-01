from __future__ import annotations

import logging
import uuid
from datetime import datetime
from threading import Thread

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from ..config import settings
from ..cobalt_downloader import VideoDownloader
from ..dependencies import get_db
from ..models import Project, User, Video
from ..services.pipeline_jobs import create_pipeline_job, get_pipeline_job, update_pipeline_job
from ..services.thumbnail_extractor import (
    detect_platform,
    extract_thumbnail_url,
    extract_video_heading,
)
from ..services.task_queue import QueueConfigurationError, enqueue_ingest_run, enqueue_vector_generation
from ..services.worker_tasks import run_ingest_task, run_vector_task

logger = logging.getLogger(__name__)
_video_downloader = VideoDownloader()

router = APIRouter(prefix="/api", tags=["analysis"])


class AnalyzeFromUrlRequest(BaseModel):
    url: HttpUrl
    project_name: str | None = None


class AnalyzeFromUrlResponse(BaseModel):
    job_id: str
    original_url: str
    project_id: int | None = None


def _extract_cobalt_title(video_url: str) -> str | None:
    try:
        info = _video_downloader.get_info(video_url)
    except Exception as exc:
        logger.warning("Failed to fetch cobalt info for project naming: %s", exc)
        return None

    if not isinstance(info, dict):
        return None

    raw_title = info.get("title")
    if not isinstance(raw_title, str):
        return None

    title = raw_title.strip()
    if not title:
        return None
    if title.lower().startswith("unknown_"):
        return None
    return title


@router.get("/video/preview")
async def get_video_preview(url: str):
    trimmed = (url or "").strip()
    if not trimmed:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        thumbnail_url = extract_thumbnail_url(trimmed)
    except Exception:
        thumbnail_url = None

    try:
        heading = extract_video_heading(trimmed)
    except Exception:
        heading = None

    return {
        "url": trimmed,
        "platform": detect_platform(trimmed),
        "thumbnail_url": thumbnail_url,
        "heading": heading,
    }


@router.post("/analyze-from-url", response_model=AnalyzeFromUrlResponse)
async def analyze_from_url(
    payload: AnalyzeFromUrlRequest,
    db: Session = Depends(get_db),
) -> AnalyzeFromUrlResponse:
    cobalt_title = _extract_cobalt_title(str(payload.url))

    existing_project = db.query(Project).filter(
        Project.video_url == str(payload.url),
        Project.user_id == 1,
    ).first()

    if existing_project and existing_project.status in {"completed", "in_progress"}:
        if cobalt_title and existing_project.name != cobalt_title:
            existing_project.name = cobalt_title
            if existing_project.video_id:
                existing_video = db.query(Video).filter(Video.id == existing_project.video_id).first()
                if existing_video:
                    existing_video.title = cobalt_title
            db.commit()

        # Backfill thumbnail for legacy projects that were created before
        # thumbnail extraction was wired into ingest.
        try:
            thumb = extract_thumbnail_url(str(payload.url))
            if thumb:
                if existing_project.video_id:
                    video = db.query(Video).filter(Video.id == existing_project.video_id).first()
                    if video and not video.thumbnail_url:
                        video.thumbnail_url = thumb
                        db.commit()
                else:
                    video = Video(
                        user_id=existing_project.user_id,
                        title=existing_project.name or "Analyzed Video",
                        description=f"Video analysis for project: {existing_project.name or 'Analyzed Video'}",
                        platform=detect_platform(str(payload.url)),
                        url=str(payload.url),
                        thumbnail_url=thumb,
                        duration_seconds=30,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(video)
                    db.commit()
                    db.refresh(video)
                    existing_project.video_id = video.id
                    db.commit()
        except Exception:
            logger.warning("Thumbnail backfill failed for existing project %s", existing_project.id)

        existing_job = existing_project.job_id or str(uuid.uuid4())
        if existing_project.job_id is None:
            existing_project.job_id = existing_job
            db.commit()
        existing_state = get_pipeline_job(existing_job)
        # Keep pipeline status aligned with persisted project status so frontend
        # polling can deterministically redirect for already-finished projects.
        if existing_project.status == "completed":
            if not existing_state:
                create_pipeline_job(
                    job_id=existing_job,
                    project_id=existing_project.id,
                    job_type="ingest",
                    status="completed",
                    step=5,
                    message="Opening Streamline",
                )
            else:
                update_pipeline_job(
                    job_id=existing_job,
                    status="completed",
                    step=5,
                    message="Opening Streamline",
                    project_id=existing_project.id,
                    error=None,
                )
        elif not existing_state:
            create_pipeline_job(
                job_id=existing_job,
                project_id=existing_project.id,
                job_type="ingest",
                status="running",
                step=0,
                message="Resumed existing project",
            )
        return AnalyzeFromUrlResponse(
            job_id=existing_job,
            original_url=str(payload.url),
            project_id=existing_project.id,
        )

    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, email=None, name=None)
        db.add(user)
        db.commit()
        db.refresh(user)

    job_id = str(uuid.uuid4())
    project_name = cobalt_title or payload.project_name or "Analyzed Video"
    project = Project(
        user_id=1,
        name=project_name,
        video_url=str(payload.url),
        status="in_progress",
        progress=0,
        job_id=job_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    create_pipeline_job(
        job_id=job_id,
        project_id=project.id,
        job_type="ingest",
        status="queued",
        step=0,
        message="Initializing video analysis",
    )

    if settings.TASKS_MODE == "cloud_tasks":
        try:
            enqueue_ingest_run(
                project_id=project.id,
                job_id=job_id,
                video_url=str(payload.url),
                project_name=project_name,
            )
        except QueueConfigurationError as exc:
            logger.warning(
                "Cloud Tasks unavailable for ingest project %s; falling back to local thread: %s",
                project.id,
                exc,
            )
            Thread(
                target=run_ingest_task,
                kwargs={
                    "project_id": project.id,
                    "job_id": job_id,
                    "video_url": str(payload.url),
                    "project_name": project_name,
                },
                daemon=True,
            ).start()
        except Exception as exc:
            logger.exception("Failed to enqueue ingest task for project %s", project.id)
            project.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to enqueue ingest task: {exc}")
    else:
        Thread(
            target=run_ingest_task,
            kwargs={
                "project_id": project.id,
                "job_id": job_id,
                "video_url": str(payload.url),
                "project_name": project_name,
            },
            daemon=True,
        ).start()

    return AnalyzeFromUrlResponse(
        job_id=job_id,
        original_url=str(payload.url),
        project_id=project.id,
    )


@router.get("/analysis/progress/{job_id}")
async def get_analysis_progress(job_id: str):
    state = get_pipeline_job(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": state.job_id,
        "status": state.status,
        "step": state.step,
        "text": state.message,
        "project_id": state.project_id,
        "error": state.error,
    }


@router.get("/video/check-duplicate")
async def check_video_duplicate(
    url: str,
    db: Session = Depends(get_db),
):
    existing_project = db.query(Project).filter(
        Project.video_url == url,
        Project.user_id == 1,
    ).first()

    if existing_project:
        return {
            "exists": True,
            "project_id": existing_project.id,
            "status": existing_project.status,
            "project_name": existing_project.name,
        }

    return {
        "exists": False,
        "project_id": None,
        "status": None,
        "project_name": None,
    }


@router.get("/analysis/status/{job_id}")
async def get_analysis_status(job_id: str):
    return await get_analysis_progress(job_id)


@router.get("/analysis/results/{job_id}")
async def get_analysis_results(job_id: str) -> str:
    raise HTTPException(
        status_code=410,
        detail="Interval-based analysis output has been removed. Use the project overview endpoint instead.",
    )


@router.get("/projects/{project_id}/vector-status")
async def get_vector_generation_status(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project_id,
        "status": project.vector_generation_status or "not_started",
        "started_at": (
            project.vector_generation_started_at.isoformat()
            if project.vector_generation_started_at
            else None
        ),
        "completed_at": (
            project.vector_generation_completed_at.isoformat()
            if project.vector_generation_completed_at
            else None
        ),
        "error": project.vector_generation_error,
    }


@router.post("/projects/{project_id}/generate-vector-data")
async def trigger_vector_data_generation(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    current_status = project.vector_generation_status or "not_started"
    if current_status in {"pending"}:
        return {
            "project_id": project_id,
            "triggered": False,
            "status": current_status,
            "message": "Vector generation is already in progress.",
        }
    if current_status == "completed":
        return {
            "project_id": project_id,
            "triggered": False,
            "status": current_status,
            "message": "Vector data has already been generated for this project.",
        }

    project.vector_generation_status = "pending"
    project.vector_generation_started_at = datetime.utcnow()
    project.vector_generation_error = None
    db.commit()

    if settings.TASKS_MODE == "cloud_tasks":
        try:
            enqueue_vector_generation(project_id=project_id)
        except QueueConfigurationError as exc:
            logger.warning(
                "Cloud Tasks unavailable for vector project %s; falling back to local thread: %s",
                project_id,
                exc,
            )
            Thread(target=run_vector_task, kwargs={"project_id": project_id}, daemon=True).start()
        except Exception as exc:
            logger.exception("Failed to enqueue vector task for project %s", project_id)
            raise HTTPException(status_code=500, detail=f"Failed to enqueue vector task: {exc}")
    else:
        Thread(target=run_vector_task, kwargs={"project_id": project_id}, daemon=True).start()

    return {
        "project_id": project_id,
        "triggered": True,
        "status": "pending",
        "message": "Vector data generation started in background.",
    }
