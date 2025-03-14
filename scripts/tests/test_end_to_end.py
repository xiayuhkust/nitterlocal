#!/usr/bin/env python3
"""
End-to-end test script for the Twitter client daily update process.
This script tests the entire process from start to finish.
"""

import os
import sys
import logging
import json
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/end_to_end_test.log"),
        logging.StreamHandler()
    ]
)

def setup_database():
    """Set up the database with sample URLs"""
    from src.database.local_database import LocalDatabase
    
    logging.info("Setting up database with sample URLs")
    
    # Create a database
    db_path = 'data/end_to_end_test.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = LocalDatabase(db_path=db_path)
    
    # Add sample URLs
    sample_urls = [
        ('https://twitter.com/0xPolygon', 'Polygon', 'kol'),
        ('https://twitter.com/elonmusk', 'Elon Musk', 'kol'),
        ('https://twitter.com/vitalikbuterin', 'Vitalik Buterin', 'kol')
    ]
    
    for url, description, url_type in sample_urls:
        db.add_url(url, description=description, url_type=url_type)
    
    logging.info(f"Added {len(sample_urls)} sample URLs to the database")
    
    return db_path

def run_daily_update(db_path, batch_size=2, sleep_between_urls=2, max_tweets=10, limit=None):
    """Run the daily update process"""
    from src.daily_update.daily_update import DailyUpdate
    
    logging.info("Running daily update process")
    logging.info(f"Batch size: {batch_size}, Sleep between URLs: {sleep_between_urls} seconds")
    logging.info(f"Max tweets per URL: {max_tweets}")
    
    # Initialize the daily update
    daily_update = DailyUpdate(db_path=db_path)
    
    # Run the daily update
    result = daily_update.run(
        batch_size=batch_size,
        sleep_between_urls=sleep_between_urls,
        max_tweets=max_tweets,
        limit=limit
    )
    
    logging.info(f"Daily update result: {result}")
    
    return result

def check_database(db_path):
    """Check the database for stored tweets"""
    from src.database.local_database import LocalDatabase
    
    logging.info("Checking database for stored tweets")
    
    # Initialize the database
    db = LocalDatabase(db_path=db_path)
    
    # Get all tweets
    tweets = db.get_tweets()
    logging.info(f"Found {len(tweets)} tweets in the database")
    
    # Get tweets by URL
    urls = db.get_urls()
    for url_data in urls:
        url = url_data['url']
        url_tweets = db.get_tweets(source_url=url)
        logging.info(f"Found {len(url_tweets)} tweets for URL: {url}")
    
    # Generate statistics
    stats = db.generate_stats()
    logging.info(f"Statistics: {stats}")
    
    # Save statistics to a file for inspection
    with open('data/end_to_end_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    return stats

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='End-to-end test for Twitter client daily update process')
    parser.add_argument('--batch-size', type=int, default=2, help='Batch size for processing URLs')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between URLs (seconds)')
    parser.add_argument('--max-tweets', type=int, default=10, help='Maximum number of tweets per URL')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    
    args = parser.parse_args()
    
    try:
        logging.info("Starting end-to-end test")
        logging.info(f"Time: {datetime.now().isoformat()}")
        
        # Set up the database
        db_path = setup_database()
        
        # Run the daily update
        result = run_daily_update(
            db_path=db_path,
            batch_size=args.batch_size,
            sleep_between_urls=args.sleep,
            max_tweets=args.max_tweets,
            limit=args.limit
        )
        
        # Check the database
        stats = check_database(db_path)
        
        logging.info("End-to-end test completed successfully")
        logging.info(f"Total URLs: {stats['total_urls']}")
        logging.info(f"Total tweets: {stats['total_tweets']}")
        
    except Exception as e:
        logging.error(f"Error in end-to-end test: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
