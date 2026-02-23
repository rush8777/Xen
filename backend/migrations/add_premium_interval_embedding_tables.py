"""
Migration script to add premium interval embedding tables.
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
        CREATE TABLE IF NOT EXISTS premium_structural_interval_embeddings (
            structural_interval_id INTEGER PRIMARY KEY,
            combined_text TEXT,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (structural_interval_id) REFERENCES premium_structural_intervals(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_psychological_interval_embeddings (
            psychological_interval_id INTEGER PRIMARY KEY,
            combined_text TEXT,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (psychological_interval_id) REFERENCES premium_psychological_intervals(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_performance_interval_embeddings (
            performance_interval_id INTEGER PRIMARY KEY,
            combined_text TEXT,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (performance_interval_id) REFERENCES premium_performance_intervals(id)
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
        "CREATE INDEX IF NOT EXISTS idx_premium_structural_interval_embeddings_id ON premium_structural_interval_embeddings(structural_interval_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_premium_psych_interval_embeddings_id ON premium_psychological_interval_embeddings(psychological_interval_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_premium_perf_interval_embeddings_id ON premium_performance_interval_embeddings(performance_interval_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_premium_transcript_interval_embeddings_id ON premium_transcript_interval_embeddings(transcript_interval_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_premium_verification_interval_embeddings_id ON premium_verification_interval_embeddings(verification_interval_id)"
    )

    conn.commit()
    print("Migration completed successfully.")
except Exception as e:
    print(f"Error during migration: {e}")
    conn.rollback()
    raise
finally:
    conn.close()
