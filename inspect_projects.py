# inspect_projects.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Project, User
from backend.config import settings

# Connect to database
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("=== CURRENT PROJECTS IN DATABASE ===\n")

# Get all projects
projects = db.query(Project).all()

if not projects:
    print("No projects found in database.")
else:
    print(f"Found {len(projects)} project(s):\n")
    
    for project in projects:
        print(f"📁 Project ID: {project.id}")
        print(f"   Name: {project.name}")
        print(f"   Category: {project.category or 'Not set'}")
        print(f"   Description: {project.description or 'Not set'}")
        print(f"   Video URL: {project.video_url or 'Not set'}")
        print(f"   Status: {project.status}")
        print(f"   Progress: {project.progress}%")
        print(f"   Job ID: {project.job_id or 'Not set'}")
        print(f"   Analysis File: {project.analysis_file_path or 'Not set'}")
        print(f"   Gemini URI: {project.gemini_file_uri or 'Not set'}")
        print(f"   Created: {project.created_at}")
        print(f"   Updated: {project.updated_at}")
        print("-" * 50)

print("\n=== USERS ===")
users = db.query(User).all()
if not users:
    print("No users found.")
else:
    for user in users:
        print(f"👤 User ID: {user.id}")
        print(f"   Email: {user.email or 'Not set'}")
        print(f"   Name: {user.name or 'Not set'}")
        print(f"   Created: {user.created_at}")
        print("-" * 30)

db.close()
