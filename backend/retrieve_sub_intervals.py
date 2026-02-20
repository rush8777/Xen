#!/usr/bin/env python3
"""
Script to retrieve text data from video_sub_intervals table
"""

import sqlite3
from pathlib import Path
import sys
import json

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

def retrieve_sub_intervals(limit=20):
    """Retrieve text data from video_sub_intervals table"""
    db_path = get_db_path()
    
    if not db_path.exists():
        print(f'Database file not found at {db_path}')
        return
    
    print(f'Connecting to database: {db_path}')
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_sub_intervals'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print('video_sub_intervals table does not exist')
        conn.close()
        return
    
    # Get count first
    cursor.execute('SELECT COUNT(*) FROM video_sub_intervals')
    count = cursor.fetchone()[0]
    print(f'Total records: {count}')
    print('=' * 100)
    
    # Get records
    cursor.execute('''
        SELECT 
            id,
            video_id,
            interval_id,
            sub_index,
            start_time_seconds,
            end_time_seconds,
            camera_frame,
            environment_background,
            people_figures,
            objects_props,
            text_symbols,
            motion_changes,
            lighting_color,
            audio_visible_indicators,
            occlusions_limits,
            raw_combined_text,
            created_at
        FROM video_sub_intervals 
        ORDER BY video_id, start_time_seconds
        LIMIT ?
    ''', (limit,))
    
    records = cursor.fetchall()
    
    if not records:
        print('No records found in video_sub_intervals table')
    else:
        print(f'Showing first {len(records)} records:')
        print('=' * 100)
        
        for i, record in enumerate(records, 1):
            print(f'\n--- Record {i} ---')
            print(f'ID: {record[0]}')
            print(f'Video ID: {record[1]}')
            print(f'Interval ID: {record[2]}')
            print(f'Sub Index: {record[3]}')
            print(f'Time: {record[4]}s - {record[5]}s')
            
            # Text fields with truncation for readability
            fields = [
                ('Camera Frame', record[6]),
                ('Environment', record[7]),
                ('People', record[8]),
                ('Objects', record[9]),
                ('Text/Symbols', record[10]),
                ('Motion', record[11]),
                ('Lighting', record[12]),
                ('Audio', record[13]),
                ('Occlusions', record[14]),
                ('Combined Text', record[15])
            ]
            
            for field_name, field_value in fields:
                if field_value:
                    if len(field_value) > 200:
                        print(f'  {field_name}: {field_value[:200]}...')
                    else:
                        print(f'  {field_name}: {field_value}')
            
            print(f'Created: {record[16]}')
            print('-' * 50)
    
    conn.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Retrieve video sub intervals text data')
    parser.add_argument('--limit', type=int, default=20, help='Number of records to retrieve')
    args = parser.parse_args()
    
    retrieve_sub_intervals(args.limit)
