#!/usr/bin/env python3
"""
Script to check for duplicate screen_names in url_tracking table and verify user_ids.
This script:
1. Identifies duplicate screen_names in url_tracking table
2. Compares user_ids for duplicate screen_names
3. Identifies which records should be kept based on dynamic_update.py's user_ids
"""

import sqlite3
import logging
import argparse
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_duplicates(db_path):
    """Check for duplicate screen_names in url_tracking table"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find duplicate screen_names
        cursor.execute("""
            SELECT screen_name, COUNT(*) as count
            FROM url_tracking
            WHERE screen_name IS NOT NULL
            GROUP BY screen_name
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            logging.info("No duplicate screen_names found in url_tracking table")
            conn.close()
            return []
        
        logging.info(f"Found {len(duplicates)} duplicate screen_names in url_tracking table")
        
        # Get details for each duplicate
        duplicate_details = []
        for screen_name, count in duplicates:
            cursor.execute("""
                SELECT url, user_id, screen_name, status, tweet_count, type
                FROM url_tracking
                WHERE screen_name = ?
            """, (screen_name,))
            
            records = cursor.fetchall()
            duplicate_details.append({
                'screen_name': screen_name,
                'count': count,
                'records': records
            })
            
            # Log details
            logging.info(f"Duplicate screen_name: {screen_name} ({count} records)")
            for i, record in enumerate(records):
                logging.info(f"  Record {i+1}: url={record[0]}, user_id={record[1]}, status={record[3]}, tweet_count={record[4]}, type={record[5]}")
        
        conn.close()
        return duplicate_details
    
    except Exception as e:
        logging.error(f"Error checking duplicates: {str(e)}")
        return []

def check_kol_character(db_path, duplicate_details):
    """Check kol_character table for duplicate screen_names"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for duplicate in duplicate_details:
            screen_name = duplicate['screen_name']
            
            # Check if screen_name exists in kol_character
            cursor.execute("""
                SELECT kol_id, kol_screen_name
                FROM kol_character
                WHERE kol_screen_name = ?
            """, (screen_name,))
            
            kol_records = cursor.fetchall()
            
            if kol_records:
                logging.info(f"Found {len(kol_records)} records in kol_character for screen_name: {screen_name}")
                for i, record in enumerate(kol_records):
                    logging.info(f"  KOL Record {i+1}: kol_id={record[0]}, kol_screen_name={record[1]}")
            else:
                logging.info(f"No records found in kol_character for screen_name: {screen_name}")
        
        conn.close()
    
    except Exception as e:
        logging.error(f"Error checking kol_character: {str(e)}")

def check_dynamic_update_user_ids(db_path, duplicate_details):
    """Check which user_ids are used in dynamic_update.py"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all user_ids from tweets table
        cursor.execute("""
            SELECT DISTINCT user_id
            FROM tweets
            WHERE user_id IS NOT NULL
        """)
        
        active_user_ids = set([row[0] for row in cursor.fetchall()])
        logging.info(f"Found {len(active_user_ids)} distinct user_ids in tweets table")
        
        # Check which duplicate records have user_ids in active_user_ids
        for duplicate in duplicate_details:
            screen_name = duplicate['screen_name']
            records = duplicate['records']
            
            logging.info(f"Checking active user_ids for screen_name: {screen_name}")
            
            for i, record in enumerate(records):
                url, user_id, _, status, tweet_count, type_val = record
                
                if user_id in active_user_ids:
                    logging.info(f"  Record {i+1}: user_id={user_id} is ACTIVE in tweets table")
                else:
                    logging.info(f"  Record {i+1}: user_id={user_id} is NOT active in tweets table")
        
        conn.close()
    
    except Exception as e:
        logging.error(f"Error checking dynamic update user_ids: {str(e)}")

def suggest_records_to_keep(duplicate_details):
    """Suggest which records to keep based on status, tweet_count, and type"""
    suggestions = []
    
    for duplicate in duplicate_details:
        screen_name = duplicate['screen_name']
        records = duplicate['records']
        
        # Sort records by priority: active status, higher tweet_count, type
        sorted_records = sorted(
            enumerate(records),
            key=lambda x: (
                0 if x[1][3] == 'active' else 1,  # status (active first)
                -int(x[1][4] or 0),               # tweet_count (higher first)
                0 if x[1][5] == 'user' else 1     # type (user first)
            )
        )
        
        # Get the index of the record to keep
        keep_idx = sorted_records[0][0]
        keep_record = records[keep_idx]
        
        suggestions.append({
            'screen_name': screen_name,
            'keep_idx': keep_idx,
            'keep_record': keep_record,
            'reason': f"Status: {keep_record[3]}, Tweet count: {keep_record[4]}, Type: {keep_record[5]}"
        })
        
        logging.info(f"For screen_name {screen_name}, suggest keeping record {keep_idx+1}:")
        logging.info(f"  URL: {keep_record[0]}")
        logging.info(f"  User ID: {keep_record[1]}")
        logging.info(f"  Reason: {suggestions[-1]['reason']}")
    
    return suggestions

def generate_sql_fix(db_path, suggestions):
    """Generate SQL to fix duplicate screen_names"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        sql_statements = []
        
        for suggestion in suggestions:
            screen_name = suggestion['screen_name']
            keep_record = suggestion['keep_record']
            keep_url = keep_record[0]
            
            # Generate SQL to delete other records with the same screen_name
            sql = f"""
-- Fix for duplicate screen_name: {screen_name}
-- Keeping record with URL: {keep_url}
DELETE FROM url_tracking 
WHERE screen_name = '{screen_name}' 
AND url != '{keep_url}';
"""
            sql_statements.append(sql)
        
        # Write SQL to file
        sql_file_path = os.path.join(os.path.dirname(db_path), 'fix_duplicates.sql')
        with open(sql_file_path, 'w') as f:
            f.write('\n'.join(sql_statements))
        
        logging.info(f"Generated SQL fix script: {sql_file_path}")
        
        conn.close()
        return sql_file_path
    
    except Exception as e:
        logging.error(f"Error generating SQL fix: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Check for duplicate screen_names in url_tracking table')
    parser.add_argument('--db-path', type=str, default='./data/local_database.db', help='Path to the SQLite database')
    parser.add_argument('--generate-fix', action='store_true', help='Generate SQL to fix duplicates')
    
    args = parser.parse_args()
    
    # Check duplicates
    duplicate_details = check_duplicates(args.db_path)
    
    if not duplicate_details:
        return
    
    # Check kol_character
    check_kol_character(args.db_path, duplicate_details)
    
    # Check dynamic update user_ids
    check_dynamic_update_user_ids(args.db_path, duplicate_details)
    
    # Suggest records to keep
    suggestions = suggest_records_to_keep(duplicate_details)
    
    # Generate SQL fix
    if args.generate_fix:
        sql_file_path = generate_sql_fix(args.db_path, suggestions)
        if sql_file_path:
            logging.info(f"To fix duplicates, run: sqlite3 {args.db_path} < {sql_file_path}")

if __name__ == "__main__":
    main()
