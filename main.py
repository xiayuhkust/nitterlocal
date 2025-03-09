#!/usr/bin/env python3
"""
Main script for the Twitter client daily update process.
This script serves as the entry point for the application.
"""

import os
import sys
import logging
import argparse
import time
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
    parser.add_argument('--max-tweets', type=int, default=10, help='Maximum number of tweets per URL')
    parser.add_argument('--max-replies', type=int, default=5, help='Maximum number of reply tweets per URL')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--performance', action='store_true', help='Enable detailed performance monitoring')
    
    args = parser.parse_args()
    
    # Start timing
    start_time = time.time()
    
    # Import the DailyUpdate class
    from src.daily_update.daily_update import DailyUpdate
    
    # Initialize the daily update
    daily_update = DailyUpdate(db_path=args.db_path)
    
    # Run the daily update
    result = daily_update.run(
        batch_size=args.batch_size,
        sleep_between_urls=args.sleep,
        max_tweets=args.max_tweets,
        max_replies=args.max_replies,
        limit=args.limit,
        performance_monitoring=args.performance
    )
    
    # Calculate total execution time
    total_time = time.time() - start_time
    
    # Add performance metrics to result
    result['total_execution_time'] = f"{total_time:.2f} seconds"
    if 'processed_count' in result and result['processed_count'] > 0:
        result['avg_time_per_url'] = f"{total_time / result['processed_count']:.2f} seconds"
    
    # Log the result with performance metrics
    logging.info(f"Daily update result: {result}")
    
    # Print performance summary
    print("\n===== Performance Summary =====")
    print(f"Total execution time: {total_time:.2f} seconds")
    if 'processed_count' in result and result['processed_count'] > 0:
        print(f"URLs processed: {result['processed_count']}")
        print(f"Average time per URL: {total_time / result['processed_count']:.2f} seconds")
    if 'performance_details' in result:
        print("\nDetailed Performance Breakdown:")
        for key, value in result['performance_details'].items():
            print(f"  {key}: {value}")
    print("===============================")

if __name__ == "__main__":
    main()
