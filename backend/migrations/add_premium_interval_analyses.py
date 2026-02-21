"""
Migration script to add premium_interval_analyses table.

Run this once to upgrade an existing database.
For SQLite, it uses CREATE TABLE IF NOT EXISTS.
"""

import sqlite3
from pathlib import Path
import os
import sys

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

try:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_interval_analyses (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            interval_id INTEGER NOT NULL,
            interval_index INTEGER NOT NULL,
            start_time_seconds INTEGER NOT NULL,
            end_time_seconds INTEGER NOT NULL,
            pass_1_json TEXT,
            pass_2_json TEXT,
            pass_3_json TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE(project_id, interval_id)
        )
        """
    )

    conn.commit()
    print("Migration completed successfully.")
except Exception as e:
    print(f"Error during migration: {e}")
    conn.rollback()
    raise
finally:
    conn.close()
