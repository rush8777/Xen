from __future__ import annotations

from typing import Optional
from datetime import date
from datetime import datetime
import concurrent.futures

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import (
    AnalysisInterval,
    AnalysisRecord,
    AnalysisRun,
    PipelineJob,
    PipelineJobEvent,
    PremiumIntervalAnalysis,
    PremiumPerformanceInterval,
    PremiumPsychologicalInterval,
    PremiumStructuralInterval,
    PremiumTranscriptInterval,
    PremiumVerificationInterval,
    Project,
    ProjectContentFeatures,
    ProjectOverview,
    ProjectPremiumAnalysis,
    ProjectPsychologyAnalysis,
    ProjectStatistics,
    User,
    Video,
)
from ..services.thumbnail_extractor import detect_platform, extract_thumbnail_url


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
    thumbnail_url: Optional[str] = None
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


class EnsureThumbnailResponse(BaseModel):
    project_id: int
    thumbnail_url: Optional[str] = None
    source: str


def _extract_thumbnail_with_timeout(url: str, timeout_seconds: float = 8.0) -> Optional[str]:
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(extract_thumbnail_url, url)
            return future.result(timeout=timeout_seconds)
    except Exception:
        return None


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
        thumbnail_url=db_project.video.thumbnail_url if db_project.video else None,
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
            thumbnail_url=p.video.thumbnail_url if p.video else None,
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
        thumbnail_url=project.video.thumbnail_url if project.video else None,
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
        thumbnail_url=project.video.thumbnail_url if project.video else None,
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


@router.delete("/{project_id}", status_code=200)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> dict:
    """Delete project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    pipeline_job_ids = [
        row[0]
        for row in db.query(PipelineJob.job_id)
        .filter(PipelineJob.project_id == project_id)
        .all()
    ]
    if pipeline_job_ids:
        db.query(PipelineJobEvent).filter(
            PipelineJobEvent.job_id.in_(pipeline_job_ids)
        ).delete(synchronize_session=False)

    db.query(PipelineJob).filter(PipelineJob.project_id == project_id).delete(
        synchronize_session=False
    )

    # Delete project-scoped records that are not configured with DB-level ON DELETE CASCADE.
    db.query(ProjectStatistics).filter(ProjectStatistics.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectPsychologyAnalysis).filter(ProjectPsychologyAnalysis.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectContentFeatures).filter(ProjectContentFeatures.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectOverview).filter(ProjectOverview.project_id == project_id).delete(synchronize_session=False)
    db.query(ProjectPremiumAnalysis).filter(ProjectPremiumAnalysis.project_id == project_id).delete(synchronize_session=False)
    db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).delete(synchronize_session=False)
    db.query(PremiumIntervalAnalysis).filter(PremiumIntervalAnalysis.project_id == project_id).delete(synchronize_session=False)

    premium_structural_rows = (
        db.query(PremiumStructuralInterval)
        .filter(PremiumStructuralInterval.project_id == project_id)
        .all()
    )
    for row in premium_structural_rows:
        db.delete(row)

    premium_psychological_rows = (
        db.query(PremiumPsychologicalInterval)
        .filter(PremiumPsychologicalInterval.project_id == project_id)
        .all()
    )
    for row in premium_psychological_rows:
        db.delete(row)

    premium_performance_rows = (
        db.query(PremiumPerformanceInterval)
        .filter(PremiumPerformanceInterval.project_id == project_id)
        .all()
    )
    for row in premium_performance_rows:
        db.delete(row)

    premium_transcript_rows = (
        db.query(PremiumTranscriptInterval)
        .filter(PremiumTranscriptInterval.project_id == project_id)
        .all()
    )
    for row in premium_transcript_rows:
        db.delete(row)

    premium_verification_rows = (
        db.query(PremiumVerificationInterval)
        .filter(PremiumVerificationInterval.project_id == project_id)
        .all()
    )
    for row in premium_verification_rows:
        db.delete(row)

    analysis_records = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.project_id == project_id)
        .all()
    )
    for row in analysis_records:
        db.delete(row)

    analysis_child_intervals = (
        db.query(AnalysisInterval)
        .filter(
            AnalysisInterval.project_id == project_id,
            AnalysisInterval.parent_interval_id.is_not(None),
        )
        .all()
    )
    for row in analysis_child_intervals:
        db.delete(row)

    analysis_parent_intervals = (
        db.query(AnalysisInterval)
        .filter(
            AnalysisInterval.project_id == project_id,
            AnalysisInterval.parent_interval_id.is_(None),
        )
        .all()
    )
    for row in analysis_parent_intervals:
        db.delete(row)

    db.delete(project)
    db.commit()

    return {"status": "ok"}


@router.post("/{project_id}/thumbnail/ensure", response_model=EnsureThumbnailResponse)
def ensure_project_thumbnail(project_id: int, db: Session = Depends(get_db)) -> EnsureThumbnailResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    video = project.video
    if video and video.thumbnail_url:
        return EnsureThumbnailResponse(
            project_id=project.id,
            thumbnail_url=video.thumbnail_url,
            source="cached",
        )

    if not project.video_url:
        return EnsureThumbnailResponse(
            project_id=project.id,
            thumbnail_url=None,
            source="missing_video_url",
        )

    thumbnail_url = _extract_thumbnail_with_timeout(project.video_url, timeout_seconds=8.0)
    if not thumbnail_url:
        return EnsureThumbnailResponse(
            project_id=project.id,
            thumbnail_url=None,
            source="extraction_failed",
        )

    if video:
        if not video.thumbnail_url:
            video.thumbnail_url = thumbnail_url
            db.commit()
        return EnsureThumbnailResponse(
            project_id=project.id,
            thumbnail_url=video.thumbnail_url,
            source="extracted",
        )

    video = Video(
        user_id=project.user_id,
        title=project.name or "Analyzed Video",
        description=f"Video analysis for project: {project.name or 'Analyzed Video'}",
        platform=detect_platform(project.video_url),
        url=project.video_url,
        thumbnail_url=thumbnail_url,
        duration_seconds=project.video_duration_seconds or 30,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    project.video_id = video.id
    db.commit()

    return EnsureThumbnailResponse(
        project_id=project.id,
        thumbnail_url=thumbnail_url,
        source="created_video_and_extracted",
    )


