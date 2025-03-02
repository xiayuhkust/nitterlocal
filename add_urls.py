#!/usr/bin/env python3
"""
Script to add URLs to the database.
This script adds URLs from a JSON file to the database.
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

def add_urls_from_file(file_path, db_path='data/local_database.db'):
    """Add URLs from a JSON file to the database"""
    logging.info(f"Adding URLs from {file_path} to database at {db_path}")
    
    try:
        # Load URLs from file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'urls' not in data:
            logging.error(f"Invalid JSON format: {file_path}")
            return False
        
        urls = data['urls']
        logging.info(f"Found {len(urls)} URLs in {file_path}")
        
        # Initialize the database
        db = LocalDatabase(db_path=db_path)
        
        # Add URLs to the database
        added_count = 0
        for url_data in urls:
            if isinstance(url_data, str):
                # Simple URL string
                result = db.add_url(url_data)
                if result:
                    added_count += 1
            elif isinstance(url_data, dict) and 'url' in url_data:
                # URL with metadata
                result = db.add_url(
                    url_data['url'],
                    description=url_data.get('description', ''),
                    url_type=url_data.get('type', 'kol')
                )
                if result:
                    added_count += 1
            else:
                logging.warning(f"Invalid URL format: {url_data}")
        
        logging.info(f"Added {added_count} URLs to the database")
        
        return True
        
    except Exception as e:
        logging.error(f"Error adding URLs from {file_path}: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Add URLs to the database')
    parser.add_argument('--file', type=str, required=True, help='Path to the JSON file containing URLs')
    parser.add_argument('--db-path', type=str, default='data/local_database.db', help='Path to the local database')
    
    args = parser.parse_args()
    
    # Add URLs from file
    add_urls_from_file(args.file, db_path=args.db_path)

if __name__ == "__main__":
    main()
