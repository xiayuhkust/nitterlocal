#!/usr/bin/env python3
"""
Script to check the schema of the tweets table in the SQLite database.
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

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def check_tweets_schema():
    """Check the schema of the tweets table in the SQLite database"""
    # Path to the SQLite database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the tweets table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tweets'")
        if not cursor.fetchone():
            logging.error("Tweets table does not exist in the database")
            conn.close()
            return
        
        # Get the schema of the tweets table
        cursor.execute("PRAGMA table_info(tweets)")
        columns = cursor.fetchall()
        
        logging.info("Tweets table schema:")
        for column in columns:
            logging.info(f"  {column[0]}: {column[1]} ({column[2]})")
        
        # Get a sample row from the tweets table
        cursor.execute("SELECT * FROM tweets LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            logging.info("Sample row from tweets table:")
            for i, column in enumerate(columns):
                logging.info(f"  {column[1]}: {row[i]}")
        else:
            logging.info("No rows found in tweets table")
        
        # Check if the url_tracking table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
        if not cursor.fetchone():
            logging.error("url_tracking table does not exist in the database")
            conn.close()
            return
        
        # Get the schema of the url_tracking table
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = cursor.fetchall()
        
        logging.info("url_tracking table schema:")
        for column in columns:
            logging.info(f"  {column[0]}: {column[1]} ({column[2]})")
        
        # Get a sample row from the url_tracking table
        cursor.execute("SELECT * FROM url_tracking LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            logging.info("Sample row from url_tracking table:")
            for i, column in enumerate(columns):
                logging.info(f"  {column[1]}: {row[i]}")
        else:
            logging.info("No rows found in url_tracking table")
        
        # Close the connection
        conn.close()
    except Exception as e:
        logging.error(f"Error checking tweets schema: {str(e)}")

if __name__ == "__main__":
    check_tweets_schema()
