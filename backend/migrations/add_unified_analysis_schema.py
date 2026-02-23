"""
Create unified interval/analysis/embedding tables.
"""

import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings


def _resolve_sqlite_db_path(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise RuntimeError("This migration script only supports SQLite databases.")
    db_file = database_url.replace("sqlite:///", "")
    if db_file.startswith("./"):
        backend_dir = Path(__file__).parent.parent.parent
        return backend_dir / db_file[2:]
    return Path(db_file).resolve()


def run() -> None:
    db_path = _resolve_sqlite_db_path(settings.DATABASE_URL)
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        print("Database will be created automatically with unified schema on first run.")
        return

    print(f"Running migration on: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_intervals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                parent_interval_id INTEGER NULL,
                granularity VARCHAR(32) NOT NULL,
                interval_index INTEGER NOT NULL DEFAULT -1,
                sub_index INTEGER NOT NULL DEFAULT -1,
                start_time_seconds INTEGER NOT NULL,
                end_time_seconds INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (video_id) REFERENCES videos(id),
                FOREIGN KEY (parent_interval_id) REFERENCES analysis_intervals(id),
                UNIQUE(project_id, granularity, interval_index, sub_index)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                interval_id INTEGER NOT NULL,
                analysis_type VARCHAR(64) NOT NULL,
                source_pass INTEGER NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'completed',
                summary_text TEXT NULL,
                payload_json TEXT NULL,
                confidence REAL NULL,
                schema_version INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (video_id) REFERENCES videos(id),
                FOREIGN KEY (interval_id) REFERENCES analysis_intervals(id),
                UNIQUE(project_id, interval_id, analysis_type)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_embeddings (
                analysis_record_id INTEGER PRIMARY KEY,
                embedding TEXT NULL,
                embedding_model VARCHAR(64) NOT NULL DEFAULT 'gemini-embedding-001',
                embedding_dim INTEGER NOT NULL DEFAULT 3072,
                embedded_at DATETIME NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_record_id) REFERENCES analysis_records(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                run_type VARCHAR(32) NOT NULL,
                status VARCHAR(20) NOT NULL,
                started_at DATETIME NULL,
                completed_at DATETIME NULL,
                error TEXT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
            """
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_intervals_project_time ON analysis_intervals(project_id, start_time_seconds, end_time_seconds)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_records_project_type ON analysis_records(project_id, analysis_type, status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_records_interval ON analysis_records(interval_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_embeddings_model_dim ON analysis_embeddings(embedding_model, embedding_dim)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_runs_project_type ON analysis_runs(project_id, run_type, status)"
        )

        conn.commit()
        print("Unified schema migration completed.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run()
