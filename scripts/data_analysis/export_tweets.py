#!/usr/bin/env python3
"""
Script to export tweets from the database to CSV or JSON format.
This script exports tweets from the database to various formats for external analysis.
"""

import os
import sys
import logging
import sqlite3
import json
import csv
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

def export_tweets(db_path='data/local_database.db', output_format='csv', output_file=None, 
                source_url=None, limit=None):
    """Export tweets from the database"""
    logging.info(f"Exporting tweets from database at {db_path}")
    
    try:
        # Initialize the database
        db = LocalDatabase(db_path=db_path)
        
        # Get tweets
        tweets = db.get_tweets(source_url=source_url, limit=limit)
        
        logging.info(f"Found {len(tweets)} tweets to export")
        
        # Determine output file name if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if source_url:
                source_name = source_url.split('/')[-1]
                output_file = f"data/exports/tweets_{source_name}_{timestamp}.{output_format}"
            else:
                output_file = f"data/exports/tweets_all_{timestamp}.{output_format}"
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Export tweets
        if output_format == 'json':
            with open(output_file, 'w') as f:
                json.dump({'tweets': tweets}, f, indent=2)
        else:  # CSV
            with open(output_file, 'w', newline='') as f:
                if tweets:
                    fieldnames = tweets[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(tweets)
                else:
                    writer = csv.writer(f)
                    writer.writerow(['No tweets found'])
        
        logging.info(f"Exported {len(tweets)} tweets to {output_file}")
        
        return output_file
        
    except Exception as e:
        logging.error(f"Error exporting tweets: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Export tweets from the database')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--format', type=str, choices=['csv', 'json'], default='csv', help='Output format')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--source-url', type=str, help='Filter tweets by source URL')
    parser.add_argument('--limit', type=int, help='Limit the number of tweets to export')
    
    args = parser.parse_args()
    
    # Export tweets
    export_tweets(
        db_path=args.db_path,
        output_format=args.format,
        output_file=args.output,
        source_url=args.source_url,
        limit=args.limit
    )

if __name__ == "__main__":
    main()
