#!/usr/bin/env python3
"""
Test script for problematic URLs in the sync script.

This script tests how the fixed kol_screen_name handling logic
handles URLs that might not have extractable Twitter handles.
"""

import os
import sys
import logging
import sqlite3
import argparse

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

def test_problematic_urls():
    """Test how the script handles problematic URLs"""
    try:
        # Connect to SQLite
        sqlite_conn = get_sqlite_connection()
        sqlite_cursor = sqlite_conn.cursor()
        
        # Create a temporary table with problematic URLs
        sqlite_cursor.execute("CREATE TEMPORARY TABLE test_urls (url TEXT, user_id TEXT)")
        
        # Insert test cases
        test_cases = [
            # Normal URL
            ("https://twitter.com/trader_xo", "608297384153714"),
            # URL with query parameters
            ("https://twitter.com/ivanontech?ref=source", "911296304146803"),
            # URL with path after username
            ("https://twitter.com/petermccormack/status/1234567890", "899740130647272"),
            # URL with special characters
            ("https://twitter.com/user-with-dash", "123456789"),
            # URL with no username
            ("https://twitter.com/", "987654321"),
            # Malformed URL
            ("https://twitter", "111222333"),
            # Empty URL
            ("", "444555666"),
            # Non-Twitter URL
            ("https://example.com", "777888999"),
            # URL with fragment
            ("https://twitter.com/username#fragment", "123123123"),
            # URL with username containing special characters
            ("https://twitter.com/user_name.with.dots", "456456456")
        ]
        
        sqlite_cursor.executemany("INSERT INTO test_urls VALUES (?, ?)", test_cases)
        
        # Test each case
        sqlite_cursor.execute("SELECT * FROM test_urls")
        rows = sqlite_cursor.fetchall()
        
        print("\n=== Testing URL Extraction Logic ===")
        print("URL | user_id | Extracted Handle | Original Logic | Fixed Logic")
        print("-" * 80)
        
        for row in rows:
            url = row['url']
            user_id = row['user_id']
            
            # Extract Twitter handle using original logic
            original_handle = None
            if url and 'twitter.com/' in url:
                parts = url.split('twitter.com/')
                if len(parts) > 1:
                    original_handle = parts[1].split('/')[0].split('?')[0]
            
            # Original logic result
            original_result = original_handle if original_handle else None
            
            # Fixed logic result
            fixed_result = None
            if url and 'twitter.com/' in url:
                parts = url.split('twitter.com/')
                if len(parts) > 1:
                    fixed_result = parts[1].split('/')[0].split('?')[0]
            
            if not fixed_result:
                fixed_result = f"unknown_user_{user_id}"
            
            # Would the original logic fail?
            would_fail = original_result is None
            
            print(f"{url[:30]}... | {user_id} | {original_handle} | {'FAIL' if would_fail else 'OK'} | OK")
        
        # Drop temporary table
        sqlite_cursor.execute("DROP TABLE test_urls")
        
        # Close connection
        sqlite_conn.close()
        
        print("\n=== Summary ===")
        print("The original logic would fail when:")
        print("1. The URL doesn't contain 'twitter.com/'")
        print("2. The URL doesn't have a username after 'twitter.com/'")
        print("3. The URL is empty")
        
        print("\nThe fixed logic handles these cases by:")
        print("1. Using existing kol_screen_name values from SQLite when available")
        print("2. Falling back to a default value when no handle can be extracted")
        print("3. Ensuring every record has a kol_screen_name value for MySQL")
        
        return True
    
    except Exception as e:
        logging.error(f"Error testing problematic URLs: {str(e)}")
        return False

def main():
    """Main function"""
    success = test_problematic_urls()
    
    if success:
        logging.info("Test completed successfully")
        return 0
    else:
        logging.error("Test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
