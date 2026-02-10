from __future__ import annotations

from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Project, User


router = APIRouter(prefix="/api/projects", tags=["projects"])


# Pydantic schemas
class ProjectCreate(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    video_id: Optional[int] = None
    priority: Optional[str] = None  # Video, Image, Post
    progress: int = 0
    status: str = "draft"
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    video_id: Optional[int] = None
    priority: Optional[str] = None
    progress: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    name: str
    category: Optional[str]
    description: Optional[str]
    video_url: Optional[str]
    video_id: Optional[int]
    priority: Optional[str]
    progress: int
    status: str
    job_id: Optional[str]
    analysis_file_path: Optional[str]
    gemini_file_uri: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    user_id: int = Query(1, description="User ID (temporary, will use auth later)")
) -> ProjectResponse:
    """Create a new project"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_project = Project(
        user_id=user_id,
        name=project.name,
        category=project.category,
        description=project.description,
        video_url=project.video_url,
        video_id=project.video_id,
        priority=project.priority,
        progress=project.progress,
        status=project.status,
        start_date=project.start_date,
        end_date=project.end_date,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return ProjectResponse(
        id=db_project.id,
        user_id=db_project.user_id,
        name=db_project.name,
        category=db_project.category,
        description=db_project.description,
        video_url=db_project.video_url,
        video_id=db_project.video_id,
        priority=db_project.priority,
        progress=db_project.progress,
        status=db_project.status,
        job_id=db_project.job_id,
        analysis_file_path=db_project.analysis_file_path,
        gemini_file_uri=db_project.gemini_file_uri,
        start_date=db_project.start_date,
        end_date=db_project.end_date,
        created_at=db_project.created_at.isoformat(),
        updated_at=db_project.updated_at.isoformat(),
    )


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[ProjectResponse]:
    """List projects with optional filtering"""
    query = db.query(Project)

    if user_id:
        query = query.filter(Project.user_id == user_id)
    if category:
        query = query.filter(Project.category == category)
    if status:
        query = query.filter(Project.status == status)

    projects = query.offset(skip).limit(limit).all()

    return [
        ProjectResponse(
            id=p.id,
            user_id=p.user_id,
            name=p.name,
            category=p.category,
            description=p.description,
            video_url=p.video_url,
            video_id=p.video_id,
            priority=p.priority,
            progress=p.progress,
            status=p.status,
            job_id=p.job_id,
            analysis_file_path=p.analysis_file_path,
            gemini_file_uri=p.gemini_file_uri,
            start_date=p.start_date,
            end_date=p.end_date,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectResponse:
    """Get project details"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        category=project.category,
        description=project.description,
        video_url=project.video_url,
        video_id=project.video_id,
        priority=project.priority,
        progress=project.progress,
        status=project.status,
        job_id=project.job_id,
        analysis_file_path=project.analysis_file_path,
        gemini_file_uri=project.gemini_file_uri,
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Update project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update only provided fields
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        category=project.category,
        description=project.description,
        video_url=project.video_url,
        video_id=project.video_id,
        priority=project.priority,
        progress=project.progress,
        status=project.status,
        job_id=project.job_id,
        analysis_file_path=project.analysis_file_path,
        gemini_file_uri=project.gemini_file_uri,
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    """Delete project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()


