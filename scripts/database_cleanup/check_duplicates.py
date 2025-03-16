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
from datetime import datetime

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
        
        # Get tweet counts for each user_id
        cursor.execute("""
            SELECT user_id, COUNT(*) as tweet_count
            FROM tweets
            WHERE user_id IS NOT NULL
            GROUP BY user_id
        """)
        
        user_id_tweet_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Check which duplicate records have user_ids in active_user_ids
        for duplicate in duplicate_details:
            screen_name = duplicate['screen_name']
            records = duplicate['records']
            
            logging.info(f"Checking active user_ids for screen_name: {screen_name}")
            
            for i, record in enumerate(records):
                url, user_id, _, status, tweet_count, type_val = record
                
                if user_id in active_user_ids:
                    tweet_count_in_tweets = user_id_tweet_counts.get(user_id, 0)
                    logging.info(f"  Record {i+1}: user_id={user_id} is ACTIVE in tweets table with {tweet_count_in_tweets} tweets")
                else:
                    logging.info(f"  Record {i+1}: user_id={user_id} is NOT active in tweets table")
        
        conn.close()
        return active_user_ids, user_id_tweet_counts
    
    except Exception as e:
        logging.error(f"Error checking dynamic update user_ids: {str(e)}")
        return set(), {}

def suggest_records_to_keep(duplicate_details, active_user_ids=None, user_id_tweet_counts=None):
    """Suggest which records to keep based on status, tweet_count, type, and active user_ids"""
    suggestions = []
    
    for duplicate in duplicate_details:
        screen_name = duplicate['screen_name']
        records = duplicate['records']
        
        # Create a list to store records with their priority scores
        scored_records = []
        
        for i, record in enumerate(records):
            url, user_id, _, status, tweet_count, type_val = record
            
            # Initialize score components
            score_components = {
                'active_user_id': 0,
                'active_status': 0,
                'tweets_in_tweets_table': 0,
                'tweet_count_in_url_tracking': 0,
                'user_type': 0
            }
            
            # 1. User ID is active in tweets table
            if active_user_ids and user_id in active_user_ids:
                score_components['active_user_id'] = 100  # Highest priority
                
                # Add tweet count from tweets table
                if user_id_tweet_counts:
                    score_components['tweets_in_tweets_table'] = user_id_tweet_counts.get(user_id, 0)
            
            # 2. Active status
            if status == 'active':
                score_components['active_status'] = 50
            
            # 3. Tweet count in url_tracking
            try:
                score_components['tweet_count_in_url_tracking'] = int(tweet_count or 0)
            except (ValueError, TypeError):
                score_components['tweet_count_in_url_tracking'] = 0
            
            # 4. Type (user type preferred)
            if type_val == 'user':
                score_components['user_type'] = 10
            
            # Calculate total score
            total_score = (
                score_components['active_user_id'] * 1000 +  # Highest weight
                score_components['active_status'] * 100 +
                score_components['tweets_in_tweets_table'] * 10 +
                score_components['tweet_count_in_url_tracking'] * 1 +
                score_components['user_type'] * 0.1  # Lowest weight
            )
            
            scored_records.append({
                'index': i,
                'record': record,
                'score': total_score,
                'score_components': score_components
            })
        
        # Sort records by total score (descending)
        sorted_records = sorted(scored_records, key=lambda x: x['score'], reverse=True)
        
        # Get the record to keep (highest score)
        keep_record_data = sorted_records[0]
        keep_idx = keep_record_data['index']
        keep_record = keep_record_data['record']
        score_components = keep_record_data['score_components']
        
        # Build detailed reason
        reason_parts = []
        
        # Check if user_id is active
        if score_components['active_user_id'] > 0:
            reason_parts.append(f"Active user_id: {keep_record[1]}")
            
            # Add tweet count from tweets table if available
            if score_components['tweets_in_tweets_table'] > 0:
                reason_parts.append(f"Tweets in tweets table: {score_components['tweets_in_tweets_table']}")
        
        # Add status
        reason_parts.append(f"Status: {keep_record[3]}")
        
        # Add tweet count from url_tracking
        reason_parts.append(f"Tweet count in url_tracking: {keep_record[4]}")
        
        # Add type
        reason_parts.append(f"Type: {keep_record[5]}")
        
        # Join all reasons
        reason = ", ".join(reason_parts)
        
        suggestions.append({
            'screen_name': screen_name,
            'keep_idx': keep_idx,
            'keep_record': keep_record,
            'reason': reason,
            'score': keep_record_data['score'],
            'score_components': score_components
        })
        
        # Log detailed information
        logging.info(f"For screen_name {screen_name}, suggest keeping record {keep_idx+1}:")
        logging.info(f"  URL: {keep_record[0]}")
        logging.info(f"  User ID: {keep_record[1]}")
        logging.info(f"  Score: {keep_record_data['score']}")
        logging.info(f"  Score components: {score_components}")
        logging.info(f"  Reason: {reason}")
    
    return suggestions

def generate_sql_fix(db_path, suggestions, args=None):
    """Generate SQL to fix duplicate screen_names
    
    Args:
        db_path (str): Path to the SQLite database
        suggestions (list): List of suggestions for records to keep
        args (argparse.Namespace, optional): Command-line arguments
        
    Returns:
        str: Path to the generated SQL file, or None if an error occurred
    """
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        sql_statements = []
        
        # Add header with timestamp and explanation
        sql_statements.append(f"""-- Generated by check_duplicates.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- This script fixes duplicate screen_names in the url_tracking table
-- It keeps one record for each screen_name and deletes the others
-- IMPORTANT: Make a backup of your database before running this script!
-- Example: sqlite3 {db_path} ".backup {os.path.basename(db_path)}.bak"

BEGIN TRANSACTION;

-- First, create a backup of the url_tracking table
CREATE TABLE IF NOT EXISTS url_tracking_backup_before_fix AS SELECT * FROM url_tracking;
""")
        
        # Add a summary of what will be fixed
        if suggestions:
            sql_statements.append(f"""
-- Summary of fixes to be applied:
-- Total duplicate screen_names to fix: {len(suggestions)}
--
-- screen_name | URL to keep | user_id to keep | Reason
-- ---------------------------------------------------------------------------""")
            
            for suggestion in suggestions:
                screen_name = suggestion['screen_name']
                keep_record = suggestion['keep_record']
                keep_url = keep_record[0]
                keep_user_id = keep_record[1] or 'NULL'
                reason = suggestion['reason'].replace('\n', ' ')
                
                sql_statements.append(f"-- {screen_name} | {keep_url} | {keep_user_id} | {reason}")
            
            sql_statements.append("-- ---------------------------------------------------------------------------\n")
        
        # Generate SQL for each duplicate
        for suggestion in suggestions:
            screen_name = suggestion['screen_name']
            keep_record = suggestion['keep_record']
            keep_url = keep_record[0]
            keep_user_id = keep_record[1] or 'NULL'
            
            # Escape single quotes in strings
            screen_name_escaped = screen_name.replace("'", "''")
            keep_url_escaped = keep_url.replace("'", "''")
            
            # Get the count of records to be deleted
            cursor.execute("""
                SELECT COUNT(*) 
                FROM url_tracking 
                WHERE screen_name = ? AND url != ?
            """, (screen_name, keep_url))
            
            delete_count = cursor.fetchone()[0]
            
            # Generate SQL to delete other records with the same screen_name
            sql = f"""
-- Fix for duplicate screen_name: {screen_name}
-- Keeping record with URL: {keep_url}
-- User ID: {keep_user_id}
-- Reason: {suggestion['reason']}
-- This will delete {delete_count} record(s)

-- First, show what will be deleted (for verification)
SELECT 'Records to be deleted for {screen_name_escaped}:' as message;
SELECT url, user_id, status, tweet_count, type 
FROM url_tracking 
WHERE screen_name = '{screen_name_escaped}' 
AND url != '{keep_url_escaped}';

-- Then delete the duplicate records
DELETE FROM url_tracking 
WHERE screen_name = '{screen_name_escaped}' 
AND url != '{keep_url_escaped}';
"""
            sql_statements.append(sql)
        
        # Add verification queries and commit transaction
        sql_statements.append("""
-- Verify no duplicates remain
SELECT 'Verification: Checking for remaining duplicates...' as message;
SELECT screen_name, COUNT(*) as count
FROM url_tracking
WHERE screen_name IS NOT NULL
GROUP BY screen_name
HAVING COUNT(*) > 1;

-- If the above query returns no rows, then all duplicates have been fixed

COMMIT;

-- To rollback changes if needed, run:
-- BEGIN;
-- DROP TABLE IF EXISTS url_tracking;
-- ALTER TABLE url_tracking_backup_before_fix RENAME TO url_tracking;
-- COMMIT;
""")
        
        # Write SQL to file
        output_dir = args.output_dir if args.output_dir else os.path.dirname(db_path)
        output_file = args.output_file if args.output_file else 'fix_duplicates.sql'
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        sql_file_path = os.path.join(output_dir, output_file)
        with open(sql_file_path, 'w') as f:
            f.write('\n'.join(sql_statements))
        
        logging.info(f"Generated SQL fix script: {sql_file_path}")
        logging.info(f"To apply fixes, run: sqlite3 {db_path} < {sql_file_path}")
        logging.info(f"To view the SQL without executing it: cat {sql_file_path}")
        logging.info(f"To backup the database before applying fixes: sqlite3 {db_path} '.backup {os.path.basename(db_path)}.bak'")
        
        conn.close()
        return sql_file_path
    
    except Exception as e:
        logging.error(f"Error generating SQL fix: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Check for duplicate screen_names in url_tracking table and generate SQL fixes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check for duplicates
  python check_duplicates.py --db-path ./data/local_database.db
  
  # Generate SQL fix script
  python check_duplicates.py --db-path ./data/local_database.db --generate-fix
  
  # Ignore active tweets when prioritizing records
  python check_duplicates.py --db-path ./data/local_database.db --generate-fix --ignore-active-tweets
  
  # Enable verbose logging
  python check_duplicates.py --db-path ./data/local_database.db --verbose
"""
    )
    
    parser.add_argument(
        '--db-path', 
        type=str, 
        default='./data/local_database.db', 
        help='Path to the SQLite database (default: ./data/local_database.db)'
    )
    
    parser.add_argument(
        '--generate-fix', 
        action='store_true', 
        help='Generate SQL script to fix duplicates (creates fix_duplicates.sql in the database directory)'
    )
    
    parser.add_argument(
        '--ignore-active-tweets', 
        action='store_true', 
        help='Ignore active tweets when prioritizing records (use only url_tracking table data)'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose logging for detailed information'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directory to save the SQL fix script (default: same directory as the database)'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        default='fix_duplicates.sql',
        help='Filename for the SQL fix script (default: fix_duplicates.sql)'
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check duplicates
    duplicate_details = check_duplicates(args.db_path)
    
    if not duplicate_details:
        logging.info("No duplicate screen_names found. Database is clean.")
        return
    
    # Check kol_character
    check_kol_character(args.db_path, duplicate_details)
    
    # Check dynamic update user_ids
    active_user_ids, user_id_tweet_counts = check_dynamic_update_user_ids(args.db_path, duplicate_details)
    
    # Suggest records to keep
    if args.ignore_active_tweets:
        logging.info("Ignoring active tweets when prioritizing records")
        suggestions = suggest_records_to_keep(duplicate_details)
    else:
        suggestions = suggest_records_to_keep(duplicate_details, active_user_ids, user_id_tweet_counts)
    
    # Generate SQL fix
    if args.generate_fix:
        sql_file_path = generate_sql_fix(args.db_path, suggestions, args)
        if sql_file_path:
            logging.info(f"To fix duplicates, run: sqlite3 {args.db_path} < {sql_file_path}")
            
    # Print summary
    logging.info(f"Summary: Found {len(duplicate_details)} duplicate screen_names")
    for suggestion in suggestions:
        screen_name = suggestion['screen_name']
        keep_record = suggestion['keep_record']
        logging.info(f"  {screen_name}: Keep URL {keep_record[0]} with user_id {keep_record[1]}")
        logging.info(f"    Reason: {suggestion['reason']}")
        if 'score' in suggestion:
            logging.info(f"    Score: {suggestion['score']}")
            
    # Return success
    return True

if __name__ == "__main__":
    main()
