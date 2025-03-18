#!/usr/bin/env python3
"""
Store tweets script for Twitter data extraction.
This script handles the database storage of tweets extracted by separate_tweet_scraper.py.
"""

import os
import sys
import logging
import argparse
import json
import glob
import sqlite3
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/store_tweets.log"),
        logging.StreamHandler()
    ]
)

class TweetStorer:
    """Tweet storer for Twitter data extraction"""
    
    def __init__(self, db_path='data/local_database.db'):
        """Initialize the tweet storer"""
        logging.info(f"Initializing tweet storer with database at {db_path}")
        
        self.db_path = db_path
        
        logging.info("Tweet storer initialization complete")
    
    def store_tweets(self, tweets, source_url):
        """Store tweets in the database"""
        try:
            # Create a new connection in this thread
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stored_count = 0
            updated_count = 0
            hashtag_count = 0
            
            for tweet in tweets:
                try:
                    # Check if tweet already exists
                    cursor.execute("SELECT 1 FROM tweets WHERE tweet_id = ?", (tweet['tweet_id'],))
                    if cursor.fetchone():
                        # Update existing tweet's metadata
                        cursor.execute('''
                        UPDATE tweets 
                        SET likes = ?, retweets = ?, replies = ?, views = ?, user_id = ?,
                            is_reply = ?, reply_to = ?, conversation_id = ?
                        WHERE tweet_id = ?
                        ''', (
                            tweet['likes'],
                            tweet['retweets'],
                            tweet['replies'],
                            tweet['views'],
                            tweet.get('user_id'),  # Include user_id in the update
                            tweet.get('is_reply', 0),  # Include is_reply in the update
                            tweet.get('reply_to'),  # Include reply_to in the update
                            tweet.get('conversation_id'),  # Include conversation_id in the update
                            tweet['tweet_id']
                        ))
                        
                        # Delete existing hashtags for this tweet
                        cursor.execute("DELETE FROM hashtags WHERE tweet_id = ?", (tweet['tweet_id'],))
                        
                        updated_count += 1
                    else:
                        # Insert new tweet
                        cursor.execute('''
                        INSERT INTO tweets (
                            tweet_id, source_url, content, created_at, author, likes, retweets, replies, views, user_id,
                            is_reply, reply_to, conversation_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            tweet['tweet_id'],
                            source_url,
                            tweet['content'],
                            tweet['created_at'],
                            tweet['author'],
                            tweet['likes'],
                            tweet['retweets'],
                            tweet['replies'],
                            tweet['views'],
                            tweet.get('user_id'),  # Include user_id in the insert
                            tweet.get('is_reply', 0),  # Include is_reply in the insert
                            tweet.get('reply_to'),  # Include reply_to in the insert
                            tweet.get('conversation_id')  # Include conversation_id in the insert
                        ))
                        
                        stored_count += 1
                    
                    # Store hashtags for the tweet
                    if 'hashtags' in tweet and tweet['hashtags']:
                        for hashtag in tweet['hashtags']:
                            cursor.execute('''
                            INSERT INTO hashtags (tweet_id, hashtag)
                            VALUES (?, ?)
                            ''', (tweet['tweet_id'], hashtag))
                            hashtag_count += 1
                        
                except Exception as e:
                    logging.warning(f"Error storing/updating tweet {tweet['tweet_id']}: {str(e)}")
                    continue
            
            # Update the tweet count for the URL (only count new tweets, not updates)
            cursor.execute('''
            UPDATE url_tracking 
            SET tweet_count = tweet_count + ?, last_scraped = ?
            WHERE url = ?
            ''', (stored_count, datetime.now().isoformat(), source_url))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Stored {stored_count} new tweets and updated {updated_count} existing tweets for URL: {source_url}")
            
            return stored_count + updated_count
            
        except Exception as e:
            logging.error(f"Error storing tweets: {str(e)}")
            return 0
    
    def process_tweet_files(self, directory='data/tweets', processed_dir='data/tweets/processed'):
        """Process tweet files in the specified directory"""
        logging.info(f"Processing tweet files in {directory}")
        
        # Create processed directory if it doesn't exist
        os.makedirs(processed_dir, exist_ok=True)
        
        # Get all JSON files in the directory
        files = glob.glob(os.path.join(directory, '*.json'))
        logging.info(f"Found {len(files)} tweet files to process")
        
        processed_count = 0
        success_count = 0
        error_count = 0
        total_tweets = 0
        
        for file_path in files:
            try:
                logging.info(f"Processing file: {file_path}")
                
                # Load tweets from file
                with open(file_path, 'r') as f:
                    tweets = json.load(f)
                
                if not tweets:
                    logging.warning(f"No tweets found in file: {file_path}")
                    continue
                
                # Extract source URL from the first tweet
                source_url = tweets[0].get('source_url')
                if not source_url:
                    logging.warning(f"No source URL found in file: {file_path}")
                    continue
                
                # Store tweets in the database
                stored_count = self.store_tweets(tweets, source_url)
                
                if stored_count > 0:
                    logging.info(f"Stored {stored_count} tweets for URL: {source_url}")
                    success_count += 1
                    total_tweets += stored_count
                else:
                    logging.warning(f"Failed to store tweets for URL: {source_url}")
                    error_count += 1
                
                # Move file to processed directory
                processed_file = os.path.join(processed_dir, os.path.basename(file_path))
                os.rename(file_path, processed_file)
                logging.info(f"Moved file to {processed_file}")
                
                processed_count += 1
                
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {str(e)}")
                error_count += 1
        
        logging.info(f"Processed {processed_count} files, {success_count} successful, {error_count} errors")
        logging.info(f"Total tweets stored: {total_tweets}")
        
        return {
            'processed_count': processed_count,
            'success_count': success_count,
            'error_count': error_count,
            'total_tweets': total_tweets
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Store tweets in the database')
    parser.add_argument('--directory', default='data/tweets', help='Directory containing tweet files')
    parser.add_argument('--processed-dir', default='data/tweets/processed', help='Directory for processed tweet files')
    
    args = parser.parse_args()
    
    # Initialize and run the tweet storer
    storer = TweetStorer()
    result = storer.process_tweet_files(args.directory, args.processed_dir)
    
    # Print summary
    print("\nTweet Storer Summary:")
    print(f"Processed files: {result.get('processed_count', 0)}")
    print(f"Success: {result.get('success_count', 0)}")
    print(f"Errors: {result.get('error_count', 0)}")
    print(f"Total tweets stored: {result.get('total_tweets', 0)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
