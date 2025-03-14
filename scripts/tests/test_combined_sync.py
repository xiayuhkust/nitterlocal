#!/usr/bin/env python3
"""
Test script for the combined MySQL synchronization script.
"""

import os
import sys
import logging
import subprocess
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_combined_sync():
    """Test the combined sync script"""
    try:
        # Run the script in test mode
        cmd = [
            'python3',
            '/home/ubuntu/nitterlocal/scripts/sync/sync_to_mysql_combined.py',
            '--test'
        ]
        
        logging.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        logging.info(f"Output: {result.stdout}")
        if result.stderr:
            logging.warning(f"Errors: {result.stderr}")
        
        # Check if the script mentions both tables
        if "url_tracking" in result.stdout and "kol_character" in result.stdout:
            logging.info("Combined sync script successfully processes both tables")
            return True
        else:
            logging.warning("Combined sync script may not be processing both tables")
            return False
    
    except Exception as e:
        logging.error(f"Error testing combined sync: {str(e)}")
        return False

def main():
    """Main function"""
    if test_combined_sync():
        print("Combined sync script test passed!")
        return 0
    else:
        print("Combined sync script test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
