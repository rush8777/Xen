from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Project, ProjectOverview


router = APIRouter(prefix="/api/projects", tags=["project-overview"])


class ProjectOverviewStatusResponse(BaseModel):
    project_id: int
    status: str
    generated_at: str | None
    version: int | None
    error: str | None


class ProjectOverviewResponse(BaseModel):
    project_id: int
    blog_markdown: str
    summary: str
    insights: dict
    generated_at: str | None
    version: int
    status: str


class ProjectOverviewUpdate(BaseModel):
    blog_markdown: str


@router.get("/{project_id}/overview", response_model=ProjectOverviewResponse)
def get_project_overview(project_id: int, db: Session = Depends(get_db)) -> ProjectOverviewResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    overview = (
        db.query(ProjectOverview)
        .filter(ProjectOverview.project_id == project_id)
        .first()
    )

    if not overview:
        return ProjectOverviewResponse(
            project_id=project_id,
            blog_markdown="",
            summary="",
            insights={},
            generated_at=None,
            version=1,
            status="not_started",
        )

    try:
        insights = json.loads(overview.insights_json or "{}")
    except Exception:
        insights = {}

    return ProjectOverviewResponse(
        project_id=project_id,
        blog_markdown=overview.blog_markdown or "",
        summary=overview.summary or "",
        insights=insights,
        generated_at=overview.generated_at.isoformat() if overview.generated_at else None,
        version=overview.version,
        status=overview.status,
    )


@router.patch("/{project_id}/overview", response_model=ProjectOverviewResponse)
def update_project_overview(
    project_id: int,
    payload: ProjectOverviewUpdate,
    db: Session = Depends(get_db),
) -> ProjectOverviewResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    overview = (
        db.query(ProjectOverview)
        .filter(ProjectOverview.project_id == project_id)
        .first()
    )

    if not overview:
        overview = ProjectOverview(
            project_id=project_id,
            blog_markdown="",
            summary="",
            insights_json="{}",
            status="not_started",
        )
        db.add(overview)
        db.commit()
        db.refresh(overview)

    overview.blog_markdown = payload.blog_markdown
    overview.version = int(overview.version or 1) + 1
    overview.updated_at = datetime.utcnow()

    if overview.status == "not_started":
        overview.status = "completed"

    db.commit()
    db.refresh(overview)

    try:
        insights = json.loads(overview.insights_json or "{}")
    except Exception:
        insights = {}

    return ProjectOverviewResponse(
        project_id=project_id,
        blog_markdown=overview.blog_markdown or "",
        summary=overview.summary or "",
        insights=insights,
        generated_at=overview.generated_at.isoformat() if overview.generated_at else None,
        version=overview.version,
        status=overview.status,
    )
