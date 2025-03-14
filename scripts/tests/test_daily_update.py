#!/usr/bin/env python3
"""
Test script for the daily update implementation.
This script tests the daily update module's ability to process URLs, extract tweets, and store them in the database.
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the daily update module
from src.daily_update.daily_update import DailyUpdate
from src.database.local_database import LocalDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_test_database():
    """Set up a test database with sample URLs"""
    logging.info("Setting up test database")
    
    # Create a test database
    db_path = 'data/test_daily_update.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = LocalDatabase(db_path=db_path)
    
    # Add test URLs
    test_urls = [
        ('https://twitter.com/0xPolygon', 'Polygon', 'kol'),
        ('https://twitter.com/elonmusk', 'Elon Musk', 'kol')
    ]
    
    for url, description, url_type in test_urls:
        db.add_url(url, description=description, url_type=url_type)
    
    logging.info(f"Added {len(test_urls)} test URLs to the database")
    
    return db_path

def test_daily_update():
    """Test the daily update implementation"""
    logging.info("Testing daily update implementation")
    
    try:
        # Set up a test database
        db_path = setup_test_database()
        
        # Initialize the daily update
        daily_update = DailyUpdate(db_path=db_path)
        
        # Run the daily update with a small batch size and limit
        logging.info("Running daily update with small batch size and limit")
        result = daily_update.run(
            batch_size=1,
            sleep_between_urls=1,
            max_tweets=5,
            limit=2
        )
        
        logging.info(f"Daily update result: {result}")
        
        # Check the database for tweets
        db = LocalDatabase(db_path=db_path)
        tweets = db.get_tweets()
        
        logging.info(f"Found {len(tweets)} tweets in the database")
        
        # Generate statistics
        stats = db.generate_stats()
        logging.info(f"Statistics: {stats}")
        
        # Save statistics to a file for inspection
        with open('data/test_daily_update_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        logging.info("Daily update implementation tests completed")
        
    except Exception as e:
        logging.error(f"Error testing daily update: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_daily_update()
