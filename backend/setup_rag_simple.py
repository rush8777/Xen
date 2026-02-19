#!/usr/bin/env python3
"""
Standalone RAG database setup script - no relative imports
"""

import sys
import os
import sqlite3

def setup_database():
    """Set up database and run migrations"""
    print("🚀 Setting up RAG Integration Database...")

    # Find the backend directory and database
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    db_path = os.path.join(backend_dir, 'app.db')

    print(f"Database path: {db_path}")

    # Check if database exists
    if not os.path.exists(db_path):
        print("❌ Database file not found. Please run the backend first to create tables.")
        return False

    # Run migration
    print("Running vector generation status migration...")
    try:
        # Set PYTHONPATH and run migration
        env = os.environ.copy()
        env['PYTHONPATH'] = backend_dir

        import subprocess
        result = subprocess.run([
            sys.executable,
            os.path.join(backend_dir, 'migrations', 'add_vector_generation_status.py')
        ], cwd=backend_dir, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Migration completed successfully!")
            print("🎉 RAG Integration setup complete!")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
