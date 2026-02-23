"""
Migration script to add pass 4/5 premium analysis fields and tables.
"""

import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

DB_PATH = settings.DATABASE_URL

if not DB_PATH.startswith("sqlite:///"):
    print("This migration script only supports SQLite databases.")
    sys.exit(1)

db_file = DB_PATH.replace("sqlite:///", "")
if db_file.startswith("./"):
    backend_dir = Path(__file__).parent.parent.parent
    db_path = backend_dir / db_file[2:]
else:
    db_path = Path(db_file).resolve()

if not db_path.exists():
    print(f"Database file not found at {db_path}")
    print("Database will be created automatically with all columns on first run.")
    sys.exit(0)

print(f"Running migration on: {db_path}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()


def _add_column_if_missing(table: str, column: str, column_def: str) -> None:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")
        print(f"Added {table}.{column}")


try:
    _add_column_if_missing("project_premium_analyses", "pass_4_output", "TEXT")
    _add_column_if_missing("project_premium_analyses", "pass_5_output", "TEXT")

    _add_column_if_missing("premium_interval_analyses", "pass_4_json", "TEXT")
    _add_column_if_missing("premium_interval_analyses", "pass_5_json", "TEXT")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_transcript_intervals (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            interval_id INTEGER NOT NULL,
            interval_index INTEGER NOT NULL,
            start_time_seconds INTEGER NOT NULL,
            end_time_seconds INTEGER NOT NULL,
            transcript_text TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, interval_id),
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (video_id) REFERENCES videos(id),
            FOREIGN KEY (interval_id) REFERENCES video_intervals(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_verification_intervals (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            interval_id INTEGER NOT NULL,
            interval_index INTEGER NOT NULL,
            start_time_seconds INTEGER NOT NULL,
            end_time_seconds INTEGER NOT NULL,
            question_type TEXT,
            timestamp_reference TEXT,
            visual_evidence_summary TEXT,
            verification_status TEXT,
            answer TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, interval_id),
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (video_id) REFERENCES videos(id),
            FOREIGN KEY (interval_id) REFERENCES video_intervals(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_transcript_interval_embeddings (
            transcript_interval_id INTEGER PRIMARY KEY,
            combined_text TEXT,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (transcript_interval_id) REFERENCES premium_transcript_intervals(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_verification_interval_embeddings (
            verification_interval_id INTEGER PRIMARY KEY,
            combined_text TEXT,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (verification_interval_id) REFERENCES premium_verification_intervals(id)
        )
        """
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_premium_transcript_project_interval ON premium_transcript_intervals(project_id, interval_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_premium_verification_project_interval ON premium_verification_intervals(project_id, interval_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_premium_transcript_embeddings_id ON premium_transcript_interval_embeddings(transcript_interval_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_premium_verification_embeddings_id ON premium_verification_interval_embeddings(verification_interval_id)"
    )

    conn.commit()
    print("Migration completed successfully.")
except Exception as exc:
    print(f"Error during migration: {exc}")
    conn.rollback()
    raise
finally:
    conn.close()
