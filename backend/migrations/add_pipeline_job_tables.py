from __future__ import annotations

from sqlalchemy import text

from ..database import engine


def run() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_jobs (
                    id INTEGER PRIMARY KEY,
                    job_id VARCHAR(255) NOT NULL UNIQUE,
                    project_id INTEGER NULL,
                    job_type VARCHAR(64) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'queued',
                    step INTEGER NOT NULL DEFAULT 0,
                    message VARCHAR(255) NOT NULL DEFAULT 'Queued',
                    error TEXT NULL,
                    started_at DATETIME NULL,
                    completed_at DATETIME NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pipeline_jobs_job_id ON pipeline_jobs (job_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pipeline_jobs_project_id ON pipeline_jobs (project_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pipeline_jobs_job_type ON pipeline_jobs (job_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pipeline_jobs_status ON pipeline_jobs (status)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_job_events (
                    id INTEGER PRIMARY KEY,
                    job_id VARCHAR(255) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    step INTEGER NOT NULL DEFAULT 0,
                    message VARCHAR(255) NOT NULL DEFAULT '',
                    error TEXT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pipeline_job_events_job_id ON pipeline_job_events (job_id)"))


if __name__ == "__main__":
    run()
