#!/usr/bin/env python3
"""
Script to remove tweets with identical content from the database.
This script identifies and removes duplicate tweets while preserving the one with the most engagement.
"""

import os
import sys
import logging
import sqlite3
import argparse
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

def remove_duplicate_tweets(db_path='data/local_database.db', dry_run=False):
    """Remove tweets with identical content from the database"""
    logging.info(f"Removing duplicate tweets from database at {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find duplicate tweets based on content
        cursor.execute("""
            SELECT content, COUNT(*) as count
            FROM tweets
            GROUP BY content
            HAVING count > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        logging.info(f"Found {len(duplicates)} groups of duplicate tweets")
        
        if dry_run:
            # Just print the duplicates
            for dup in duplicates:
                content = dup['content']
                count = dup['count']
                logging.info(f"Content: '{content[:50]}...' appears {count} times")
            
            logging.info("Dry run completed. No changes made to the database.")
            conn.close()
            return len(duplicates)
        
        # Process each group of duplicates
        total_removed = 0
        
        for dup in duplicates:
            content = dup['content']
            
            # Get all tweets with this content
            cursor.execute("""
                SELECT tweet_id, source_url, content, created_at, author, 
                       likes, retweets, replies, views, stored_at
                FROM tweets
                WHERE content = ?
                ORDER BY likes DESC, retweets DESC, replies DESC, views DESC
            """, (content,))
            
            tweets = cursor.fetchall()
            
            if len(tweets) <= 1:
                continue
            
            # Keep the tweet with the most engagement (already sorted)
            keep_tweet = tweets[0]
            remove_tweets = tweets[1:]
            
            # Log the operation
            logging.info(f"Keeping tweet {keep_tweet['tweet_id']} with {keep_tweet['likes']} likes, removing {len(remove_tweets)} duplicates")
            
            # Remove the duplicates
            for tweet in remove_tweets:
                cursor.execute("DELETE FROM tweets WHERE tweet_id = ?", (tweet['tweet_id'],))
                total_removed += 1
        
        # Update the tweet counts for each URL
        cursor.execute("""
            UPDATE url_tracking
            SET tweet_count = (
                SELECT COUNT(*)
                FROM tweets
                WHERE tweets.source_url = url_tracking.url
            )
        """)
        
        # Commit the changes
        conn.commit()
        
        # Log the operation to the backup_log table
        cursor.execute("""
            INSERT INTO backup_log (operation, details, success)
            VALUES (?, ?, ?)
        """, ('remove_duplicates', f"Removed {total_removed} duplicate tweets", 1))
        
        conn.commit()
        conn.close()
        
        logging.info(f"Removed {total_removed} duplicate tweets")
        
        return total_removed
        
    except Exception as e:
        logging.error(f"Error removing duplicate tweets: {str(e)}")
        return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Remove duplicate tweets from the database')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    
    args = parser.parse_args()
    
    # Remove duplicate tweets
    remove_duplicate_tweets(db_path=args.db_path, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
