"""
Migration script to add premium interval tables (structural, psychological, performance).
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
        CREATE TABLE IF NOT EXISTS premium_structural_intervals (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            interval_id INTEGER NOT NULL,
            interval_index INTEGER NOT NULL,
            start_time_seconds INTEGER NOT NULL,
            end_time_seconds INTEGER NOT NULL,

            hook_strength_score INTEGER,
            hook_strength_justification TEXT,

            stimulation_cuts_per_20s INTEGER,
            stimulation_camera_variation VARCHAR(20),
            stimulation_motion_intensity VARCHAR(20),
            stimulation_justification TEXT,

            escalation_intensity_increase INTEGER,
            escalation_stakes_raised INTEGER,
            escalation_justification TEXT,

            cognitive_information_rate VARCHAR(20),
            cognitive_over_explanation_risk INTEGER,
            cognitive_justification TEXT,

            drop_risk_score_percent INTEGER,
            drop_risk_justification TEXT,

            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE(project_id, interval_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_psychological_intervals (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            interval_id INTEGER NOT NULL,
            interval_index INTEGER NOT NULL,
            start_time_seconds INTEGER NOT NULL,
            end_time_seconds INTEGER NOT NULL,

            primary_trigger_type VARCHAR(50),
            primary_trigger_justification TEXT,

            trigger_intensity_score INTEGER,
            trigger_intensity_justification TEXT,

            emotional_arc_pattern_type VARCHAR(50),
            emotional_arc_justification TEXT,

            attention_sustainability_type VARCHAR(50),
            attention_sustainability_justification TEXT,

            viewer_momentum_score INTEGER,
            viewer_momentum_justification TEXT,

            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE(project_id, interval_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS premium_performance_intervals (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            interval_id INTEGER NOT NULL,
            interval_index INTEGER NOT NULL,
            start_time_seconds INTEGER NOT NULL,
            end_time_seconds INTEGER NOT NULL,

            retention_strength_score INTEGER,
            retention_strength_justification TEXT,

            competitive_density_score INTEGER,
            competitive_density_justification TEXT,

            platform_tiktok_score INTEGER,
            platform_tiktok_justification TEXT,
            platform_instagram_reels_score INTEGER,
            platform_instagram_reels_justification TEXT,
            platform_youtube_shorts_score INTEGER,
            platform_youtube_shorts_justification TEXT,

            conversion_leverage_score INTEGER,
            conversion_leverage_justification TEXT,

            total_performance_index_score INTEGER,
            total_performance_index_justification TEXT,

            structural_weakness_priority_json TEXT,
            highest_leverage_target TEXT,
            highest_leverage_justification TEXT,

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
