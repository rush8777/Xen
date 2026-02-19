"""
Migration script to add cached video metadata columns to projects table.

Run this once to add the new columns to existing databases.
For SQLite, this uses ALTER TABLE ADD COLUMN (which SQLite supports).
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
        print("The database will be created automatically on first run with the new columns.")
        print("If you have an existing database, please ensure it's at the correct path.")
        exit(0)
    
    print(f"Adding columns to database: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "gemini_cached_content_name" not in columns:
            print("Adding gemini_cached_content_name column...")
            cursor.execute(
                "ALTER TABLE projects ADD COLUMN gemini_cached_content_name VARCHAR(255)"
            )
            print("✓ Added gemini_cached_content_name")
        else:
            print("✓ Column gemini_cached_content_name already exists.")
        
        if "video_duration_seconds" not in columns:
            print("Adding video_duration_seconds column...")
            cursor.execute(
                "ALTER TABLE projects ADD COLUMN video_duration_seconds INTEGER"
            )
            print("✓ Added video_duration_seconds")
        else:
            print("✓ Column video_duration_seconds already exists.")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()
else:
    print(f"Non-SQLite database detected: {DB_PATH}")
    print("Please run the following SQL manually:")
    print("  ALTER TABLE projects ADD COLUMN gemini_cached_content_name VARCHAR(255);")
    print("  ALTER TABLE projects ADD COLUMN video_duration_seconds INTEGER;")

