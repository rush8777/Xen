#!/usr/bin/env python3
"""
Direct database setup - bypasses import issues
"""

import sqlite3
import os

def create_tables():
    """Create the basic tables needed for RAG"""
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create basic tables
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email VARCHAR(255),
            name VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            description TEXT,
            video_url VARCHAR(500),
            video_id INTEGER,
            priority VARCHAR(50),
            progress INTEGER DEFAULT 0,
            status VARCHAR(50) DEFAULT 'draft',
            job_id VARCHAR(255),
            analysis_file_path VARCHAR(1000),
            gemini_file_uri VARCHAR(500),
            gemini_cached_content_name VARCHAR(255),
            video_duration_seconds INTEGER,
            start_date DATE,
            end_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            platform VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            role VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]

    for table_sql in tables:
        cursor.execute(table_sql)

    conn.commit()
    conn.close()
    print("✅ Basic database tables created!")

def add_vector_columns():
    """Add vector generation status columns to projects table"""
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(projects)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    new_columns = [
        ("vector_generation_status", "VARCHAR(20) NOT NULL DEFAULT 'not_started'"),
        ("vector_generation_started_at", "DATETIME"),
        ("vector_generation_completed_at", "DATETIME"),
        ("vector_generation_error", "TEXT"),
    ]

    for col_name, col_def in new_columns:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_def}")
            print(f"  Added column: {col_name}")
        else:
            print(f"  Column already exists (skipped): {col_name}")

    conn.commit()
    conn.close()
    print("✅ Vector columns added to projects table!")

if __name__ == "__main__":
    print("🚀 Setting up RAG database...")
    create_tables()
    add_vector_columns()
    print("🎉 RAG database setup complete!")
