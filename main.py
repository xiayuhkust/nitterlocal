#!/usr/bin/env python3
"""
Main script for the Twitter client daily update process.
This script serves as the entry point for the application.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/daily_update.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Twitter client daily update process')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing URLs')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between URLs (seconds)')
    parser.add_argument('--max-tweets', type=int, default=50, help='Maximum number of tweets per URL')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    
    args = parser.parse_args()
    
    # Import the DailyUpdate class
    from src.daily_update.daily_update import DailyUpdate
    
    # Initialize the daily update
    daily_update = DailyUpdate(db_path=args.db_path)
    
    # Run the daily update
    result = daily_update.run(
        batch_size=args.batch_size,
        sleep_between_urls=args.sleep,
        max_tweets=args.max_tweets,
        limit=args.limit
    )
    
    # Log the result
    logging.info(f"Daily update result: {result}")

if __name__ == "__main__":
    main()
