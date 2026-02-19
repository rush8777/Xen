#!/usr/bin/env python3
"""
Create database tables only - run once to initialize
"""

import sys
import os

# Set up paths correctly
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

# Set up minimal environment
os.environ['DATABASE_URL'] = 'sqlite:///./app.db'
os.environ['SECRET_KEY'] = 'temp_key_for_init'
os.environ['GEMINI_API_KEY'] = 'temp_key_for_init'

try:
    # Import using absolute imports
    import database

    # Import models module to register all models
    import models

    # Create tables
    database.Base.metadata.create_all(bind=database.engine)
    print("✅ Database tables created successfully!")
except Exception as e:
    print(f"❌ Error creating tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
