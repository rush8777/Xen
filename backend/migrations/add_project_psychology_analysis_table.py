"""
Migration script to add project psychology analyses table.
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
        CREATE TABLE IF NOT EXISTS project_psychology_analyses (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL UNIQUE,
            psychology_json TEXT NOT NULL DEFAULT '{}',
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            version INTEGER NOT NULL DEFAULT 1,
            error TEXT,
            generated_at DATETIME,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        """
    )

    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_project_psychology_analyses_project ON project_psychology_analyses(project_id)"
    )

    conn.commit()
    print("Migration completed successfully.")
except Exception as exc:
    print(f"Error during migration: {exc}")
    conn.rollback()
    raise
finally:
    conn.close()
