from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ..config import settings


class QueueConfigurationError(RuntimeError):
    pass


TASK_TARGETS: dict[str, dict[str, str]] = {
    "ingest": {
        "queue": settings.CLOUD_TASKS_QUEUE_INGEST,
        "path": "/internal/tasks/ingest-run",
        "base_url": settings.WORKER_INGEST_BASE_URL or settings.WORKER_BASE_URL or "",
        "audience": settings.WORKER_INGEST_AUDIENCE or settings.WORKER_AUDIENCE or "",
    },
    "statistics": {
        "queue": settings.CLOUD_TASKS_QUEUE_STATS,
        "path": "/internal/tasks/statistics-generate",
        "base_url": settings.WORKER_STATS_BASE_URL or settings.WORKER_BASE_URL or "",
        "audience": settings.WORKER_STATS_AUDIENCE or settings.WORKER_AUDIENCE or "",
    },
    "vector": {
        "queue": settings.CLOUD_TASKS_QUEUE_VECTOR,
        "path": "/internal/tasks/vector-generate",
        "base_url": settings.WORKER_VECTOR_BASE_URL or settings.WORKER_BASE_URL or "",
        "audience": settings.WORKER_VECTOR_AUDIENCE or settings.WORKER_AUDIENCE or "",
    },
    "overview": {
        "queue": settings.CLOUD_TASKS_QUEUE_OVERVIEW,
        "path": "/internal/tasks/overview-generate",
        "base_url": settings.WORKER_DEEP_ANALYSIS_BASE_URL or settings.WORKER_BASE_URL or "",
        "audience": settings.WORKER_DEEP_ANALYSIS_AUDIENCE or settings.WORKER_AUDIENCE or "",
    },
    "premium": {
        "queue": settings.CLOUD_TASKS_QUEUE_PREMIUM,
        "path": "/internal/tasks/premium-generate",
        "base_url": settings.WORKER_DEEP_ANALYSIS_BASE_URL or settings.WORKER_BASE_URL or "",
        "audience": settings.WORKER_DEEP_ANALYSIS_AUDIENCE or settings.WORKER_AUDIENCE or "",
    },
    "psychology": {
        "queue": settings.CLOUD_TASKS_QUEUE_PSYCHOLOGY,
        "path": "/internal/tasks/psychology-generate",
        "base_url": settings.WORKER_DEEP_ANALYSIS_BASE_URL or settings.WORKER_BASE_URL or "",
        "audience": settings.WORKER_DEEP_ANALYSIS_AUDIENCE or settings.WORKER_AUDIENCE or "",
    },
    "content_features": {
        "queue": settings.CLOUD_TASKS_QUEUE_CONTENT_FEATURES,
        "path": "/internal/tasks/content-features-generate",
        "base_url": settings.WORKER_DEEP_ANALYSIS_BASE_URL or settings.WORKER_BASE_URL or "",
        "audience": settings.WORKER_DEEP_ANALYSIS_AUDIENCE or settings.WORKER_AUDIENCE or "",
    },
}


def enqueue_task(
    *,
    target: str,
    payload: dict[str, Any],
    request_id: str | None = None,
) -> dict[str, str]:
    cfg = TASK_TARGETS.get(target)
    if not cfg:
        raise QueueConfigurationError(f"Unknown task target: {target}")

    req_id = request_id or str(uuid4())
    task_payload = {
        **payload,
        "request_id": req_id,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }

    if settings.TASKS_MODE != "cloud_tasks":
        return {"mode": "inline", "request_id": req_id, "task_name": ""}

    if not settings.GCP_PROJECT_ID:
        raise QueueConfigurationError("Missing GCP_PROJECT_ID for Cloud Tasks mode.")
    if not cfg["base_url"]:
        raise QueueConfigurationError(f"Missing base URL for Cloud Tasks target '{target}'.")

    try:
        from google.cloud import tasks_v2
    except ImportError as exc:
        raise QueueConfigurationError(
            "google-cloud-tasks is not installed. Add it to backend requirements."
        ) from exc

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(
        settings.GCP_PROJECT_ID,
        settings.GCP_LOCATION,
        cfg["queue"],
    )

    target_url = cfg["base_url"].rstrip("/") + cfg["path"]
    task: dict[str, Any] = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": target_url,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(task_payload).encode("utf-8"),
        }
    }

    if settings.WORKER_AUTH_MODE == "oidc":
        if not settings.WORKER_INVOKER_SERVICE_ACCOUNT:
            raise QueueConfigurationError(
                "Missing WORKER_INVOKER_SERVICE_ACCOUNT for WORKER_AUTH_MODE=oidc."
            )
        task["http_request"]["oidc_token"] = {
            "service_account_email": settings.WORKER_INVOKER_SERVICE_ACCOUNT,
            "audience": cfg["audience"] or cfg["base_url"],
        }
    elif settings.WORKER_AUTH_MODE == "shared_secret":
        if not settings.WORKER_SHARED_SECRET:
            raise QueueConfigurationError(
                "Missing WORKER_SHARED_SECRET for WORKER_AUTH_MODE=shared_secret."
            )
        task["http_request"]["headers"]["X-Worker-Secret"] = settings.WORKER_SHARED_SECRET

    created = client.create_task(parent=parent, task=task)
    return {"mode": "cloud_tasks", "request_id": req_id, "task_name": created.name}


def enqueue_statistics_generation(
    *,
    project_id: int,
    run_id: int | None,
    request_id: str | None = None,
) -> dict[str, str]:
    return enqueue_task(
        target="statistics",
        payload={"project_id": project_id, "run_id": run_id},
        request_id=request_id,
    )


def enqueue_ingest_run(
    *,
    project_id: int,
    job_id: str,
    video_url: str,
    project_name: str | None,
    request_id: str | None = None,
) -> dict[str, str]:
    return enqueue_task(
        target="ingest",
        payload={
            "project_id": project_id,
            "job_id": job_id,
            "video_url": video_url,
            "project_name": project_name,
        },
        request_id=request_id,
    )


def enqueue_vector_generation(
    *,
    project_id: int,
    request_id: str | None = None,
) -> dict[str, str]:
    return enqueue_task(
        target="vector",
        payload={"project_id": project_id},
        request_id=request_id,
    )


def enqueue_overview_generation(
    *,
    project_id: int,
    request_id: str | None = None,
) -> dict[str, str]:
    return enqueue_task(
        target="overview",
        payload={"project_id": project_id},
        request_id=request_id,
    )


def enqueue_premium_generation(
    *,
    project_id: int,
    request_id: str | None = None,
) -> dict[str, str]:
    return enqueue_task(
        target="premium",
        payload={"project_id": project_id},
        request_id=request_id,
    )


def enqueue_psychology_generation(
    *,
    project_id: int,
    run_id: int | None,
    interval_seconds: int = 5,
    request_id: str | None = None,
) -> dict[str, str]:
    safe_interval_seconds = 2 if interval_seconds == 2 else 5
    return enqueue_task(
        target="psychology",
        payload={
            "project_id": project_id,
            "run_id": run_id,
            "interval_seconds": safe_interval_seconds,
        },
        request_id=request_id,
    )


def enqueue_content_features_generation(
    *,
    project_id: int,
    feature_id: str | None = None,
    force: bool = False,
    request_id: str | None = None,
) -> dict[str, str]:
    return enqueue_task(
        target="content_features",
        payload={"project_id": project_id, "feature_id": feature_id, "force": force},
        request_id=request_id,
    )

