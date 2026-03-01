from __future__ import annotations

from datetime import datetime
import logging
from threading import Thread

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_db
from ..models import Project, ProjectPremiumAnalysis
from ..services.task_queue import QueueConfigurationError, enqueue_premium_generation
from ..services.worker_tasks import run_premium_task

router = APIRouter(prefix="/api/projects", tags=["premium-analysis"])
logger = logging.getLogger(__name__)


class PremiumAnalysisStatusResponse(BaseModel):
    project_id: int
    status: str
    started_at: str | None
    completed_at: str | None
    error: str | None


class PremiumAnalysisResponse(BaseModel):
    project_id: int
    pass_1_output: str
    pass_2_output: str
    pass_3_output: str
    pass_4_output: str
    pass_5_output: str
    generated_at: str | None
    version: int
    status: str


@router.get("/{project_id}/premium-analysis-status", response_model=PremiumAnalysisStatusResponse)
def get_premium_analysis_status(
    project_id: int,
    db: Session = Depends(get_db),
) -> PremiumAnalysisStatusResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return PremiumAnalysisStatusResponse(
        project_id=project_id,
        status=project.premium_analysis_status or "not_started",
        started_at=(
            project.premium_analysis_started_at.isoformat()
            if project.premium_analysis_started_at
            else None
        ),
        completed_at=(
            project.premium_analysis_completed_at.isoformat()
            if project.premium_analysis_completed_at
            else None
        ),
        error=project.premium_analysis_error,
    )


@router.post("/{project_id}/trigger-premium-analysis")
def trigger_premium_analysis(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if (project.vector_generation_status or "not_started") != "completed":
        raise HTTPException(
            status_code=400,
            detail="Vector data must be completed before premium analysis.",
        )

    current_status = project.premium_analysis_status or "not_started"
    if current_status in ("pending",):
        return {
            "project_id": project_id,
            "triggered": False,
            "status": current_status,
            "message": "Premium analysis is already in progress.",
        }

    if current_status == "completed":
        return {
            "project_id": project_id,
            "triggered": False,
            "status": current_status,
            "message": "Premium analysis has already been completed for this project.",
        }

    project.premium_analysis_status = "pending"
    project.premium_analysis_started_at = datetime.utcnow()
    project.premium_analysis_error = None
    db.commit()

    if settings.TASKS_MODE == "cloud_tasks":
        try:
            enqueue_premium_generation(project_id=project_id)
        except QueueConfigurationError as exc:
            logger.warning(
                "Cloud Tasks unavailable for premium project %s; falling back to local thread: %s",
                project_id,
                exc,
            )
            Thread(target=run_premium_task, kwargs={"project_id": project_id}, daemon=True).start()
        except Exception as exc:
            logger.exception("Failed to enqueue premium task for project %s", project_id)
            raise HTTPException(status_code=500, detail=f"Failed to enqueue premium task: {exc}")
    else:
        Thread(target=run_premium_task, kwargs={"project_id": project_id}, daemon=True).start()

    return {
        "project_id": project_id,
        "triggered": True,
        "status": "pending",
        "message": "Premium analysis started in background.",
    }


@router.get("/{project_id}/premium-analysis", response_model=PremiumAnalysisResponse)
def get_premium_analysis(
    project_id: int,
    db: Session = Depends(get_db),
) -> PremiumAnalysisResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    analysis = (
        db.query(ProjectPremiumAnalysis)
        .filter(ProjectPremiumAnalysis.project_id == project_id)
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=404, detail="Premium analysis not found. Try generating it first."
        )

    if analysis.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Premium analysis not ready. Current status: {analysis.status}",
        )

    return PremiumAnalysisResponse(
        project_id=project_id,
        pass_1_output=analysis.pass_1_output or "",
        pass_2_output=analysis.pass_2_output or "",
        pass_3_output=analysis.pass_3_output or "",
        pass_4_output=analysis.pass_4_output or "",
        pass_5_output=analysis.pass_5_output or "",
        generated_at=analysis.generated_at.isoformat() if analysis.generated_at else None,
        version=analysis.version,
        status=analysis.status,
    )
