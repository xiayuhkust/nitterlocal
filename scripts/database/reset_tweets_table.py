#!/usr/bin/env python3
"""
One-time script to clear the tweets table and refill it with 50 regular tweets and 50 reply tweets per URL.
This script will:
1. Clear all data from the tweets table
2. Fetch 50 regular tweets and 50 reply tweets for each URL in the url_tracking table
3. Store the tweets in the database with the correct user_id from the url_tracking table
"""

import os
import sys
import logging
import sqlite3
import time
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the required modules
from src.twitter_client.twitter_scraper import TwitterScraper
from src.database.local_database import LocalDatabase

def clear_tweets_table(db_path):
    """Clear all data from the tweets table"""
    logging.info("Clearing tweets table")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Clear the tweets table
        cursor.execute("DELETE FROM tweets")
        
        # Clear the hashtags table (since it references tweets)
        cursor.execute("DELETE FROM hashtags")
        
        # Reset the tweet_count in url_tracking table
        cursor.execute("UPDATE url_tracking SET tweet_count = 0")
        
        conn.commit()
        conn.close()
        
        logging.info("Tweets table cleared successfully")
        return True
    except Exception as e:
        logging.error(f"Error clearing tweets table: {str(e)}")
        return False

def reset_and_refill_tweets(max_regular_tweets=50, max_reply_tweets=50, batch_size=5, sleep_between_urls=2, limit=None):
    """Clear and refill the tweets table with regular tweets and replies"""
    logging.info(f"Starting reset and refill process with {max_regular_tweets} regular tweets and {max_reply_tweets} reply tweets per URL")
    
    # Initialize components
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')
    scraper = TwitterScraper()
    database = LocalDatabase(db_path=db_path)
    
    # Create a backup of the database before clearing
    backup_path = f"{db_path}.backup_reset_tweets_{int(datetime.now().timestamp())}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logging.info(f"Created database backup at {backup_path}")
    except Exception as e:
        logging.error(f"Error creating database backup: {str(e)}")
        if input("Continue without backup? (y/n): ").lower() != 'y':
            return False
    
    # Clear the tweets table
    if not clear_tweets_table(db_path):
        logging.error("Failed to clear tweets table. Aborting.")
        return False
    
    # Get active URLs
    urls = database.get_urls(status='active')
    
    if limit:
        urls = urls[:limit]
    
    total_urls = len(urls)
    logging.info(f"Found {total_urls} active URLs to process")
    
    # Process URLs in batches
    processed_count = 0
    success_count = 0
    error_count = 0
    total_tweets = 0
    
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i+batch_size]
        logging.info(f"Processing batch {i//batch_size + 1}/{(total_urls + batch_size - 1)//batch_size}")
        
        # Scrape the batch of URLs
        for url_data in batch:
            url = url_data['url']
            user_id = url_data['user_id']
            
            try:
                logging.info(f"Processing URL: {url}")
                
                # Scrape the URL for both regular tweets and replies
                tweets = scraper.scrape_url(url, max_tweets=max_regular_tweets, max_replies=max_reply_tweets)
                
                # Ensure user_id is set for all tweets
                if user_id:
                    for tweet in tweets:
                        if 'user_id' not in tweet or not tweet['user_id']:
                            tweet['user_id'] = user_id
                
                if tweets:
                    # Store the tweets in the database
                    stored_count = database.store_tweets(tweets, url)
                    
                    if stored_count > 0:
                        logging.info(f"Processed {stored_count} tweets for URL: {url}")
                        success_count += 1
                        total_tweets += stored_count
                    else:
                        logging.warning(f"No tweets processed for URL: {url}")
                        error_count += 1
                else:
                    logging.warning(f"No tweets found for URL: {url}")
                    error_count += 1
                
                processed_count += 1
                logging.info(f"Processed {processed_count}/{total_urls} URLs")
                
            except Exception as e:
                logging.error(f"Error processing URL {url}: {str(e)}")
                error_count += 1
                processed_count += 1
        
        # Sleep between batches
        if i + batch_size < len(urls):
            logging.info(f"Sleeping for {sleep_between_urls} seconds between batches")
            time.sleep(sleep_between_urls)
    
    # Generate statistics
    logging.info("Generating statistics")
    stats = database.generate_stats()
    
    # Log completion
    logging.info("Reset and refill completed successfully")
    logging.info(f"Processed: {processed_count}, Success: {success_count}, Errors: {error_count}")
    logging.info(f"Total tweets stored: {total_tweets}")
    
    if stats:
        logging.info(f"Total URLs in database: {stats['total_urls']}")
        logging.info(f"Total tweets in database: {stats['total_tweets']}")
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Reset and refill the tweets table with regular tweets and replies')
    parser.add_argument('--max-regular', type=int, default=50, help='Maximum number of regular tweets to fetch per URL')
    parser.add_argument('--max-replies', type=int, default=50, help='Maximum number of reply tweets to fetch per URL')
    parser.add_argument('--batch-size', type=int, default=5, help='Number of URLs to process in a batch')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between batches in seconds')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--no-clear', action='store_true', help='Skip clearing the tweets table')
    
    args = parser.parse_args()
    
    if args.no_clear:
        logging.info("Skipping clearing the tweets table")
        # Initialize components
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')
        database = LocalDatabase(db_path=db_path)
        
        # Get active URLs
        urls = database.get_urls(status='active')
        
        if args.limit:
            urls = urls[:args.limit]
        
        total_urls = len(urls)
        logging.info(f"Found {total_urls} active URLs to process")
        
        # Process URLs using the TwitterScraper and LocalDatabase
        scraper = TwitterScraper()
        
        for url_data in urls:
            url = url_data['url']
            user_id = url_data['user_id']
            
            try:
                logging.info(f"Processing URL: {url}")
                
                # Scrape the URL for both regular tweets and replies
                tweets = scraper.scrape_url(url, max_tweets=args.max_regular, max_replies=args.max_replies)
                
                # Ensure user_id is set for all tweets
                if user_id:
                    for tweet in tweets:
                        if 'user_id' not in tweet or not tweet['user_id']:
                            tweet['user_id'] = user_id
                
                if tweets:
                    # Store the tweets in the database
                    stored_count = database.store_tweets(tweets, url)
                    logging.info(f"Processed {stored_count} tweets for URL: {url}")
                else:
                    logging.warning(f"No tweets found for URL: {url}")
            
            except Exception as e:
                logging.error(f"Error processing URL {url}: {str(e)}")
    else:
        # Run the reset and refill process
        reset_and_refill_tweets(
            max_regular_tweets=args.max_regular,
            max_reply_tweets=args.max_replies,
            batch_size=args.batch_size,
            sleep_between_urls=args.sleep,
            limit=args.limit
        )

if __name__ == "__main__":
    main()
