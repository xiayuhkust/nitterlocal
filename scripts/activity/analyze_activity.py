#!/usr/bin/env python3
"""
Script to analyze Twitter account activity levels.
This script analyzes the activity levels of all Twitter accounts in the database.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import activity manager
from src.database.activity_manager import ActivityManager
from src.database.local_database import LocalDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/activity_analysis.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Analyze Twitter account activity levels')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--report', action='store_true', help='Generate activity report')
    
    args = parser.parse_args()
    
    logging.info("Starting activity analysis")
    logging.info(f"Time: {datetime.now().isoformat()}")
    logging.info(f"Analyzing activity over the past {args.days} days")
    
    # Initialize components
    db = LocalDatabase()
    activity_manager = ActivityManager()
    
    # Get active URLs
    urls = db.get_urls(status='active', limit=args.limit)
    total_urls = len(urls)
    logging.info(f"Found {total_urls} active URLs to process")
    
    # Process each URL
    processed_count = 0
    activity_levels = {
        'very_high': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
        'inactive': 0
    }
    
    for url_data in urls:
        url = url_data['url']
        logging.info(f"Analyzing activity for URL: {url}")
        
        # Analyze activity
        activity_data = activity_manager.analyze_activity(url, days=args.days)
        
        if activity_data:
            level = activity_data['activity_level']
            activity_levels[level] = activity_levels.get(level, 0) + 1
            logging.info(f"Activity level for {url}: {level}")
            logging.info(f"Max tweets: {activity_data['max_tweets']}, Max replies: {activity_data['max_replies']}")
        
        processed_count += 1
        logging.info(f"Processed {processed_count}/{total_urls} URLs")
    
    # Generate report
    if args.report:
        logging.info("Generating activity distribution report")
        
        # Calculate percentages
        total = sum(activity_levels.values())
        percentages = {}
        for level, count in activity_levels.items():
            percentages[level] = (count / total) * 100 if total > 0 else 0
        
        # Print report
        print("\n===== Activity Distribution Report =====")
        print(f"Total URLs analyzed: {total}")
        print("\nActivity Level Distribution:")
        for level, count in activity_levels.items():
            print(f"  {level}: {count} URLs ({percentages[level]:.2f}%)")
        
        print("\nRecommended Tweet Quantities:")
        print("  Very High Activity: 10 tweets, 5 replies")
        print("  High Activity: 8 tweets, 4 replies")
        print("  Medium Activity: 5 tweets, 3 replies")
        print("  Low Activity: 3 tweets, 2 replies")
        print("  Inactive: 1 tweet, 1 reply")
        print("=======================================")
    
    logging.info("Activity analysis completed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
