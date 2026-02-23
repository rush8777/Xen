from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Project, ProjectPremiumAnalysis
from ..services.premium_analysis_service import generate_premium_analysis_for_project

router = APIRouter(prefix="/api/projects", tags=["premium-analysis"])


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

    # Launch background task
    asyncio.create_task(generate_premium_analysis_for_project(project_id))

    project.premium_analysis_status = "pending"
    project.premium_analysis_started_at = datetime.utcnow()
    project.premium_analysis_error = None
    db.commit()

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
