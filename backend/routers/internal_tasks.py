from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from ..config import settings
from ..database import SessionLocal
from ..models import AnalysisRun
from ..services.statistics_tasks import execute_statistics_generation
from ..services.worker_tasks import (
    run_content_features_task,
    run_ingest_task,
    run_overview_task,
    run_psychology_task,
    run_premium_task,
    run_vector_task,
)

router = APIRouter(prefix="/internal/tasks", tags=["internal-tasks"])


class StatisticsTaskPayload(BaseModel):
    project_id: int
    run_id: int | None = None
    request_id: str | None = None
    requested_at: str | None = None


class PsychologyTaskPayload(BaseModel):
    project_id: int
    run_id: int | None = None
    interval_seconds: int = 5
    request_id: str | None = None
    requested_at: str | None = None


class IngestTaskPayload(BaseModel):
    project_id: int
    job_id: str
    video_url: str
    project_name: str | None = None
    request_id: str | None = None
    requested_at: str | None = None


class ProjectTaskPayload(BaseModel):
    project_id: int
    request_id: str | None = None
    requested_at: str | None = None


class ContentFeaturesTaskPayload(BaseModel):
    project_id: int
    feature_id: str | None = None
    force: bool = False
    request_id: str | None = None
    requested_at: str | None = None


def _verify_internal_auth(
    authorization: str | None,
    worker_secret: str | None,
) -> None:
    mode = settings.WORKER_AUTH_MODE
    if mode == "none":
        return

    if mode == "shared_secret":
        expected = settings.WORKER_SHARED_SECRET or ""
        if not expected or worker_secret != expected:
            raise HTTPException(status_code=401, detail="Invalid worker shared secret")
        return

    if mode == "oidc":
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")
        token = authorization.split(" ", 1)[1].strip()
        audience = settings.WORKER_AUDIENCE or settings.WORKER_BASE_URL
        if not audience:
            raise HTTPException(status_code=500, detail="Worker audience is not configured")
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token

            id_token.verify_oauth2_token(token, google_requests.Request(), audience)
        except Exception as exc:
            raise HTTPException(status_code=401, detail=f"Invalid OIDC token: {exc}")
        return

    raise HTTPException(status_code=500, detail=f"Unsupported WORKER_AUTH_MODE: {mode}")


def _is_run_terminal(run_id: int | None) -> bool:
    if not run_id:
        return False
    db = SessionLocal()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not run:
            return False
        return run.status in {"completed", "failed"}
    finally:
        db.close()


@router.post("/ingest-run")
def run_ingest(
    payload: IngestTaskPayload,
    authorization: str | None = Header(default=None, alias="Authorization"),
    worker_secret: str | None = Header(default=None, alias="X-Worker-Secret"),
) -> dict:
    _verify_internal_auth(authorization=authorization, worker_secret=worker_secret)
    run_ingest_task(
        project_id=payload.project_id,
        job_id=payload.job_id,
        video_url=payload.video_url,
        project_name=payload.project_name,
    )
    return {
        "status": "ok",
        "task": "ingest",
        "project_id": payload.project_id,
        "job_id": payload.job_id,
        "request_id": payload.request_id,
    }


@router.post("/statistics-generate")
def run_statistics_task(
    payload: StatisticsTaskPayload,
    authorization: str | None = Header(default=None, alias="Authorization"),
    worker_secret: str | None = Header(default=None, alias="X-Worker-Secret"),
) -> dict:
    _verify_internal_auth(authorization=authorization, worker_secret=worker_secret)
    if _is_run_terminal(payload.run_id):
        return {
            "status": "ok",
            "task": "statistics",
            "project_id": payload.project_id,
            "run_id": payload.run_id,
            "request_id": payload.request_id,
            "skipped": True,
        }
    execute_statistics_generation(project_id=payload.project_id, run_id=payload.run_id)
    return {
        "status": "ok",
        "task": "statistics",
        "project_id": payload.project_id,
        "run_id": payload.run_id,
        "request_id": payload.request_id,
    }


@router.post("/vector-generate")
def run_vector_generation(
    payload: ProjectTaskPayload,
    authorization: str | None = Header(default=None, alias="Authorization"),
    worker_secret: str | None = Header(default=None, alias="X-Worker-Secret"),
) -> dict:
    _verify_internal_auth(authorization=authorization, worker_secret=worker_secret)
    run_vector_task(project_id=payload.project_id)
    return {
        "status": "ok",
        "task": "vector",
        "project_id": payload.project_id,
        "request_id": payload.request_id,
    }


@router.post("/overview-generate")
def run_overview_generation(
    payload: ProjectTaskPayload,
    authorization: str | None = Header(default=None, alias="Authorization"),
    worker_secret: str | None = Header(default=None, alias="X-Worker-Secret"),
) -> dict:
    _verify_internal_auth(authorization=authorization, worker_secret=worker_secret)
    run_overview_task(project_id=payload.project_id)
    return {
        "status": "ok",
        "task": "overview",
        "project_id": payload.project_id,
        "request_id": payload.request_id,
    }


@router.post("/premium-generate")
def run_premium_generation(
    payload: ProjectTaskPayload,
    authorization: str | None = Header(default=None, alias="Authorization"),
    worker_secret: str | None = Header(default=None, alias="X-Worker-Secret"),
) -> dict:
    _verify_internal_auth(authorization=authorization, worker_secret=worker_secret)
    run_premium_task(project_id=payload.project_id)
    return {
        "status": "ok",
        "task": "premium",
        "project_id": payload.project_id,
        "request_id": payload.request_id,
    }


@router.post("/psychology-generate")
def run_psychology_generation(
    payload: PsychologyTaskPayload,
    authorization: str | None = Header(default=None, alias="Authorization"),
    worker_secret: str | None = Header(default=None, alias="X-Worker-Secret"),
) -> dict:
    _verify_internal_auth(authorization=authorization, worker_secret=worker_secret)
    if _is_run_terminal(payload.run_id):
        return {
            "status": "ok",
            "task": "psychology",
            "project_id": payload.project_id,
            "run_id": payload.run_id,
            "request_id": payload.request_id,
            "skipped": True,
        }
    run_psychology_task(
        project_id=payload.project_id,
        run_id=payload.run_id,
        interval_seconds=payload.interval_seconds,
    )
    return {
        "status": "ok",
        "task": "psychology",
        "project_id": payload.project_id,
        "run_id": payload.run_id,
        "request_id": payload.request_id,
    }


@router.post("/content-features-generate")
def run_content_features_generation(
    payload: ContentFeaturesTaskPayload,
    authorization: str | None = Header(default=None, alias="Authorization"),
    worker_secret: str | None = Header(default=None, alias="X-Worker-Secret"),
) -> dict:
    _verify_internal_auth(authorization=authorization, worker_secret=worker_secret)
    run_content_features_task(
        project_id=payload.project_id,
        feature_id=payload.feature_id,
        force=payload.force,
    )
    return {
        "status": "ok",
        "task": "content_features",
        "project_id": payload.project_id,
        "feature_id": payload.feature_id,
        "request_id": payload.request_id,
    }
