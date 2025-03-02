#!/usr/bin/env python3
"""
Script to view tweets in the database.
This script displays tweets stored in the database.
"""

import os
import sys
import logging
import json
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the database module
from src.database.local_database import LocalDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def view_tweets(db_path='data/local_database.db', source_url=None, limit=None, output_file=None):
    """View tweets in the database"""
    logging.info(f"Viewing tweets in database at {db_path}")
    
    try:
        # Initialize the database
        db = LocalDatabase(db_path=db_path)
        
        # Get tweets
        tweets = db.get_tweets(source_url=source_url, limit=limit)
        
        logging.info(f"Found {len(tweets)} tweets in the database")
        
        # Display tweets
        for i, tweet_data in enumerate(tweets):
            print(f"{i+1}. Tweet ID: {tweet_data['tweet_id']}")
            print(f"   Author: {tweet_data['author']}")
            print(f"   Content: {tweet_data['content'][:100]}...")
            print(f"   Created at: {tweet_data['created_at']}")
            print(f"   Likes: {tweet_data['likes']}, Retweets: {tweet_data['retweets']}, Replies: {tweet_data['replies']}")
            print(f"   Source URL: {tweet_data['source_url']}")
            print()
        
        # Save tweets to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump({'tweets': tweets}, f, indent=2)
            logging.info(f"Saved tweets to {output_file}")
        
        return tweets
        
    except Exception as e:
        logging.error(f"Error viewing tweets: {str(e)}")
        return []

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='View tweets in the database')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--source-url', type=str, help='Filter tweets by source URL')
    parser.add_argument('--limit', type=int, help='Limit the number of tweets to display')
    parser.add_argument('--output', type=str, help='Save tweets to a JSON file')
    
    args = parser.parse_args()
    
    # View tweets
    view_tweets(db_path=args.db_path, source_url=args.source_url, limit=args.limit, output_file=args.output)

if __name__ == "__main__":
    main()
