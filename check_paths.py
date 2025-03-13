#!/usr/bin/env python3
"""
Script to check paths and script execution in the nitterlocal project.
"""

import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_script_paths():
    """Check if scripts exist at expected paths"""
    # Base paths
    repo_path = '/home/ubuntu/repos/nitterlocal'
    actual_path = '/home/ubuntu/nitterlocal'
    
    # Script paths to check
    script_paths = [
        'scripts/database/process_excel.py',
        'scripts/sync/sync_kol_character.py',
        'scripts/database/create_tables.py'
    ]
    
    print("Checking script paths:")
    print(f"Repo path: {repo_path}")
    print(f"Actual path: {actual_path}")
    
    for script in script_paths:
        repo_script_path = os.path.join(repo_path, script)
        actual_script_path = os.path.join(actual_path, script)
        
        repo_exists = os.path.exists(repo_script_path)
        actual_exists = os.path.exists(actual_script_path)
        
        print(f"\nScript: {script}")
        print(f"  Repo path exists: {repo_exists} - {repo_script_path}")
        print(f"  Actual path exists: {actual_exists} - {actual_script_path}")
        
        # If both exist, check if they're the same
        if repo_exists and actual_exists:
            try:
                # Get file sizes
                repo_size = os.path.getsize(repo_script_path)
                actual_size = os.path.getsize(actual_script_path)
                
                print(f"  Repo file size: {repo_size} bytes")
                print(f"  Actual file size: {actual_size} bytes")
                
                # Compare file contents
                with open(repo_script_path, 'r') as f1, open(actual_script_path, 'r') as f2:
                    repo_content = f1.read()
                    actual_content = f2.read()
                    
                    if repo_content == actual_content:
                        print("  Files are identical")
                    else:
                        print("  Files are different")
                        
                        # Show a diff of the first few lines
                        repo_lines = repo_content.splitlines()[:10]
                        actual_lines = actual_content.splitlines()[:10]
                        
                        print("  First few lines diff:")
                        for i in range(min(len(repo_lines), len(actual_lines))):
                            if repo_lines[i] != actual_lines[i]:
                                print(f"    Repo: {repo_lines[i]}")
                                print(f"    Actual: {actual_lines[i]}")
            except Exception as e:
                print(f"  Error comparing files: {str(e)}")

def check_import_paths():
    """Check Python import paths"""
    print("\nChecking Python import paths:")
    print(f"sys.path: {sys.path}")
    
    # Check if important directories are in the path
    important_dirs = [
        '/home/ubuntu/repos/nitterlocal',
        '/home/ubuntu/nitterlocal',
        '/home/ubuntu/repos/nitterlocal/scripts',
        '/home/ubuntu/nitterlocal/scripts'
    ]
    
    for dir_path in important_dirs:
        if dir_path in sys.path:
            print(f"  {dir_path} is in sys.path")
        else:
            print(f"  {dir_path} is NOT in sys.path")

def check_database_paths():
    """Check database paths"""
    print("\nChecking database paths:")
    
    # Database paths to check
    db_paths = [
        '/home/ubuntu/repos/nitterlocal/data/local_database.db',
        '/home/ubuntu/nitterlocal/data/local_database.db'
    ]
    
    for db_path in db_paths:
        exists = os.path.exists(db_path)
        print(f"  {db_path} exists: {exists}")
        
        if exists:
            size = os.path.getsize(db_path)
            print(f"  Size: {size} bytes")
            
            # Try to connect to the database
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                print(f"  Tables: {[table[0] for table in tables]}")
                
                # Check row counts
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  {table_name} row count: {count}")
                
                conn.close()
            except Exception as e:
                print(f"  Error connecting to database: {str(e)}")

def main():
    """Main function"""
    print("=== Path Check Tool ===")
    
    # Check script paths
    check_script_paths()
    
    # Check import paths
    check_import_paths()
    
    # Check database paths
    check_database_paths()

if __name__ == "__main__":
    main()
