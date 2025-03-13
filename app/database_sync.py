"""
Module for database synchronization between SQLite and MySQL.
This module provides functions to synchronize data between SQLite and MySQL databases.
"""

import os
import sys
import logging
import sqlite3
import subprocess
import pandas as pd
try:
    import mysql.connector
except ImportError:
    pass  # Will be handled in the sync function
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Default paths
DEFAULT_SQLITE_PATH = '/home/ubuntu/nitterlocal/data/local_database.db'
DEFAULT_EXCEL_PATH = '/tmp/uploaded_excel.xlsx'

# Ensure the database directory exists
os.makedirs(os.path.dirname(DEFAULT_SQLITE_PATH), exist_ok=True)

def extract_twitter_handle(url: str) -> Optional[str]:
    """Extract Twitter handle from a URL (works with both twitter.com and x.com)"""
    if not url:
        return None
    
    try:
        # Remove trailing slash if present
        if url.endswith('/'):
            url = url[:-1]
        
        # Extract the handle from the URL
        parts = url.split('/')
        if len(parts) < 4:
            logging.warning(f"Invalid URL format: {url}")
            return None
        
        handle = parts[-1]
        return handle.lower()
    except Exception as e:
        logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
        return None

def run_process_excel_script(excel_path: str, db_path: str = DEFAULT_SQLITE_PATH) -> Dict[str, Any]:
    """Run the process_excel.py script to process an Excel file"""
    try:
        # Make sure the script is executable
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'database', 'process_excel.py')
        os.chmod(script_path, 0o755)
        
        # Run the script
        cmd = [
            'python3',
            script_path,
            '--excel', excel_path,
            '--db-path', db_path
        ]
        
        logging.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Parse the output to get the number of processed rows
        processed_count = 0
        for line in result.stdout.splitlines():
            if "Processed" in line and "rows from Excel file" in line:
                try:
                    processed_count = int(line.split("Processed")[1].split("rows")[0].strip())
                except:
                    pass
        
        return {
            "success": True,
            "processed_count": processed_count,
            "output": result.stdout,
            "errors": result.stderr
        }
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running process_excel.py: {e}")
        return {
            "success": False,
            "processed_count": 0,
            "output": e.stdout if hasattr(e, 'stdout') else "",
            "errors": e.stderr if hasattr(e, 'stderr') else str(e)
        }
    except Exception as e:
        logging.error(f"Error running process_excel.py: {e}")
        return {
            "success": False,
            "processed_count": 0,
            "output": "",
            "errors": str(e)
        }

def run_sync_kol_character_script(db_path: str = DEFAULT_SQLITE_PATH, limit: Optional[int] = None, test: bool = False) -> Dict[str, Any]:
    """Run the sync_kol_character.py script to synchronize data with MySQL"""
    try:
        # Make sure the script is executable
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'sync', 'sync_kol_character.py')
        os.chmod(script_path, 0o755)
        
        # Run the script
        cmd = [
            'python3',
            script_path,
            '--db-path', db_path
        ]
        
        if limit:
            cmd.extend(['--limit', str(limit)])
        
        if test:
            cmd.append('--test')
        
        logging.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Parse the output to get the number of processed records
        processed_count = 0
        for line in result.stdout.splitlines():
            if "Processed" in line and "KOL characters" in line:
                try:
                    processed_count = int(line.split("Processed")[1].split("KOL")[0].strip())
                except:
                    pass
        
        return {
            "success": True,
            "processed_count": processed_count,
            "output": result.stdout,
            "errors": result.stderr
        }
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running sync_kol_character.py: {e}")
        return {
            "success": False,
            "processed_count": 0,
            "output": e.stdout if hasattr(e, 'stdout') else "",
            "errors": e.stderr if hasattr(e, 'stderr') else str(e)
        }
    except Exception as e:
        logging.error(f"Error running sync_kol_character.py: {e}")
        return {
            "success": False,
            "processed_count": 0,
            "output": "",
            "errors": str(e)
        }

def get_sqlite_kol_character_stats(db_path: str = DEFAULT_SQLITE_PATH) -> Dict[str, Any]:
    """Get statistics about the kol_character table in SQLite"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kol_character'")
        if not cursor.fetchone():
            conn.close()
            return {
                "exists": False,
                "count": 0,
                "sample_data": []
            }
        
        # Get the count
        cursor.execute("SELECT COUNT(*) FROM kol_character")
        count = cursor.fetchone()[0]
        
        # Get a sample of the data
        cursor.execute("SELECT * FROM kol_character LIMIT 5")
        columns = [column[0] for column in cursor.description]
        sample_data = []
        
        for row in cursor.fetchall():
            sample_data.append(dict(zip(columns, row)))
        
        conn.close()
        
        return {
            "exists": True,
            "count": count,
            "sample_data": sample_data
        }
    except Exception as e:
        logging.error(f"Error getting kol_character stats: {e}")
        return {
            "exists": False,
            "count": 0,
            "sample_data": [],
            "error": str(e)
        }

def get_sqlite_url_tracking_stats(db_path: str = DEFAULT_SQLITE_PATH) -> Dict[str, Any]:
    """Get statistics about the url_tracking table in SQLite"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
        if not cursor.fetchone():
            conn.close()
            return {
                "exists": False,
                "count": 0,
                "sample_data": []
            }
        
        # Get the count
        cursor.execute("SELECT COUNT(*) FROM url_tracking")
        count = cursor.fetchone()[0]
        
        # Get a sample of the data
        cursor.execute("SELECT url, type, subtype, user_id FROM url_tracking LIMIT 5")
        columns = [column[0] for column in cursor.description]
        sample_data = []
        
        for row in cursor.fetchall():
            sample_data.append(dict(zip(columns, row)))
        
        conn.close()
        
        return {
            "exists": True,
            "count": count,
            "sample_data": sample_data
        }
    except Exception as e:
        logging.error(f"Error getting url_tracking stats: {e}")
        return {
            "exists": False,
            "count": 0,
            "sample_data": [],
            "error": str(e)
        }

def process_excel_and_sync(excel_path: str, db_path: str = DEFAULT_SQLITE_PATH, sync_to_mysql: bool = True, test_mode: bool = True) -> Dict[str, Any]:
    """Process an Excel file and synchronize data with MySQL"""
    results: Dict[str, Any] = {
        "excel_processing": None,
        "kol_character_sync": None,
        "sqlite_kol_character_stats": None,
        "sqlite_url_tracking_stats": None
    }
    
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        # Process the Excel file
        results["excel_processing"] = run_process_excel_script(excel_path, db_path)
    except Exception as e:
        logging.error(f"Error processing Excel file: {str(e)}")
        results["excel_processing"] = {"success": False, "processed_count": 0, "output": "", "errors": str(e)}
    
    try:
        # Get statistics about the kol_character table
        results["sqlite_kol_character_stats"] = get_sqlite_kol_character_stats(db_path)
    except Exception as e:
        logging.error(f"Error getting kol_character stats: {str(e)}")
        results["sqlite_kol_character_stats"] = {"exists": False, "count": 0, "sample_data": [], "error": str(e)}
    
    try:
        # Get statistics about the url_tracking table
        results["sqlite_url_tracking_stats"] = get_sqlite_url_tracking_stats(db_path)
    except Exception as e:
        logging.error(f"Error getting url_tracking stats: {str(e)}")
        results["sqlite_url_tracking_stats"] = {"exists": False, "count": 0, "sample_data": [], "error": str(e)}
    
    # Synchronize data with MySQL if requested
    if sync_to_mysql:
        try:
            results["kol_character_sync"] = run_sync_kol_character_script(db_path, test=test_mode)
        except Exception as e:
            logging.error(f"Error syncing kol_character: {str(e)}")
            results["kol_character_sync"] = {"success": False, "processed_count": 0, "output": "", "errors": str(e)}
    
    return results
