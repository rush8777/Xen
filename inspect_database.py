#!/usr/bin/env python3
"""
Simple script to inspect the SQLite database contents
"""

import sqlite3
import os

def inspect_database(db_path):
    """Inspect and display database contents"""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"=== Database: {db_path} ===\n")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database")
            return
        
        print(f"Tables found: {len(tables)}")
        for table in tables:
            table_name = table[0]
            print(f"\n--- Table: {table_name} ---")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            print(f"Rows: {row_count}")
            
            # Show sample data (first 5 rows)
            if row_count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                rows = cursor.fetchall()
                print("Sample data:")
                for i, row in enumerate(rows, 1):
                    print(f"  Row {i}: {row}")
            
            print()
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

def clear_database(db_path):
    """Clear all data from database tables"""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"=== Clearing Database: {db_path} ===\n")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database")
            return
        
        # Clear each table
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # Skip SQLite internal table
                cursor.execute(f"DELETE FROM {table_name};")
                rows_deleted = cursor.rowcount
                print(f"Cleared table '{table_name}': {rows_deleted} rows deleted")
        
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence;")
        
        conn.commit()
        conn.close()
        
        print(f"\nDatabase {db_path} cleared successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        # Clear both database files
        db_files = [
            "d:/web_dev/v0-social/app.db",
            "d:/web_dev/v0-social/backend/app.db"
        ]
        
        for db_file in db_files:
            clear_database(db_file)
            print("-" * 50)
    else:
        # Check both possible database locations
        db_files = [
            "d:/web_dev/v0-social/app.db",
            "d:/web_dev/v0-social/backend/app.db",
            "app.db",  # Current directory
            "backend/app.db"  # Relative path
        ]
        
        for db_file in db_files:
            inspect_database(db_file)
            print("-" * 50)
