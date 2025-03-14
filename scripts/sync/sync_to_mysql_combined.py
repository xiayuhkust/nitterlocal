#!/usr/bin/env python3
"""
Combined MySQL synchronization script for nitterlocal.

This script synchronizes data from the local SQLite database to the MySQL database.
It handles both kol_character and url_tracking tables.
"""

import os
import sys
import logging
import argparse
import sqlite3
import mysql.connector
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
    """Synchronize url_tracking table from SQLite to MySQL (kol_info table)"""
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
            
            # Check if record already exists in MySQL
            mysql_cursor.execute(
                "SELECT COUNT(*) FROM kol_info WHERE user_id = %s",
                (row_dict['user_id'],)
            )
            count = mysql_cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record
                update_query = f"""
                UPDATE kol_info SET
                    twitter_url = %s,
                    first_category = %s,
                    second_category = %s,
                    updated_at = %s
                WHERE user_id = %s
                """
                
                update_params = (
                    row_dict['twitter_url'],
                    row_dict['first_category'],
                    row_dict['second_category'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    row_dict['user_id']
                )
                
                if not test_mode:
                    mysql_cursor.execute(update_query, update_params)
                
                logging.info(f"Updated kol_info record for user_id: {row_dict['user_id']}")
            else:
                # Insert new record
                insert_query = f"""
                INSERT INTO kol_info (
                    user_id, twitter_url, first_category, second_category, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                """
                
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                insert_params = (
                    row_dict['user_id'],
                    row_dict['twitter_url'],
                    row_dict['first_category'],
                    row_dict['second_category'],
                    current_time,
                    current_time
                )
                
                if not test_mode:
                    mysql_cursor.execute(insert_query, insert_params)
                
                logging.info(f"Inserted new kol_info record for user_id: {row_dict['user_id']}")
            
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize SQLite data to MySQL')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db',
                        help='Path to SQLite database')
    args = parser.parse_args()
    
    try:
        # Connect to databases
        sqlite_conn = get_sqlite_connection(args.db_path)
        mysql_conn = get_mysql_connection()
        
        # Synchronize data
        kol_character_count = sync_kol_character(sqlite_conn, mysql_conn, args.test)
        url_tracking_count = sync_url_tracking(sqlite_conn, mysql_conn, args.test)
        
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()
        
        logging.info(f"Synchronization completed successfully")
        logging.info(f"Synchronized {kol_character_count} kol_character records")
        logging.info(f"Synchronized {url_tracking_count} url_tracking records")
        
        return 0
    
    except Exception as e:
        logging.error(f"Error in synchronization: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
