"""
Migration script to add premium analysis status fields to the projects table.

Run this once to upgrade an existing database.
For SQLite, it uses ALTER TABLE to add the new columns safely.
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
    # Point to the root directory's app.db
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
    # Inspect existing columns
    cursor.execute("PRAGMA table_info(projects)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    new_columns = [
        ("premium_analysis_status", "VARCHAR(20) NOT NULL DEFAULT 'not_started'"),
        ("premium_analysis_started_at", "DATETIME"),
        ("premium_analysis_completed_at", "DATETIME"),
        ("premium_analysis_error", "TEXT"),
    ]

    for col_name, col_def in new_columns:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_def}")
            print(f"  Added column: {col_name}")
        else:
            print(f"  Column already exists (skipped): {col_name}")

    conn.commit()
    print("Migration completed successfully.")

except Exception as e:
    print(f"Error during migration: {e}")
    conn.rollback()
    raise
finally:
    conn.close()
