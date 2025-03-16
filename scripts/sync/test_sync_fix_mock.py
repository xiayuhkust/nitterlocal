#!/usr/bin/env python3
"""
Mock test script for the fixed kol_character synchronization script.

This script tests the kol_screen_name handling logic without requiring
an actual MySQL connection.
"""

import os
import sys
import logging
import sqlite3
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_sqlite_connection(db_path='/home/ubuntu/nitterlocal/data/local_database.db'):
    """Get a connection to the SQLite database"""
    try:
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to SQLite: {str(e)}")
        raise

def test_kol_screen_name_logic(verbose=False):
    """Test the kol_screen_name handling logic"""
    try:
        # Connect to SQLite
        sqlite_conn = get_sqlite_connection()
        sqlite_cursor = sqlite_conn.cursor()
        
        # Check if kol_character table exists
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kol_character'")
        use_url_tracking = not sqlite_cursor.fetchone()
        
        if use_url_tracking:
            logging.info("kol_character table not found, using url_tracking table")
            sqlite_cursor.execute("SELECT * FROM url_tracking LIMIT 10")
        else:
            logging.info("Using kol_character table")
            sqlite_cursor.execute("SELECT * FROM kol_character LIMIT 10")
            
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logging.error("No data found in the table")
            return False
        
        # Get column names from SQLite
        sqlite_columns = [column[0] for column in sqlite_cursor.description]
        logging.info(f"SQLite columns: {sqlite_columns}")
        
        # Mock MySQL columns
        mysql_columns = ['id', 'kol_id', 'kol_screen_name', 'bio', 'lore', 'knowledge', 'postExamples', 'topics', 'style_all', 'style_chat', 'style_post', 'adjectives']
        logging.info(f"Mock MySQL columns: {mysql_columns}")
        
        # Process each row
        for i, row in enumerate(rows):
            # Convert row to dict
            row_dict = dict(zip(sqlite_columns, row))
            
            # For url_tracking table, extract Twitter handle from URL if available
            twitter_handle = None
            if use_url_tracking and 'url' in row_dict and row_dict.get('url') and 'twitter.com/' in row_dict.get('url', ''):
                url = row_dict.get('url', '')
                parts = url.split('twitter.com/')
                if len(parts) > 1:
                    twitter_handle = parts[1].split('/')[0].split('?')[0]
                    if verbose:
                        logging.info(f"Extracted Twitter handle {twitter_handle} from URL {url}")
            
            # Handle different column names between url_tracking and kol_character
            kol_id = row_dict.get('kol_id', row_dict.get('user_id'))
            if not kol_id:
                logging.warning(f"Skipping row with no kol_id or user_id")
                continue
            
            # Test original logic
            original_kol_screen_name = None
            if 'kol_screen_name' in mysql_columns and twitter_handle:
                original_kol_screen_name = twitter_handle
            
            # Test fixed logic
            fixed_kol_screen_name = None
            if 'kol_screen_name' in mysql_columns:
                if not use_url_tracking and 'kol_screen_name' in row_dict and row_dict['kol_screen_name']:
                    # 直接使用kol_character表中的值
                    fixed_kol_screen_name = row_dict['kol_screen_name']
                    logging.info(f"Using kol_screen_name '{row_dict['kol_screen_name']}' from SQLite kol_character table")
                elif use_url_tracking and twitter_handle:
                    # 从URL中提取的Twitter用户名
                    fixed_kol_screen_name = twitter_handle
                    logging.info(f"Using extracted Twitter handle '{twitter_handle}' for kol_screen_name")
                elif use_url_tracking and 'screen_name' in row_dict and row_dict['screen_name']:
                    # 使用url_tracking表中的screen_name字段
                    fixed_kol_screen_name = row_dict['screen_name']
                    logging.info(f"Using screen_name '{row_dict['screen_name']}' from url_tracking table")
                else:
                    # 使用默认值
                    fixed_kol_screen_name = f"unknown_user_{kol_id}"
                    logging.info(f"Using default 'unknown_user_{kol_id}' for kol_screen_name")
            
            # Compare results
            logging.info(f"Row {i+1}, kol_id: {kol_id}")
            logging.info(f"  Original logic: kol_screen_name = {original_kol_screen_name}")
            logging.info(f"  Fixed logic: kol_screen_name = {fixed_kol_screen_name}")
            
            # Check if the fix would resolve the issue
            if original_kol_screen_name is None and fixed_kol_screen_name is not None:
                logging.info(f"  FIXED: The new logic provides a value where the original logic did not")
            elif original_kol_screen_name == fixed_kol_screen_name:
                logging.info(f"  UNCHANGED: Both logics provide the same value")
            else:
                logging.info(f"  CHANGED: The new logic provides a different value")
            
            logging.info("")
        
        # Close connection
        sqlite_conn.close()
        
        return True
    
    except Exception as e:
        logging.error(f"Error testing kol_screen_name logic: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test the kol_screen_name handling logic')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    success = test_kol_screen_name_logic(args.verbose)
    
    if success:
        logging.info("Test completed successfully")
        return 0
    else:
        logging.error("Test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
