from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
import uuid
import asyncio
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

# Import the yt-dlp downloader directly
from .video_downloader import VideoDownloader

# Import Gemini analyzer components directly
from .gemini_analyzer import VideoAnalyzer

# Import comments extractor
from ..extractor.comments_extractor import CommentsExtractor

# Import database dependencies and models
from ..dependencies import get_db
from ..models import Project, User, ProjectStatistics, ProjectOverview
from ..gemini_backend.config import GEMINI_API_KEY
from ..services.project_statistics_generator import ProjectStatisticsGenerator
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
video_analyzer = VideoAnalyzer()
comments_extractor = CommentsExtractor()

stats_generator = ProjectStatisticsGenerator(api_key=GEMINI_API_KEY)
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


def _generate_statistics_sync(project_id: int):
    """Generate statistics in background task (sync)."""
    from ..database import SessionLocal

    db2 = SessionLocal()
    try:
        project = db2.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project {project_id} not found for statistics generation")
            return

        stats = (
            db2.query(ProjectStatistics)
            .filter(ProjectStatistics.project_id == project_id)
            .first()
        )
        if not stats:
            stats = ProjectStatistics(project_id=project_id, stats_json="{}", status="pending")
            db2.add(stats)
            db2.commit()
            db2.refresh(stats)
        else:
            stats.status = "pending"
            stats.error = None
            db2.commit()

        try:
            stats_data = stats_generator.generate_statistics(
                analysis_file_path=project.analysis_file_path or "",
                video_url=project.video_url or "",
                project_name=project.name,
                project_id=project.id,
                job_id=project.job_id,
            )
            import json as _json
            from datetime import datetime as _dt

            stats.stats_json = _json.dumps(stats_data)
            stats.status = "completed"
            stats.generated_at = _dt.utcnow()
            stats.error = None
            db2.commit()
            logger.info(f"Statistics generation completed for project {project_id}")
        except Exception as e:
            logger.error(f"Statistics generation failed for project {project_id}: {e}")
            stats.status = "failed"
            stats.error = str(e)
            db2.commit()
    finally:
        db2.close()


def _generate_overview_sync(project_id: int) -> None:
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

        if not project.analysis_file_path:
            overview.status = "failed"
            overview.error = "Project has no analysis file. Cannot generate overview."
            db2.commit()
            return

        try:
            overview_data = overview_generator.generate_overview(
                analysis_file_path=project.analysis_file_path or "",
                video_url=project.video_url or "",
                project_name=project.name,
                project_id=project.id,
                job_id=project.job_id,
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

            # 3) Gemini analysis
            _set_progress(job_id_, step=3, text="Running Gemini analysis")
            analyzer_job_id = video_analyzer.create_job(tmp_file)
            output_path = await video_analyzer.analyze_job(analyzer_job_id)

            # Get gemini_file_uri if available
            gemini_file_uri = None
            job = video_analyzer.jobs.get(analyzer_job_id)
            if job:
                gemini_file_uri = job.get("gemini_file_uri")

            # 4) Append comments
            try:
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write("\n" + "=" * 80 + "\n")
                    f.write("VIDEO COMMENTS\n")
                    f.write("=" * 80 + "\n\n")
                    if comments_data and comments_data.get("comments_count", 0) > 0:
                        f.write(f"Total Comments: {comments_data['comments_count']}\n")
                        f.write(f"Video Title: {comments_data['video_info']['title']}\n")
                        f.write(f"Video URL: {url}\n\n")
                        for comment in comments_data["comments"]:
                            f.write(f"Author: {comment['author']}\n")
                            f.write(f"Likes: {comment['like_count']}\n")
                            if comment["is_reply"]:
                                f.write("[REPLY]\n")
                            f.write(f"Text: {comment['text']}\n")
                            f.write("-" * 80 + "\n")
                    else:
                        f.write("No comments found\n")
                        f.write(f"Video URL: {url}\n")
            except Exception as e:
                logger.warning(f"Failed to append comments to file (non-critical): {e}")

            project_id: int | None = None
            if project_name:
                _set_progress(job_id_, step=4, text="Creating project")
                user = db2.query(User).filter(User.id == 1).first()
                if not user:
                    user = User(id=1, email=None, name=None)
                    db2.add(user)
                    db2.commit()
                    db2.refresh(user)

                project = Project(
                    user_id=1,
                    name=project_name,
                    video_url=url,
                    job_id=analyzer_job_id,
                    analysis_file_path=str(output_path),
                    gemini_file_uri=gemini_file_uri,
                    status="in_progress",
                    progress=0,
                )
                db2.add(project)
                db2.commit()
                db2.refresh(project)
                project_id = project.id

                # statistics generation
                try:
                    _generate_statistics_sync(project_id)
                except Exception as e:
                    logger.warning(f"Statistics generation failed (non-critical): {e}")

                # overview generation
                try:
                    _generate_overview_sync(project_id)
                except Exception as e:
                    logger.warning(f"Overview generation failed (non-critical): {e}")

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


@router.get("/analysis/status/{job_id}")
async def get_analysis_status(job_id: str):
    """
    Get analysis status directly from VideoAnalyzer
    """
    logger.info(f"Getting analysis status for job_id: {job_id}")
    
    try:
        status = video_analyzer.get_job_status(job_id)
        logger.info(f"Status: {status['status']}")
        return status
    except ValueError as e:
        logger.error(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/results/{job_id}",
    response_class=PlainTextResponse,
)
async def get_analysis_results(job_id: str) -> str:
    """
    Get analysis results directly from VideoAnalyzer
    Returns plain text with timestamped descriptions
    """
    logger.info(f"Getting analysis results for job_id: {job_id}")
    
    try:
        # Get job status first
        status = video_analyzer.get_job_status(job_id)
        
        if status['status'] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Analysis not completed yet. Current status: {status['status']}"
            )
        
        # Get the job to find output path
        job = video_analyzer.jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        output_path = job.get('output_path')
        if not output_path or not output_path.exists():
            raise HTTPException(status_code=404, detail="Results file not found")
        
        # Read and return results
        with open(output_path, 'r', encoding='utf-8') as f:
            results = f.read()
        
        logger.info(f"Results retrieved successfully for job_id: {job_id}")
        return results
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Results retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))