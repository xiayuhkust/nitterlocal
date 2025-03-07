#!/usr/bin/env python3
"""
Test script for the Python 3.6 compatible combined update script.
"""

import os
import sys
import logging
import subprocess
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_combined_update(limit=2, max_tweets=5, max_replies=5):
    """Test the combined update script"""
    try:
        # Path to the combined update script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  'database/combined_update_with_performance_py36.py')
        
        # Run the script with a small limit
        logging.info("Running combined update script with limit={}...".format(limit))
        
        # Python 3.6 compatible subprocess call
        process = subprocess.run(
            ['python3', script_path, '--limit', str(limit), 
             '--max-tweets', str(max_tweets), '--max-replies', str(max_replies)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Check if the script ran successfully
        if process.returncode == 0:
            logging.info("Combined update script ran successfully")
            logging.info("Output: {}".format(process.stdout))
            return True
        else:
            logging.error("Combined update script failed with return code {}".format(process.returncode))
            logging.error("Error: {}".format(process.stderr))
            return False
    
    except Exception as e:
        logging.error("Error testing combined update script: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test the Python 3.6 compatible combined update script')
    parser.add_argument('--limit', type=int, default=2, help='Limit the number of URLs to process')
    parser.add_argument('--max-tweets', type=int, default=5, help='Maximum number of tweets to fetch per URL')
    parser.add_argument('--max-replies', type=int, default=5, help='Maximum number of replies to fetch per URL')
    
    args = parser.parse_args()
    
    logging.info("Testing Python 3.6 compatible combined update script")
    
    # Test the combined update script
    if test_combined_update(args.limit, args.max_tweets, args.max_replies):
        logging.info("Combined update script test passed")
        return 0
    else:
        logging.error("Combined update script test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
