from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from ..config import settings
from ..database import SessionLocal
from ..extractor.comments_extractor import CommentsExtractor
from ..gemini_backend.config import GEMINI_API_KEY
from ..gemini_backend.gemini_client import upload_video_to_gemini
from ..models import Project, ProjectOverview, User, Video
from ..cobalt_downloader import VideoDownloader
from .thumbnail_extractor import extract_thumbnail_url
from .content_features_generator import ProjectContentFeaturesGenerator
from .pipeline_jobs import update_pipeline_job
from .premium_analysis_service import generate_premium_analysis_for_project
from .project_overview_generator import ProjectOverviewGenerator
from .psychology_tasks import execute_psychology_generation
from .statistics_tasks import create_statistics_run, ensure_statistics_pending, execute_statistics_generation
from .task_queue import (
    enqueue_overview_generation,
    enqueue_statistics_generation,
    enqueue_vector_generation,
)
from .vector_data_generator import generate_vector_data_for_project

logger = logging.getLogger(__name__)

_video_downloader = VideoDownloader()
_comments_extractor = CommentsExtractor()
_overview_generator = ProjectOverviewGenerator(api_key=GEMINI_API_KEY)
_content_features_generator = ProjectContentFeaturesGenerator()


def _resolve_cobalt_video_title(video_url: str) -> str | None:
    try:
        info = _video_downloader.get_info(video_url)
    except Exception as exc:
        logger.warning("Failed to fetch cobalt info for title extraction: %s", exc)
        return None

    if not isinstance(info, dict):
        return None

    title = info.get("title")
    if not isinstance(title, str):
        return None

    cleaned = title.strip()
    return cleaned or None


def run_ingest_task(*, project_id: int, job_id: str, video_url: str, project_name: str | None) -> None:
    db = SessionLocal()
    tmp_file: Path | None = None
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            update_pipeline_job(
                job_id=job_id,
                status="failed",
                error="Project not found",
                message="Project not found",
            )
            return

        update_pipeline_job(job_id=job_id, status="running", step=0, message="Initializing video analysis")
        update_pipeline_job(job_id=job_id, step=1, message="Downloading video")

        tmp_dir = Path(tempfile.gettempdir())
        tmp_filename = f"v0social_{os.getpid()}_{os.urandom(4).hex()}"
        original_download_dir = _video_downloader.download_dir
        _video_downloader.download_dir = tmp_dir
        try:
            downloaded_file = _video_downloader.download(
                url=video_url,
                quality="720p",
                audio_only=False,
                output_filename=tmp_filename,
            )
            tmp_file = Path(downloaded_file)
        finally:
            _video_downloader.download_dir = original_download_dir

        if not tmp_file or not tmp_file.exists():
            raise RuntimeError(f"Downloaded file not found at {tmp_file}")

        update_pipeline_job(job_id=job_id, step=2, message="Extracting comments")
        if _comments_extractor.is_available():
            try:
                _comments_extractor.extract_comments(
                    url=video_url,
                    max_comments=100,
                    include_replies=True,
                )
            except Exception as exc:
                logger.warning("Comments extraction failed for project %s: %s", project_id, exc)
        else:
            logger.info("Skipping comment extraction (disabled in Cobalt-only runtime) for project %s", project_id)

        update_pipeline_job(job_id=job_id, step=3, message="Uploading video for overview generation")
        cached_content_name = asyncio.run(upload_video_to_gemini(tmp_file))

        user = db.query(User).filter(User.id == project.user_id).first()
        if not user:
            user = User(id=project.user_id, email=None, name=None)
            db.add(user)
            db.commit()
            db.refresh(user)

        thumbnail_url = extract_thumbnail_url(video_url)

        extracted_video_title = _resolve_cobalt_video_title(video_url)
        resolved_title = extracted_video_title or (project_name or project.name or "Analyzed Video")
        if extracted_video_title:
            project.name = extracted_video_title

        if not project.video_id:
            video = Video(
                user_id=project.user_id,
                title=resolved_title,
                description=f"Video analysis for project: {resolved_title}",
                platform="youtube",
                url=video_url,
                thumbnail_url=thumbnail_url,
                duration_seconds=30,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(video)
            db.commit()
            db.refresh(video)
            project.video_id = video.id
        else:
            video = db.query(Video).filter(Video.id == project.video_id).first()
            if video:
                if thumbnail_url and not video.thumbnail_url:
                    video.thumbnail_url = thumbnail_url
                if extracted_video_title:
                    video.title = extracted_video_title

        project.video_url = video_url
        project.job_id = job_id
        project.gemini_cached_content_name = cached_content_name
        project.video_duration_seconds = project.video_duration_seconds or 30
        project.status = "in_progress"
        project.progress = 60
        db.commit()

        # Trigger downstream tasks
        ensure_statistics_pending(project_id=project_id)
        run = create_statistics_run(project_id=project_id)
        if settings.TASKS_MODE == "cloud_tasks":
            enqueue_statistics_generation(project_id=project_id, run_id=run.id)
            enqueue_overview_generation(project_id=project_id)
            enqueue_vector_generation(project_id=project_id)
        else:
            run_statistics_task_inline(project_id=project_id, run_id=run.id)
            run_overview_task(project_id=project_id)
            run_vector_task(project_id=project_id)

        update_pipeline_job(
            job_id=job_id,
            status="completed",
            step=5,
            message="Opening Streamline",
            project_id=project_id,
        )
        project.status = "completed"
        project.progress = 100
        db.commit()
    except Exception as exc:
        logger.exception("Ingest task failed for project %s", project_id)
        update_pipeline_job(
            job_id=job_id,
            status="failed",
            message="Pipeline failed",
            error=str(exc),
            project_id=project_id,
        )
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        try:
            if tmp_file and tmp_file.exists():
                tmp_file.unlink(missing_ok=True)
        except Exception:
            pass
        db.close()


def run_overview_task(*, project_id: int) -> None:
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error("Project %s not found for overview generation", project_id)
            return

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
                status="pending",
            )
            db.add(overview)
            db.commit()
            db.refresh(overview)
        else:
            overview.status = "pending"
            overview.error = None
            db.commit()

        overview_data = asyncio.run(
            _overview_generator.generate_overview(
                analysis_file_path=project.analysis_file_path or "",
                video_url=project.video_url or "",
                project_name=project.name,
                project_id=project.id,
                job_id=project.job_id,
                cached_content_name=project.gemini_cached_content_name,
                video_duration_seconds=project.video_duration_seconds,
            )
        )
        blog = overview_data.get("blog") if isinstance(overview_data, dict) else None
        blog_markdown = str(blog.get("markdown") if isinstance(blog, dict) else "")
        summary = str(overview_data.get("summary") or "")
        insights = overview_data.get("insights")
        if not isinstance(insights, dict):
            insights = {}

        overview.blog_markdown = blog_markdown
        overview.summary = summary
        overview.insights_json = json.dumps(insights)
        overview.status = "completed"
        overview.generated_at = datetime.utcnow()
        overview.error = None
        db.commit()
    except Exception as exc:
        logger.exception("Overview generation failed for project %s", project_id)
        try:
            overview = (
                db.query(ProjectOverview)
                .filter(ProjectOverview.project_id == project_id)
                .first()
            )
            if overview:
                overview.status = "failed"
                overview.error = str(exc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def run_vector_task(*, project_id: int) -> None:
    asyncio.run(generate_vector_data_for_project(project_id))


def run_premium_task(*, project_id: int) -> None:
    asyncio.run(generate_premium_analysis_for_project(project_id))


def run_psychology_task(
    *,
    project_id: int,
    run_id: int | None = None,
    interval_seconds: int = 5,
) -> None:
    execute_psychology_generation(
        project_id=project_id,
        run_id=run_id,
        interval_seconds=interval_seconds,
    )


def run_content_features_task(*, project_id: int, feature_id: str | None, force: bool) -> None:
    if feature_id:
        asyncio.run(_content_features_generator.generate_feature(project_id, feature_id, force=force))
        return
    asyncio.run(_content_features_generator.generate_all(project_id, force=force))


def run_statistics_task_inline(*, project_id: int, run_id: int | None = None) -> None:
    execute_statistics_generation(project_id=project_id, run_id=run_id)
