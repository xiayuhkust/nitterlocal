#!/usr/bin/env python3
"""
Test script to verify the fix for the MySQL synchronization issue.
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

def test_sync_script():
    """Test the sync_to_mysql_combined.py script"""
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
        
        # Check if the script ran without errors
        if "Error synchronizing" in result.stdout or "Error in synchronization" in result.stdout:
            logging.error("Synchronization script reported errors")
            return False
        
        logging.info("Synchronization script ran successfully")
        return True
    
    except Exception as e:
        logging.error(f"Error testing sync script: {str(e)}")
        return False

def main():
    """Main function"""
    if test_sync_script():
        print("MySQL synchronization fix test passed!")
        return 0
    else:
        print("MySQL synchronization fix test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
