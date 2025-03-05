#!/usr/bin/env python3
"""
Migration script to convert nitter URLs to Twitter URLs in the database.
This script updates all URLs in the url_tracking table and corresponding source_url values in the tweets table.
"""

import os
import sys
import logging
import sqlite3
import argparse
from urllib.parse import urlparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def convert_nitter_to_twitter(url):
    """Convert a nitter URL to a Twitter URL"""
    if not url or 'nitter.net/' not in url:
        return url
    
    try:
        # Replace nitter.net with twitter.com
        return url.replace('nitter.net/', 'twitter.com/')
    except Exception as e:
        logging.error(f"Error converting URL {url}: {str(e)}")
        return url

def migrate_database(db_path='data/local_database.db'):
    """Migrate the database to convert nitter URLs to Twitter URLs"""
    logging.info(f"Migrating database at {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Temporarily disable foreign keys to allow updates
        cursor.execute("PRAGMA foreign_keys=OFF")
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Get all URLs from the url_tracking table
            cursor.execute("SELECT url FROM url_tracking")
            urls = cursor.fetchall()
            
            url_count = 0
            for (url,) in urls:
                # Convert the URL
                new_url = convert_nitter_to_twitter(url)
                
                if url != new_url:
                    # Update the source_url in the tweets table first
                    cursor.execute("UPDATE tweets SET source_url = ? WHERE source_url = ?", (new_url, url))
                    
                    # Then update the URL in the url_tracking table
                    cursor.execute("UPDATE url_tracking SET url = ? WHERE url = ?", (new_url, url))
                    
                    url_count += 1
                    logging.info(f"Converted URL: {url} -> {new_url}")
            
            # Commit the transaction
            conn.commit()
            
            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Verify foreign key constraints
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            if fk_violations:
                logging.error(f"Foreign key violations found: {fk_violations}")
                return False
            
            logging.info(f"Successfully converted {url_count} URLs in the database")
            
        except Exception as e:
            # Rollback the transaction in case of error
            conn.rollback()
            logging.error(f"Error migrating database: {str(e)}")
            return False
        
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"Error connecting to database: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Migrate the database to convert nitter URLs to Twitter URLs')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the database')
    
    args = parser.parse_args()
    
    if migrate_database(args.db_path):
        logging.info("Database migration completed successfully")
        return 0
    else:
        logging.error("Database migration failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
