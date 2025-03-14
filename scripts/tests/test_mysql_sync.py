#!/usr/bin/env python3
"""
Script to test MySQL synchronization.
"""

import os
import sys
import logging
import argparse
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_sync_script(test_mode=True):
    """Run the sync_to_mysql_combined.py script"""
    try:
        # Build the command
        cmd = [
            'python3',
            'scripts/sync/sync_to_mysql_combined.py'
        ]
        
        if test_mode:
            cmd.append('--test')
        
        # Run the command
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Print the output
        print("Output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running sync script: {str(e)}")
        print(f"Output: {e.stdout}")
        print(f"Errors: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error running sync script: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test MySQL synchronization')
    parser.add_argument('--no-test', action='store_true', help='Run in non-test mode (will update MySQL)')
    
    args = parser.parse_args()
    
    # Run the sync script
    success = run_sync_script(not args.no_test)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
