"""
Migration script to add the project_content_features table.

Run this once to upgrade an existing SQLite database.
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
    print("Database will be created automatically with all tables on first run.")
    sys.exit(0)

print(f"Running migration on: {db_path}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS project_content_features (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL UNIQUE,
            status VARCHAR(20) NOT NULL DEFAULT 'not_started',
            started_at DATETIME,
            completed_at DATETIME,
            error TEXT,
            clips_status VARCHAR(20) NOT NULL DEFAULT 'not_started',
            clips_progress INTEGER NOT NULL DEFAULT 0,
            clips_json TEXT NOT NULL DEFAULT '{}',
            clips_error TEXT,
            subtitles_status VARCHAR(20) NOT NULL DEFAULT 'not_started',
            subtitles_progress INTEGER NOT NULL DEFAULT 0,
            subtitles_json TEXT NOT NULL DEFAULT '{}',
            subtitles_error TEXT,
            chapters_status VARCHAR(20) NOT NULL DEFAULT 'not_started',
            chapters_progress INTEGER NOT NULL DEFAULT 0,
            chapters_json TEXT NOT NULL DEFAULT '{}',
            chapters_error TEXT,
            moments_status VARCHAR(20) NOT NULL DEFAULT 'not_started',
            moments_progress INTEGER NOT NULL DEFAULT 0,
            moments_json TEXT NOT NULL DEFAULT '{}',
            moments_error TEXT,
            version INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_project_content_features_project ON project_content_features(project_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS ix_project_content_features_project_id ON project_content_features(project_id)"
    )

    conn.commit()
    print("Migration completed successfully.")
except Exception as e:
    conn.rollback()
    print(f"Error during migration: {e}")
    raise
finally:
    conn.close()

