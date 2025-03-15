#!/usr/bin/env python3
"""
Combined MySQL synchronization script for nitterlocal.

This script synchronizes data from the local SQLite database to the MySQL database.
It handles both kol_character and url_tracking tables.
"""

import os
import sys
import time
import logging
import argparse
import sqlite3
import mysql.connector
import subprocess
from datetime import datetime
import dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
dotenv.load_dotenv()

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        # Get MySQL connection parameters from environment variables
        mysql_host = os.getenv('MYSQL_HOST', '43.135.26.222')
        mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
        mysql_user = os.getenv('MYSQL_USER', 'root')
        mysql_password = os.getenv('MYSQL_PASSWORD', '')
        mysql_database = os.getenv('MYSQL_DATABASE', 'kol_info')
        
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {str(e)}")
        raise

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

def sync_kol_character(sqlite_conn, mysql_conn, test_mode=False):
    """Synchronize kol_character table from SQLite to MySQL"""
    try:
        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM kol_character")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logging.info("No kol_character data to synchronize")
            return 0
        
        # Prepare MySQL cursor
        mysql_cursor = mysql_conn.cursor()
        
        # Get column names from SQLite
        columns = [column[0] for column in sqlite_cursor.description]
        
        # Count of processed records
        processed_count = 0
        
        # Process each row
        for row in rows:
            # Convert row to dict
            row_dict = dict(zip(columns, row))
            
            # Check if record already exists in MySQL
            mysql_cursor.execute(
                "SELECT COUNT(*) FROM kol_character WHERE kol_id = %s",
                (row_dict['kol_id'],)
            )
            count = mysql_cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record
                update_query = f"""
                UPDATE kol_character SET
                    kol_screen_name = %s,
                    bio = %s,
                    lore = %s,
                    knowledge = %s,
                    postExamples = %s,
                    topics = %s,
                    style_all = %s,
                    style_chat = %s,
                    style_post = %s,
                    adjectives = %s
                WHERE kol_id = %s
                """
                
                update_params = (
                    row_dict['kol_screen_name'],
                    row_dict['bio'],
                    row_dict['lore'],
                    row_dict['knowledge'],
                    row_dict['postExamples'],
                    row_dict['topics'],
                    row_dict['style_all'],
                    row_dict['style_chat'],
                    row_dict['style_post'],
                    row_dict['adjectives'],
                    row_dict['kol_id']
                )
                
                if not test_mode:
                    mysql_cursor.execute(update_query, update_params)
                
                logging.info(f"Updated kol_character record for kol_id: {row_dict['kol_id']}")
            else:
                # Insert new record
                insert_query = f"""
                INSERT INTO kol_character (
                    kol_id, kol_screen_name, bio, lore, knowledge, postExamples,
                    topics, style_all, style_chat, style_post, adjectives
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                insert_params = (
                    row_dict['kol_id'],
                    row_dict['kol_screen_name'],
                    row_dict['bio'],
                    row_dict['lore'],
                    row_dict['knowledge'],
                    row_dict['postExamples'],
                    row_dict['topics'],
                    row_dict['style_all'],
                    row_dict['style_chat'],
                    row_dict['style_post'],
                    row_dict['adjectives']
                )
                
                if not test_mode:
                    mysql_cursor.execute(insert_query, insert_params)
                
                logging.info(f"Inserted new kol_character record for kol_id: {row_dict['kol_id']}")
            
            processed_count += 1
        
        # Commit changes
        if not test_mode:
            mysql_conn.commit()
        
        logging.info(f"Synchronized {processed_count} kol_character records to MySQL")
        return processed_count
    
    except Exception as e:
        logging.error(f"Error synchronizing kol_character: {str(e)}")
        if not test_mode:
            mysql_conn.rollback()
        raise

def sync_url_tracking(sqlite_conn, mysql_conn, test_mode=False):
    """Synchronize url_tracking table from SQLite to MySQL (kol_info table)
    
    Note: This function maps SQLite's url_tracking.user_id to MySQL's kol_info.kol_id
    """
    try:
        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM url_tracking")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logging.info("No url_tracking data to synchronize")
            return 0
        
        # Prepare MySQL cursor
        mysql_cursor = mysql_conn.cursor()
        
        # Get column names from SQLite
        columns = [column[0] for column in sqlite_cursor.description]
        
        # Count of processed records
        processed_count = 0
        
        # Process each row
        for row in rows:
            # Convert row to dict
            row_dict = dict(zip(columns, row))
            
            # Skip rows with no user_id
            if not row_dict.get('user_id'):
                logging.warning(f"Skipping row with no user_id: {row_dict.get('url', 'unknown')}")
                continue
            
            # Check if record already exists in MySQL
            # Note: MySQL uses kol_id column while SQLite uses user_id
            mysql_cursor.execute(
                "SELECT COUNT(*) FROM kol_info WHERE kol_id = %s",
                (row_dict['user_id'],)  # Use user_id from SQLite as kol_id in MySQL
            )
            count = mysql_cursor.fetchone()[0]
            
            # Get Twitter handle from URL if available
            twitter_handle = None
            url = row_dict.get('url', '')
            if url and 'twitter.com/' in url:
                parts = url.split('twitter.com/')
                if len(parts) > 1:
                    twitter_handle = parts[1].split('/')[0].split('?')[0]
            
            if count > 0:
                # Update existing record
                update_query = f"""
                UPDATE kol_info SET
                    kol_screen_name = %s,
                    updated_at = %s
                WHERE kol_id = %s
                """
                
                update_params = (
                    twitter_handle or '',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    row_dict['user_id']
                )
                
                if not test_mode:
                    mysql_cursor.execute(update_query, update_params)
                
                logging.info(f"Updated kol_info record for kol_id: {row_dict['user_id']}")
            else:
                # Insert new record
                insert_query = f"""
                INSERT INTO kol_info (
                    kol_id, kol_screen_name, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s
                )
                """
                
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                insert_params = (
                    row_dict['user_id'],
                    twitter_handle or '',
                    current_time,
                    current_time
                )
                
                if not test_mode:
                    mysql_cursor.execute(insert_query, insert_params)
                
                logging.info(f"Inserted new kol_info record for kol_id: {row_dict['user_id']}")
            
            processed_count += 1
        
        # Commit changes
        if not test_mode:
            mysql_conn.commit()
        
        logging.info(f"Synchronized {processed_count} url_tracking records to MySQL")
        return processed_count
    
    except Exception as e:
        logging.error(f"Error synchronizing url_tracking: {str(e)}")
        if not test_mode:
            mysql_conn.rollback()
        raise

def sync_tweets(sqlite_conn, mysql_conn, test_mode=False, since_days=None):
    """Synchronize tweets from SQLite to MySQL using the fixed_update_mysql_kol_tweet.py script"""
    try:
        # Build the command
        cmd = ["python3", "scripts/database/fixed_update_mysql_kol_tweet.py"]
        
        if test_mode:
            cmd.append("--test")
        
        if since_days:
            cmd.extend(["--since-days", str(since_days)])
        
        # Run the command
        logging.info("Starting tweet synchronization")
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            check=False,  # Don't raise exception on non-zero return code
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        logging.info(f"Tweet synchronization completed in {time.time() - start_time:.2f} seconds")
        logging.info(f"Output: {result.stdout}")
        
        if result.stderr:
            logging.warning(f"Errors: {result.stderr}")
        
        return result.returncode == 0
    
    except Exception as e:
        logging.error(f"Error synchronizing tweets: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize SQLite data to MySQL')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    parser.add_argument('--since-days', type=int, default=1, help='Synchronize data from the last N days')
    parser.add_argument('--tweets-only', action='store_true', help='Only synchronize tweets')
    args = parser.parse_args()
    
    try:
        # Connect to databases
        sqlite_conn = get_sqlite_connection(args.db_path)
        
        # Try to connect to MySQL, but continue with test mode if it fails
        mysql_conn = None
        try:
            mysql_conn = get_mysql_connection()
        except Exception as e:
            if not args.test:
                logging.error(f"Error connecting to MySQL: {str(e)}")
                return 1
            else:
                logging.warning(f"MySQL connection failed, but continuing in test mode: {str(e)}")
        
        # Initialize counters
        kol_character_count = 0
        url_tracking_count = 0
        tweets_synced = False
        
        # Synchronize data (skip if tweets-only is specified)
        if not args.tweets_only and mysql_conn:
            kol_character_count = sync_kol_character(sqlite_conn, mysql_conn, args.test)
            url_tracking_count = sync_url_tracking(sqlite_conn, mysql_conn, args.test)
        
        # Synchronize tweets (always do this)
        tweets_synced = sync_tweets(sqlite_conn, mysql_conn, args.test, args.since_days)
        
        # Close connections
        sqlite_conn.close()
        if mysql_conn:
            mysql_conn.close()
        
        logging.info(f"Synchronization completed")
        if not args.tweets_only:
            logging.info(f"Synchronized {kol_character_count} kol_character records")
            logging.info(f"Synchronized {url_tracking_count} url_tracking records")
        logging.info(f"Tweets synchronization {'succeeded' if tweets_synced else 'failed'}")
        
        return 0
    
    except Exception as e:
        logging.error(f"Error in synchronization: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
