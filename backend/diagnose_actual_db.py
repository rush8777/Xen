import os
import sys
sys.path.append('.')
from config import settings
from database import engine
from sqlalchemy import text
import sqlite3

print("=== DATABASE CONNECTION DIAGNOSTIC ===")
print(f"DATABASE_URL from config: {settings.DATABASE_URL}")
print(f"Current working directory: {os.getcwd()}")

# Test SQLAlchemy engine connection
print("\n=== SQLALCHEMY ENGINE TEST ===")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM projects"))
        project_count = result.scalar()
        print(f"Projects found via SQLAlchemy: {project_count}")
        
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%vector%'"))
        vector_tables = [row[0] for row in result.fetchall()]
        print(f"Vector tables found: {vector_tables}")
        
        if vector_tables:
            result = conn.execute(text("SELECT COUNT(*) FROM video_vector_embeddings"))
            vector_count = result.scalar()
            print(f"Vector embeddings found: {vector_count}")
            
except Exception as e:
    print(f"SQLAlchemy connection error: {e}")

# Test direct connection to root DB
print("\n=== DIRECT SQLITE TEST (root app.db) ===")
root_db_path = "D:/web_dev/v0-social/app.db"
try:
    conn = sqlite3.connect(root_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects")
    project_count = cursor.fetchone()[0]
    print(f"Projects in root app.db: {project_count}")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%vector%'")
    vector_tables = [row[0] for row in cursor.fetchall()]
    print(f"Vector tables in root DB: {vector_tables}")
    
    if vector_tables:
        cursor.execute("SELECT COUNT(*) FROM video_vector_embeddings")
        vector_count = cursor.fetchone()[0]
        print(f"Vector embeddings in root DB: {vector_count}")
    
    conn.close()
except Exception as e:
    print(f"Root SQLite error: {e}")
