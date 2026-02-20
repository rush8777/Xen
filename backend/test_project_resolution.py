#!/usr/bin/env python3
"""
Test the project name resolution logic
"""

import sqlite3
from pathlib import Path
import sys
import re

# Add parent directory to path to import config
sys.path.insert(0, '.')
from config import settings

def get_db_path():
    """Get database path from settings"""
    DB_PATH = settings.DATABASE_URL
    if DB_PATH.startswith('sqlite:///'):
        db_file = DB_PATH.replace('sqlite:///', '')
        if db_file.startswith('./'):
            backend_dir = Path('.').resolve()
            db_path = backend_dir / db_file[2:]
        else:
            db_path = Path(db_file).resolve()
        return db_path
    else:
        print('Only SQLite databases are supported')
        sys.exit(1)

def test_project_resolution():
    """Test project name extraction and resolution"""
    db_path = get_db_path()
    
    if not db_path.exists():
        print(f'Database file not found at {db_path}')
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get all projects
    cursor.execute('SELECT id, name FROM projects ORDER BY name')
    projects = cursor.fetchall()

    print('Available projects:')
    for project in projects:
        print(f'  ID: {project[0]}, Name: "{project[1]}"')
    
    print('\nTesting message extraction:')
    
    # Test messages
    test_messages = [
        "@Mock recording Summarize this project",
        "@Mock recording what is this about?",
        "@Are we eggs ? .(Egg Theory) explain the theory",
        "@Are we eggs tell me more"
    ]
    
    _MENTION_RE = re.compile(r"@([^\n@]+)")
    
    for message in test_messages:
        print(f'\nMessage: "{message}"')
        
        match = _MENTION_RE.search(message)
        if match:
            raw = (match.group(1) or "").strip()
            raw = raw.rstrip(" \t\r\n.,;:!?)]}\"'")
            print(f'  Extracted: "{raw}"')
            
            # Test against actual projects
            for project_id, project_name in projects:
                if project_name.lower() == raw.lower():
                    print(f'  ✓ Exact match: "{project_name}"')
                    break
                elif project_name.lower().startswith(raw.lower()):
                    print(f'  ⚠ Partial match: "{project_name}" starts with "{raw}"')
                    break
                elif raw.lower().startswith(project_name.lower()):
                    print(f'  ⚠ Reverse match: "{raw}" starts with "{project_name}"')
                    break
            else:
                print(f'  ✗ No match found')
        else:
            print('  No @ mention found')

    conn.close()

if __name__ == '__main__':
    test_project_resolution()
