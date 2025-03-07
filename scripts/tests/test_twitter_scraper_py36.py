#!/usr/bin/env python3
"""
Test script for the Python 3.6 compatible TwitterScraper class.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_twitter_scraper_initialization():
    """Test initializing the TwitterScraper class"""
    try:
        from src.twitter_client.twitter_scraper_py36 import TwitterScraper
        
        logging.info("Importing TwitterScraper_py36 class...")
        scraper = TwitterScraper()
        logging.info("TwitterScraper_py36 initialized successfully")
        
        return True
    except Exception as e:
        logging.error("Error initializing TwitterScraper_py36: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False

def test_extract_username():
    """Test extracting username from URL"""
    try:
        from src.twitter_client.twitter_scraper_py36 import TwitterScraper
        
        scraper = TwitterScraper()
        url = "https://twitter.com/VitalikButerin"
        username = scraper.extract_username_from_url(url)
        
        logging.info("Extracted username from {}: {}".format(url, username))
        
        if username == "VitalikButerin":
            logging.info("Username extraction test passed")
            return True
        else:
            logging.error("Username extraction test failed. Expected 'VitalikButerin', got '{}'".format(username))
            return False
    except Exception as e:
        logging.error("Error in username extraction test: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    logging.info("Testing Python 3.6 compatible TwitterScraper class")
    
    # Test initialization
    if not test_twitter_scraper_initialization():
        logging.error("TwitterScraper initialization test failed")
        return 1
    
    # Test username extraction
    if not test_extract_username():
        logging.error("Username extraction test failed")
        return 1
    
    logging.info("All tests passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
