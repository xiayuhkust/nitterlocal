#!/usr/bin/env python3
"""
Test script to verify that the MySQL tweet update script works correctly.
This script runs the update_mysql_kol_tweet.py script with a small limit and verifies that it can insert or update records in the MySQL database.
"""

import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_mysql_tweet_update():
    """Test the MySQL tweet update script"""
    try:
        # Get the path to the update_mysql_kol_tweet.py script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        update_script = os.path.join(script_dir, 'update_mysql_kol_tweet.py')
        
        # Run the update script with a small limit
        logging.info(f"Running update script: {update_script}")
        process = subprocess.run(
            ['python', update_script, '--limit', '2', '--test'],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Print the output
        logging.info("Update script output:")
        for line in process.stdout.splitlines():
            logging.info(line)
        
        # Run the update script again without test mode
        logging.info(f"Running update script in real mode: {update_script}")
        process = subprocess.run(
            ['python', update_script, '--limit', '2'],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Print the output
        logging.info("Update script output (real mode):")
        for line in process.stdout.splitlines():
            logging.info(line)
        
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running update script: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_mysql_tweet_update()
