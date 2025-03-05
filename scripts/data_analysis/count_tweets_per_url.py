#!/usr/bin/env python3
"""
Script to count tweets per URL in the database.
This script generates statistics about tweet counts per URL and outputs them in various formats.
"""

import os
import sys
import logging
import sqlite3
import json
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

def count_tweets_per_url(db_path='data/local_database.db', output_format='text', output_file=None, limit=None):
    """Count tweets per URL in the database"""
    logging.info(f"Counting tweets per URL in database at {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get tweet counts per URL
        try:
            # Try with user_id column and reply counts
            cursor.execute("""
                SELECT url_tracking.url, url_tracking.description, url_tracking.type, 
                       url_tracking.user_id, COUNT(tweets.tweet_id) as tweet_count,
                       SUM(CASE WHEN tweets.is_reply = 1 THEN 1 ELSE 0 END) as reply_count,
                       SUM(CASE WHEN tweets.is_reply = 0 OR tweets.is_reply IS NULL THEN 1 ELSE 0 END) as non_reply_count
                FROM url_tracking
                LEFT JOIN tweets ON url_tracking.url = tweets.source_url
                GROUP BY url_tracking.url
                ORDER BY tweet_count DESC
                LIMIT ?
            """, (limit or -1,))
        except sqlite3.OperationalError as e:
            if "no such column: url_tracking.user_id" in str(e):
                # Fall back to query without user_id
                cursor.execute("""
                    SELECT url_tracking.url, url_tracking.description, url_tracking.type, 
                           NULL as user_id, COUNT(tweets.tweet_id) as tweet_count,
                           0 as reply_count,
                           COUNT(tweets.tweet_id) as non_reply_count
                    FROM url_tracking
                    LEFT JOIN tweets ON url_tracking.url = tweets.source_url
                    GROUP BY url_tracking.url
                    ORDER BY tweet_count DESC
                    LIMIT ?
                """, (limit or -1,))
            elif "no such column: tweets.is_reply" in str(e):
                # Fall back to query without reply counts
                cursor.execute("""
                    SELECT url_tracking.url, url_tracking.description, url_tracking.type, 
                           url_tracking.user_id, COUNT(tweets.tweet_id) as tweet_count,
                           0 as reply_count,
                           COUNT(tweets.tweet_id) as non_reply_count
                    FROM url_tracking
                    LEFT JOIN tweets ON url_tracking.url = tweets.source_url
                    GROUP BY url_tracking.url
                    ORDER BY tweet_count DESC
                    LIMIT ?
                """, (limit or -1,))
            else:
                raise
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # Get total tweet count
        cursor.execute("SELECT COUNT(*) FROM tweets")
        total_tweets = cursor.fetchone()[0]
        
        # Get total URL count
        cursor.execute("SELECT COUNT(*) FROM url_tracking")
        total_urls = cursor.fetchone()[0]
        
        # Generate statistics
        stats = {
            'total_tweets': total_tweets,
            'total_urls': total_urls,
            'url_tweet_counts': results,
            'generated_at': datetime.now().isoformat()
        }
        
        conn.close()
        
        # Output the statistics
        if output_format == 'json':
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(stats, f, indent=2)
                logging.info(f"Statistics saved to {output_file}")
            else:
                print(json.dumps(stats, indent=2))
        else:
            print(f"Tweet Count Statistics:")
            print(f"Total URLs: {total_urls}")
            print(f"Total Tweets: {total_tweets}")
            print(f"Generated at: {stats['generated_at']}")
            print(f"\nTweet Counts per URL:")
            
            for i, result in enumerate(results):
                print(f"{i+1}. {result['url']}")
                print(f"   Description: {result['description']}")
                print(f"   Type: {result['type']}")
                print(f"   User ID: {result['user_id'] or 'N/A'}")
                print(f"   Tweet Count: {result['tweet_count']}")
                print(f"   Reply Count: {result.get('reply_count', 0)}")
                print(f"   Non-Reply Count: {result.get('non_reply_count', result['tweet_count'])}")
                print()
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(f"Tweet Count Statistics:\n")
                    f.write(f"Total URLs: {total_urls}\n")
                    f.write(f"Total Tweets: {total_tweets}\n")
                    f.write(f"Generated at: {stats['generated_at']}\n")
                    f.write(f"\nTweet Counts per URL:\n")
                    
                    for i, result in enumerate(results):
                        f.write(f"{i+1}. {result['url']}\n")
                        f.write(f"   Description: {result['description']}\n")
                        f.write(f"   Type: {result['type']}\n")
                        f.write(f"   User ID: {result['user_id'] or 'N/A'}\n")
                        f.write(f"   Tweet Count: {result['tweet_count']}\n")
                        f.write(f"   Reply Count: {result.get('reply_count', 0)}\n")
                        f.write(f"   Non-Reply Count: {result.get('non_reply_count', result['tweet_count'])}\n")
                        f.write("\n")
                
                logging.info(f"Statistics saved to {output_file}")
        
        return stats
        
    except Exception as e:
        logging.error(f"Error counting tweets per URL: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Count tweets per URL in the database')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--format', type=str, choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to display')
    
    args = parser.parse_args()
    
    # Count tweets per URL
    count_tweets_per_url(db_path=args.db_path, output_format=args.format, output_file=args.output, limit=args.limit)

if __name__ == "__main__":
    main()
