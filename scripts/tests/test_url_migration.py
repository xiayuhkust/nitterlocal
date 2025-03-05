#!/usr/bin/env python3
"""
Test script to verify URL migration.
This script checks that all URLs in the database have been converted to Twitter format.
"""

import os
import sys
import logging
import sqlite3
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def verify_urls(db_path='data/local_database.db'):
    """Verify that all URLs in the database are in Twitter format"""
    logging.info(f"Verifying URLs in database at {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check URL format in url_tracking table
        cursor.execute("SELECT COUNT(*) FROM url_tracking WHERE url LIKE '%nitter.net%'")
        nitter_url_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM url_tracking WHERE url LIKE '%twitter.com%'")
        twitter_url_count = cursor.fetchone()[0]
        
        # Check URL format in tweets table
        cursor.execute("SELECT COUNT(*) FROM tweets WHERE source_url LIKE '%nitter.net%'")
        nitter_source_url_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tweets WHERE source_url LIKE '%twitter.com%'")
        twitter_source_url_count = cursor.fetchone()[0]
        
        conn.close()
        
        logging.info(f"URL tracking table: {nitter_url_count} nitter URLs, {twitter_url_count} Twitter URLs")
        logging.info(f"Tweets table: {nitter_source_url_count} nitter source URLs, {twitter_source_url_count} Twitter source URLs")
        
        if nitter_url_count > 0 or nitter_source_url_count > 0:
            logging.error("Migration incomplete: Nitter URLs still exist in the database")
            return False
        
        logging.info("Migration successful: All URLs have been converted to Twitter format")
        return True
        
    except Exception as e:
        logging.error(f"Error verifying URLs: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Verify URL migration')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the database')
    
    args = parser.parse_args()
    
    if verify_urls(args.db_path):
        logging.info("URL verification completed successfully")
        return 0
    else:
        logging.error("URL verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
