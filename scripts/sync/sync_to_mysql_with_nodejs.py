#!/usr/bin/env python3
"""
Script to synchronize data from SQLite to MySQL with full profile information.
This script will synchronize both KOL info and tweets using the Node.js Twitter client
to retrieve comprehensive profile information.
"""

import os
import sys
import logging
import argparse
import subprocess
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_command(command):
    """Run a command and return the result"""
    try:
        process = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return {
            'success': True,
            'output': process.stdout,
            'error_output': process.stderr,
            'timestamp': datetime.now().isoformat()
        }
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': str(e),
            'output': e.stdout,
            'error_output': e.stderr,
            'timestamp': datetime.now().isoformat()
        }

def sync_kol_info(limit=None, test=False):
    """Synchronize KOL info from SQLite to MySQL"""
    logging.info("Starting KOL info synchronization")
    
    # Build the command (without --no-nodejs flag to enable full profile retrieval)
    command = ['python3', 'scripts/database/fixed_update_mysql_kol_info_v3.py']
    
    if limit:
        command.extend(['--limit', str(limit)])
    
    if test:
        command.append('--test')
    
    # Run the command
    start_time = time.time()
    result = run_command(command)
    end_time = time.time()
    
    # Log the result
    if result['success']:
        logging.info("KOL info synchronization completed in {:.2f} seconds".format(end_time - start_time))
        logging.info("Output: {}".format(result['output']))
        if result['error_output']:
            logging.warning("Errors: {}".format(result['error_output']))
    else:
        logging.error("KOL info synchronization failed: {}".format(result['error']))
        logging.error("Output: {}".format(result['output']))
        logging.error("Errors: {}".format(result['error_output']))
    
    return result

def sync_tweets(since_days=None, limit=None, test=False):
    """Synchronize tweets from SQLite to MySQL"""
    logging.info("Starting tweet synchronization")
    
    # Build the command
    command = ['python3', 'scripts/database/fixed_update_mysql_kol_tweet.py']
    
    if since_days:
        command.extend(['--since-days', str(since_days)])
    
    if limit:
        command.extend(['--limit', str(limit)])
    
    if test:
        command.append('--test')
    
    # Run the command
    start_time = time.time()
    result = run_command(command)
    end_time = time.time()
    
    # Log the result
    if result['success']:
        logging.info("Tweet synchronization completed in {:.2f} seconds".format(end_time - start_time))
        logging.info("Output: {}".format(result['output']))
        if result['error_output']:
            logging.warning("Errors: {}".format(result['error_output']))
    else:
        logging.error("Tweet synchronization failed: {}".format(result['error']))
        logging.error("Output: {}".format(result['output']))
        logging.error("Errors: {}".format(result['error_output']))
    
    return result

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize data from SQLite to MySQL')
    parser.add_argument('--limit', type=int, help='Limit the number of records to process')
    parser.add_argument('--test', action='store_true', help='Test mode - do not insert or update records in MySQL')
    parser.add_argument('--kol-only', action='store_true', help='Only synchronize KOL info')
    parser.add_argument('--tweets-only', action='store_true', help='Only synchronize tweets')
    parser.add_argument('--since-days', type=int, default=1, help='Synchronize tweets from the last N days')
    
    args = parser.parse_args()
    
    # Start timing
    start_time = time.time()
    
    logging.info("Starting cross-server synchronization")
    logging.info("Time: {}".format(datetime.now().isoformat()))
    
    # Synchronize KOL info
    kol_result = None
    if not args.tweets_only:
        kol_result = sync_kol_info(limit=args.limit, test=args.test)
    
    # Synchronize tweets
    tweet_result = None
    if not args.kol_only:
        tweet_result = sync_tweets(since_days=args.since_days, limit=args.limit, test=args.test)
    
    # Calculate total time
    end_time = time.time()
    total_time = end_time - start_time
    
    # Check if all tasks were successful
    all_success = True
    if kol_result and not kol_result['success']:
        all_success = False
    if tweet_result and not tweet_result['success']:
        all_success = False
    
    # Log the result
    if all_success:
        logging.info("Cross-server synchronization completed in {:.2f} seconds".format(total_time))
        logging.info("All synchronization tasks completed successfully")
    else:
        logging.warning("Cross-server synchronization completed in {:.2f} seconds".format(total_time))
        logging.warning("Some synchronization tasks failed")
    
    # Print summary
    print("\nSynchronization Summary:")
    print("Total Duration: {:.2f} seconds".format(total_time))
    print("Success: {}".format(all_success))
    
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())
