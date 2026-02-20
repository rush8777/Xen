"""
Migration script to add VectorDB tables for video intervals and embeddings.

Run this once to add the new tables to existing databases.
For SQLite, this creates tables if they don't exist.
"""

import sqlite3
from pathlib import Path
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

# Get database path from settings
DB_PATH = settings.DATABASE_URL

# Extract file path from SQLite URL
if DB_PATH.startswith("sqlite:///"):
    db_file = DB_PATH.replace("sqlite:///", "")
    if db_file.startswith("./"):
        # Relative to backend directory
        backend_dir = Path(__file__).parent.parent
        db_path = backend_dir / db_file[2:]
    else:
        db_path = Path(db_file).resolve()
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        print("The database will be created automatically on first run with the new tables.")
        print("If you have an existing database, please ensure it's at the correct path.")
        exit(0)
    
    print(f"Adding tables to database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Create video_intervals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_intervals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                interval_index INTEGER NOT NULL,
                start_time_seconds INTEGER NOT NULL,
                end_time_seconds INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(id),
                UNIQUE(video_id, interval_index)
            )
        """)
        print("Created video_intervals table.")
        
        # Create video_sub_intervals table (no embeddings here)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_sub_intervals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interval_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                sub_index INTEGER NOT NULL,
                start_time_seconds INTEGER NOT NULL,
                end_time_seconds INTEGER NOT NULL,
                camera_frame TEXT,
                environment_background TEXT,
                people_figures TEXT,
                objects_props TEXT,
                text_symbols TEXT,
                motion_changes TEXT,
                lighting_color TEXT,
                audio_visible_indicators TEXT,
                occlusions_limits TEXT,
                raw_combined_text TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interval_id) REFERENCES video_intervals(id),
                FOREIGN KEY (video_id) REFERENCES videos(id),
                UNIQUE(video_id, start_time_seconds)
            )
        """)
        print("Created video_sub_intervals table.")

        # Create sub_video_interval_embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sub_video_interval_embeddings (
                sub_interval_id INTEGER PRIMARY KEY,
                embedding TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sub_interval_id) REFERENCES video_sub_intervals(id)
            )
        """)
        print("Created sub_video_interval_embeddings table.")

        # Migrate existing embeddings if legacy column exists
        cursor.execute("PRAGMA table_info(video_sub_intervals)")
        columns = [row[1] for row in cursor.fetchall()]
        if "embedding" in columns:
            cursor.execute("""
                INSERT OR IGNORE INTO sub_video_interval_embeddings (sub_interval_id, embedding)
                SELECT id, embedding
                FROM video_sub_intervals
                WHERE embedding IS NOT NULL AND embedding != ''
            """)
            print("Migrated existing sub-interval embeddings.")
        
        # Create interval_embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interval_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                interval_id INTEGER NOT NULL,
                combined_interval_text TEXT,
                embedding TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(id),
                FOREIGN KEY (interval_id) REFERENCES video_intervals(id)
            )
        """)
        print("Created interval_embeddings table.")
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_intervals_video_id ON video_intervals(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_sub_intervals_video_id ON video_sub_intervals(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_sub_intervals_interval_id ON video_sub_intervals(interval_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interval_embeddings_video_id ON interval_embeddings(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interval_embeddings_interval_id ON interval_embeddings(interval_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_video_interval_embeddings_sub_interval_id ON sub_video_interval_embeddings(sub_interval_id)")
        print("Created indexes.")
        
        conn.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
else:
    print("This migration script only supports SQLite databases.")
    exit(1)
