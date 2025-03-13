#!/usr/bin/env python3
"""
Cross-server synchronization script for Twitter data.
This script synchronizes data from SQLite on the Ubuntu server to MySQL on the CentOS server.

Usage:
    python3 sync_to_mysql.py [--limit LIMIT] [--test] [--kol-only] [--tweets-only]
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/sync_log.log'),
        logging.StreamHandler()
    ]
)

def run_kol_info_sync(limit=None, test=False):
    """Run the KOL info synchronization script"""
    logging.info("Starting KOL info synchronization")
    
    cmd = ["python3", "scripts/database/fixed_update_mysql_kol_info_v2.py"]
    
    if limit:
        cmd.extend(["--limit", str(limit)])
    
    if test:
        cmd.append("--test")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        logging.info(f"KOL info synchronization completed in {time.time() - start_time:.2f} seconds")
        logging.info(f"Output: {result.stdout}")
        
        if result.stderr:
            logging.warning(f"Errors: {result.stderr}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        logging.error(f"KOL info synchronization failed: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Errors: {e.stderr}")
        return False

def run_tweet_sync(limit=None, test=False, since_days=None):
    """Run the tweet synchronization script"""
    logging.info("Starting tweet synchronization")
    
    cmd = ["python3", "scripts/database/fixed_update_mysql_kol_tweet.py"]
    
    if limit:
        cmd.extend(["--limit", str(limit)])
    
    if test:
        cmd.append("--test")
    
    if since_days:
        cmd.extend(["--since-days", str(since_days)])
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        logging.info(f"Tweet synchronization completed in {time.time() - start_time:.2f} seconds")
        logging.info(f"Output: {result.stdout}")
        
        if result.stderr:
            logging.warning(f"Errors: {result.stderr}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Tweet synchronization failed: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Errors: {e.stderr}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Cross-server synchronization script for Twitter data')
    parser.add_argument('--limit', type=int, help='Limit the number of records to process')
    parser.add_argument('--test', action='store_true', help='Test mode - do not insert or update records in MySQL')
    parser.add_argument('--kol-only', action='store_true', help='Only synchronize KOL info')
    parser.add_argument('--tweets-only', action='store_true', help='Only synchronize tweets')
    parser.add_argument('--since-days', type=int, help='Only process tweets from the last N days')
    
    args = parser.parse_args()
    
    logging.info("Starting cross-server synchronization")
    logging.info(f"Time: {datetime.now().isoformat()}")
    
    start_time = time.time()
    success = True
    
    # Run KOL info synchronization
    if not args.tweets_only:
        kol_success = run_kol_info_sync(args.limit, args.test)
        success = success and kol_success
    
    # Run tweet synchronization
    if not args.kol_only:
        tweet_success = run_tweet_sync(args.limit, args.test, args.since_days)
        success = success and tweet_success
    
    # Log completion
    total_time = time.time() - start_time
    logging.info(f"Cross-server synchronization completed in {total_time:.2f} seconds")
    
    if success:
        logging.info("All synchronization tasks completed successfully")
    else:
        logging.warning("Some synchronization tasks failed")
    
    # Print summary
    print("\nSynchronization Summary:")
    print(f"Total Duration: {total_time:.2f} seconds")
    print(f"Success: {success}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
