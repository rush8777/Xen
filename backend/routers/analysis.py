from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
import uuid
import asyncio
from datetime import datetime
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

# Import the yt-dlp downloader directly
from .video_downloader import VideoDownloader

# Import comments extractor
from ..extractor.comments_extractor import CommentsExtractor

# Import database dependencies and models
from ..dependencies import get_db
from ..models import Project, User, ProjectStatistics, ProjectOverview, Video
from ..services.vector_data_generator import generate_vector_data_for_project
from ..gemini_backend.config import GEMINI_API_KEY
from ..services.project_overview_generator import ProjectOverviewGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


class AnalyzeFromUrlRequest(BaseModel):
    url: HttpUrl
    project_name: str | None = None


class AnalyzeFromUrlResponse(BaseModel):
    job_id: str
    original_url: str
    project_id: int | None = None


# Initialize the video downloader, analyzer, and comments extractor
video_downloader = VideoDownloader()
comments_extractor = CommentsExtractor()

overview_generator = ProjectOverviewGenerator(api_key=GEMINI_API_KEY)


@dataclass
class ProgressState:
    status: str  # queued | running | completed | failed
    step: int
    text: str
    project_id: int | None = None
    error: str | None = None


# NOTE: In-memory progress tracking (sufficient for local/dev and single-process deploys).
# If you scale to multiple workers/instances, move this to Redis / DB.
ANALYSIS_PROGRESS: dict[str, ProgressState] = {}


def _set_progress(job_id: str, *, status: str | None = None, step: int | None = None, text: str | None = None,
                  project_id: int | None = None, error: str | None = None) -> None:
    current = ANALYSIS_PROGRESS.get(job_id)
    if not current:
        current = ProgressState(status="queued", step=0, text="Queued")
        ANALYSIS_PROGRESS[job_id] = current
    if status is not None:
        current.status = status
    if step is not None:
        current.step = step
    if text is not None:
        current.text = text
    if project_id is not None:
        current.project_id = project_id
    if error is not None:
        current.error = error


async def _generate_overview_sync(project_id: int) -> None:
    """Generate project overview (blog markdown + summary + insights) in background task (sync)."""
    from ..database import SessionLocal

    db2 = SessionLocal()
    try:
        project = db2.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project {project_id} not found for overview generation")
            return

        overview = (
            db2.query(ProjectOverview)
            .filter(ProjectOverview.project_id == project_id)
            .first()
        )
        if not overview:
            overview = ProjectOverview(project_id=project_id, blog_markdown="", summary="", insights_json="{}", status="pending")
            db2.add(overview)
            db2.commit()
            db2.refresh(overview)
        else:
            overview.status = "pending"
            overview.error = None
            db2.commit()

        try:
            overview_data = await overview_generator.generate_overview(
                analysis_file_path=project.analysis_file_path or "",
                video_url=project.video_url or "",
                project_name=project.name,
                project_id=project.id,
                job_id=project.job_id,
                cached_content_name=project.gemini_cached_content_name,
                video_duration_seconds=project.video_duration_seconds,
            )

            blog = overview_data.get("blog") if isinstance(overview_data, dict) else None
            blog_markdown = ""
            if isinstance(blog, dict):
                blog_markdown = str(blog.get("markdown") or "")

            summary = str(overview_data.get("summary") or "")
            insights = overview_data.get("insights")
            if not isinstance(insights, dict):
                insights = {}

            import json as _json
            from datetime import datetime as _dt

            overview.blog_markdown = blog_markdown
            overview.summary = summary
            overview.insights_json = _json.dumps(insights)
            overview.status = "completed"
            overview.generated_at = _dt.utcnow()
            overview.error = None
            db2.commit()
            logger.info(f"Overview generation completed for project {project_id}")
        except Exception as e:
            logger.error(f"Overview generation failed for project {project_id}: {e}")
            overview.status = "failed"
            overview.error = str(e)
            db2.commit()
    finally:
        db2.close()


@router.post("/analyze-from-url", response_model=AnalyzeFromUrlResponse)
async def analyze_from_url(
    payload: AnalyzeFromUrlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnalyzeFromUrlResponse:
    """Start analysis pipeline and return a job_id immediately.

    The frontend can poll `/api/analysis/progress/{job_id}` to drive the loader
    based on real backend stages.
    """
    
    # Check for duplicate video URL
    existing_project = db.query(Project).filter(
        Project.video_url == str(payload.url),
        Project.user_id == 1  # Assuming single user for now
    ).first()
    
    if existing_project:
        # If analysis is completed or still in progress, return existing project
        if existing_project.status in ["completed", "in_progress"]:
            return AnalyzeFromUrlResponse(
                job_id=existing_project.job_id or str(uuid.uuid4()),
                original_url=str(payload.url),
                project_id=existing_project.id,
            )
        # If analysis failed, allow retry by continuing to new analysis

    job_id = str(uuid.uuid4())
    _set_progress(job_id, status="queued", step=0, text="Initializing video analysis")

    async def _run_pipeline(job_id_: str, url: str, project_name: str | None) -> None:
        from ..database import SessionLocal

        db2 = SessionLocal()
        tmp_file: Path | None = None

        try:
            _set_progress(job_id_, status="running", step=0, text="Initializing video analysis")

            # 1) Download video
            _set_progress(job_id_, step=1, text="Downloading video")
            tmp_dir = Path(tempfile.gettempdir())
            tmp_filename = f"v0social_{os.getpid()}_{os.urandom(4).hex()}"
            original_download_dir = video_downloader.download_dir
            video_downloader.download_dir = tmp_dir
            try:
                downloaded_file = video_downloader.download(
                    url=url,
                    quality="720p",
                    audio_only=False,
                    output_filename=tmp_filename,
                )
                tmp_file = Path(downloaded_file)
                if not tmp_file.exists():
                    raise Exception(f"Downloaded file not found at {tmp_file}")
            finally:
                video_downloader.download_dir = original_download_dir

            # 2) Extract comments
            _set_progress(job_id_, step=2, text="Extracting comments")
            comments_data = None
            try:
                comments_data = comments_extractor.extract_comments(
                    url=url,
                    max_comments=100,
                    include_replies=True,
                )
            except Exception as e:
                logger.warning(f"Comments extraction failed (non-critical): {e}")
                comments_data = None

            # 3) Upload video directly for cached content without interval analysis
            _set_progress(job_id_, step=3, text="Uploading video for overview generation")
            from ..gemini_backend.gemini_client import upload_video_to_gemini
            
            try:
                cached_content_name = await upload_video_to_gemini(tmp_file)
                video_duration_seconds = 30  # Default duration, will be updated if available
                output_path = None  # No interval analysis output
                gemini_file_uri = None
                analyzer_job_id = None
            except Exception as e:
                logger.error(f"Video upload failed: {e}")
                cached_content_name = None
                video_duration_seconds = None
                output_path = None
                gemini_file_uri = None
                analyzer_job_id = None

            # 4) Append comments - COMMENTED OUT since no interval analysis output file
            # try:
            #     with open(output_path, "a", encoding="utf-8") as f:
            #         f.write("\n" + "=" * 80 + "\n")
            #         f.write("VIDEO COMMENTS\n")
            #         f.write("=" * 80 + "\n\n")
            #         if comments_data and comments_data.get("comments_count", 0) > 0:
            #             f.write(f"Total Comments: {comments_data['comments_count']}\n")
            #             f.write(f"Video Title: {comments_data['video_info']['title']}\n")
            #             f.write(f"Video URL: {url}\n\n")
            #             for comment in comments_data["comments"]:
            #                 f.write(f"Author: {comment['author']}\n")
            #                 f.write(f"Likes: {comment['like_count']}\n")
            #                 if comment["is_reply"]:
            #                     f.write("[REPLY]\n")
            #                 f.write(f"Text: {comment['text']}\n")
            #                 f.write("-" * 80 + "\n")
            #         else:
            #             f.write("No comments found\n")
            #             f.write(f"Video URL: {url}\n")
            # except Exception as e:
            #     logger.warning(f"Failed to append comments to file (non-critical): {e}")

            project_id: int | None = None
            if project_name:
                _set_progress(job_id_, step=4, text="Creating project")

                # Create or get user
                user = db2.query(User).filter(User.id == 1).first()
                if not user:
                    user = User(id=1, email=None, name=None)
                    db2.add(user)
                    db2.commit()
                    db2.refresh(user)

                # Create video record first
                # Extract basic video info from URL and available data
                video_title = project_name or "Analyzed Video"
                platform = "youtube"  # Default, could be enhanced to detect from URL

                video = Video(
                    user_id=1,
                    title=video_title,
                    description=f"Video analysis for project: {project_name}",
                    platform=platform,
                    url=url,
                    duration_seconds=video_duration_seconds,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db2.add(video)
                db2.commit()
                db2.refresh(video)
                video_id = video.id

                project = Project(
                    user_id=1,
                    name=project_name,
                    video_url=url,
                    video_id=video_id,  # Link to the created video
                    job_id=analyzer_job_id,
                    analysis_file_path=str(output_path),
                    gemini_file_uri=gemini_file_uri,
                    gemini_cached_content_name=cached_content_name,
                    video_duration_seconds=video_duration_seconds,
                    status="in_progress",
                    progress=0,
                )
                db2.add(project)
                db2.commit()
                db2.refresh(project)
                project_id = project.id

                # overview generation
                try:
                    await _generate_overview_sync(project_id)
                except Exception as e:
                    logger.warning(f"Overview generation failed (non-critical): {e}")

                # Trigger vector data generation in background
                try:
                    asyncio.create_task(generate_vector_data_for_project(project_id))
                    logger.info(f"Vector data generation triggered for project {project_id}")
                except Exception as e:
                    logger.warning(f"Vector data generation trigger failed (non-critical): {e}")

            _set_progress(job_id_, status="completed", step=5, text="Opening Streamline", project_id=project_id)
        except Exception as e:
            logger.error(f"Pipeline failed for job {job_id_}: {e}")
            _set_progress(job_id_, status="failed", error=str(e))
        finally:
            try:
                db2.close()
            except Exception:
                pass

    asyncio.create_task(_run_pipeline(job_id, str(payload.url), payload.project_name))

    return AnalyzeFromUrlResponse(
        job_id=job_id,
        original_url=str(payload.url),
        project_id=None,
    )


@router.get("/analysis/progress/{job_id}")
async def get_analysis_progress(job_id: str):
    state = ANALYSIS_PROGRESS.get(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": state.status,
        "step": state.step,
        "text": state.text,
        "project_id": state.project_id,
        "error": state.error,
    }


@router.get("/video/check-duplicate")
async def check_video_duplicate(
    url: str,
    db: Session = Depends(get_db),
):
    """
    Check if a video URL has already been analyzed.
    
    Returns:
        {
            "exists": bool,
            "project_id": int | null,
            "status": str | null,
            "project_name": str | null
        }
    """
    existing_project = db.query(Project).filter(
        Project.video_url == url,
        Project.user_id == 1  # Assuming single user for now
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
    """
    Back-compat endpoint.

    Interval-based analysis jobs are no longer produced. Use the progress endpoint.
    """
    return await get_analysis_progress(job_id)


@router.get(
    "/analysis/results/{job_id}",
)
async def get_analysis_results(job_id: str) -> str:
    """
    Interval-based analysis results are no longer generated.
    """
    raise HTTPException(
        status_code=410,
        detail="Interval-based analysis output has been removed. Use the project overview endpoint instead.",
    )


# ---------------------------------------------------------------------------
# Vector generation endpoints
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/vector-status")
async def get_vector_generation_status(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Check the vector data generation status for a project.

    Returns:
        {
            "project_id": int,
            "status": "not_started" | "pending" | "completed" | "failed",
            "started_at": str | null,
            "completed_at": str | null,
            "error": str | null
        }
    """
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
    """
    Manually trigger background vector data generation for a project.

    Idempotent: if status is already 'pending' or 'completed', it will not
    re-trigger unless forced. Returns the current status.

    To force regeneration even on 'completed', append ?force=true.
    """
    from fastapi import Query  # local import to avoid cluttering top-level

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    current_status = project.vector_generation_status or "not_started"

    if current_status in ("pending",):
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

    # Launch background task
    asyncio.create_task(generate_vector_data_for_project(project_id))
    logger.info(
        "Vector data generation triggered for project %s via API.", project_id
    )

    return {
        "project_id": project_id,
        "triggered": True,
        "status": "pending",
        "message": "Vector data generation started in background.",
    }