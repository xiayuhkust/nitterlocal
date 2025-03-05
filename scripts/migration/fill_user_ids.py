#!/usr/bin/env python3
"""
Migration script to fill in missing user_id values in the url_tracking table.
This script uses the agent-twitter-client library to get user IDs for Twitter usernames.
"""

import os
import sys
import logging
import sqlite3
import json
import argparse
import subprocess
import time
import re
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the database module
from src.database.local_database import LocalDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def add_user_id_column(db_path, dry_run=False):
    """Add user_id column to url_tracking table if it doesn't exist"""
    logging.info(f"Checking if user_id column exists in url_tracking table")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user_id column exists
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            logging.info("user_id column does not exist, adding it")
            
            if not dry_run:
                cursor.execute("ALTER TABLE url_tracking ADD COLUMN user_id TEXT")
                conn.commit()
                logging.info("Added user_id column to url_tracking table")
            else:
                logging.info("[DRY RUN] Would add user_id column to url_tracking table")
        else:
            logging.info("user_id column already exists")
        
        conn.close()
        
    except Exception as e:
        logging.error(f"Error adding user_id column: {str(e)}")

def extract_username_from_url(url):
    """Extract username from Twitter URL"""
    # Handle different URL formats
    patterns = [
        r'https?://(?:www\.)?twitter\.com/([^/]+)',
        r'https?://(?:www\.)?nitter\.net/([^/]+)',
        r'https?://(?:www\.)?x\.com/([^/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            username = match.group(1)
            # Remove any query parameters
            username = username.split('?')[0]
            return username
    
    return None

def get_user_id_by_username(username, twitter_client_path, temp_output_file):
    """Get user ID by username using the Twitter client"""
    try:
        # Call the Twitter client to get the user ID
        cmd = ['node', twitter_client_path, username, '1', temp_output_file]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logging.error(f"Error getting user ID for @{username}: {stderr.decode('utf-8')}")
            return None
        
        # Read the output file
        with open(temp_output_file, 'r') as f:
            data = json.load(f)
        
        # Return the user ID
        return data.get('userId')
    
    except Exception as e:
        logging.error(f"Error getting user ID for @{username}: {str(e)}")
        return None

def fill_user_ids(db_path, twitter_client_path, batch_size=10, sleep_time=2, limit=None, dry_run=False):
    """Fill in missing user_id values in the url_tracking table"""
    logging.info(f"Filling in missing user_id values in database at {db_path}")
    
    try:
        # First, add user_id column if it doesn't exist
        add_user_id_column(db_path, dry_run)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get URLs with missing user_id
        try:
            # Try to get URLs with missing user_id
            cursor.execute("""
                SELECT url, description, type FROM url_tracking 
                WHERE user_id IS NULL OR user_id = ''
                LIMIT ?
            """, (limit or -1,))
        except sqlite3.OperationalError as e:
            if "no such column: user_id" in str(e):
                # If user_id column doesn't exist, get all URLs
                cursor.execute("""
                    SELECT url, description, type FROM url_tracking
                    LIMIT ?
                """, (limit or -1,))
            else:
                raise
        
        urls = [dict(row) for row in cursor.fetchall()]
        
        if not urls:
            logging.info("No URLs with missing user_id found")
            conn.close()
            return
        
        logging.info(f"Found {len(urls)} URLs with missing user_id")
        
        # Create a temporary file for Twitter client output
        temp_output_file = os.path.join(os.path.dirname(twitter_client_path), 'temp_user_id.json')
        
        # Process URLs in batches
        updated_count = 0
        error_count = 0
        
        for i, url_data in enumerate(urls):
            url = url_data['url']
            description = url_data['description']
            url_type = url_data['type']
            
            # Extract username from URL
            username = extract_username_from_url(url)
            
            if not username:
                logging.warning(f"Could not extract username from URL: {url}")
                error_count += 1
                continue
            
            logging.info(f"Processing URL {i+1}/{len(urls)}: {url} (@{username})")
            
            # Get user ID by username
            user_id = get_user_id_by_username(username, twitter_client_path, temp_output_file)
            
            if not user_id:
                logging.warning(f"Could not get user ID for @{username}")
                error_count += 1
                continue
            
            # Update the database
            if not dry_run:
                cursor.execute("""
                    UPDATE url_tracking 
                    SET user_id = ?
                    WHERE url = ?
                """, (user_id, url))
                
                conn.commit()
                
                logging.info(f"Updated user_id for URL {url}: {user_id}")
                updated_count += 1
            else:
                logging.info(f"[DRY RUN] Would update user_id for URL {url}: {user_id}")
                updated_count += 1
            
            # Sleep between requests to avoid rate limits
            if (i + 1) % batch_size == 0 and i < len(urls) - 1:
                logging.info(f"Processed {i+1} URLs, sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
        
        conn.close()
        
        # Clean up temporary file
        if os.path.exists(temp_output_file):
            os.remove(temp_output_file)
        
        logging.info(f"Migration complete: {updated_count} URLs updated, {error_count} errors")
        
    except Exception as e:
        logging.error(f"Error filling in user_id values: {str(e)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Fill in missing user_id values in the url_tracking table')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--twitter-client', type=str, default='src/twitter_client/twitter_client.js', help='Path to the Twitter client')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of URLs to process in each batch')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between batches in seconds')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    
    args = parser.parse_args()
    
    # Fill in missing user_id values
    fill_user_ids(
        db_path=args.db_path,
        twitter_client_path=args.twitter_client,
        batch_size=args.batch_size,
        sleep_time=args.sleep,
        limit=args.limit,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
