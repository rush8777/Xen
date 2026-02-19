#!/usr/bin/env python3
"""
Initialize database and run RAG migrations for v0-social
"""

import sys
import os

# Set up paths
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")

    # Import after path setup
    import database

    try:
        # Import all models to ensure they're registered with SQLAlchemy
        import models  # This will register all models with Base
        database.Base.metadata.create_all(bind=database.engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def run_migration():
    """Run the vector generation status migration"""
    print("Running vector generation status migration...")

    try:
        # Import the migration script
        import migrations.add_vector_generation_status as migration

        print("✅ Migration completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    print("🚀 Initializing RAG Integration Database...")

    # Create tables first
    if not create_tables():
        return 1

    # Run migration
    if not run_migration():
        return 1

    print("🎉 RAG Integration setup complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
