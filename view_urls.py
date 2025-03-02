#!/usr/bin/env python3
"""
Script to view URLs in the database.
This script displays URLs stored in the database.
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

def view_urls(db_path='data/local_database.db', status=None, limit=None, output_file=None):
    """View URLs in the database"""
    logging.info(f"Viewing URLs in database at {db_path}")
    
    try:
        # Initialize the database
        db = LocalDatabase(db_path=db_path)
        
        # Get URLs
        urls = db.get_urls(status=status, limit=limit)
        
        logging.info(f"Found {len(urls)} URLs in the database")
        
        # Display URLs
        for i, url_data in enumerate(urls):
            print(f"{i+1}. {url_data['url']}")
            print(f"   Description: {url_data['description']}")
            print(f"   Status: {url_data['status']}")
            print(f"   Type: {url_data['type']}")
            print(f"   Tweet count: {url_data['tweet_count']}")
            print(f"   Last scraped: {url_data['last_scraped']}")
            print()
        
        # Save URLs to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump({'urls': urls}, f, indent=2)
            logging.info(f"Saved URLs to {output_file}")
        
        return urls
        
    except Exception as e:
        logging.error(f"Error viewing URLs: {str(e)}")
        return []

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='View URLs in the database')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    parser.add_argument('--status', type=str, help='Filter URLs by status')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to display')
    parser.add_argument('--output', type=str, help='Save URLs to a JSON file')
    
    args = parser.parse_args()
    
    # View URLs
    view_urls(db_path=args.db_path, status=args.status, limit=args.limit, output_file=args.output)

if __name__ == "__main__":
    main()
