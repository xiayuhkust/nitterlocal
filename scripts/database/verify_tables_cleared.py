#!/usr/bin/env python3
"""
Script to verify that tables have been cleared but structure is preserved.
"""

import os
import sys
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def verify_tables(db_path):
    """Verify that tables are empty but structure is preserved"""
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
    url_tracking_exists = cursor.fetchone() is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kol_character'")
    kol_character_exists = cursor.fetchone() is not None
    
    if not url_tracking_exists or not kol_character_exists:
        logging.error("One or more tables do not exist")
        conn.close()
        return False
    
    # Check record counts
    cursor.execute("SELECT COUNT(*) FROM url_tracking")
    url_tracking_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM kol_character")
    kol_character_count = cursor.fetchone()[0]
    
    # Get table schemas
    cursor.execute("PRAGMA table_info(url_tracking)")
    url_tracking_columns = cursor.fetchall()
    
    cursor.execute("PRAGMA table_info(kol_character)")
    kol_character_columns = cursor.fetchall()
    
    conn.close()
    
    # Print results
    logging.info(f"URL tracking table exists: {url_tracking_exists}")
    logging.info(f"KOL character table exists: {kol_character_exists}")
    logging.info(f"URL tracking record count: {url_tracking_count}")
    logging.info(f"KOL character record count: {kol_character_count}")
    
    logging.info("\nURL tracking columns:")
    for col in url_tracking_columns:
        logging.info(f"  {col[1]} ({col[2]})")
    
    logging.info("\nKOL character columns:")
    for col in kol_character_columns:
        logging.info(f"  {col[1]} ({col[2]})")
    
    # Check if tables are empty
    if url_tracking_count == 0 and kol_character_count == 0:
        logging.info("\n✅ SUCCESS: Tables are empty but structure is preserved")
        return True
    else:
        logging.error("\n❌ ERROR: Tables are not empty")
        return False

if __name__ == "__main__":
    db_path = "data/local_database.db"
    verify_tables(db_path)
