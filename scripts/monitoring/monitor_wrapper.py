#!/usr/bin/env python3
"""
Monitoring wrapper script for Twitter data extraction and MySQL synchronization.
This script wraps the main.py and sync_to_mysql.py scripts with monitoring and alerting.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import time
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import monitoring modules
from src.monitoring.email_alert import EmailAlertSystem
from src.monitoring.failure_monitor import FailureMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/monitoring.log"),
        logging.StreamHandler()
    ]
)

def run_twitter_extraction(args):
    """Run Twitter data extraction with monitoring"""
    logging.info("Running Twitter data extraction with monitoring")
    
    # Build command
    cmd = ["python3", "main.py"]
    
    # Add arguments
    if args.batch_size:
        cmd.extend(["--batch-size", str(args.batch_size)])
    
    if args.sleep:
        cmd.extend(["--sleep", str(args.sleep)])
    
    if args.max_tweets:
        cmd.extend(["--max-tweets", str(args.max_tweets)])
    
    if args.max_replies:
        cmd.extend(["--max-replies", str(args.max_replies)])
    
    if args.limit:
        cmd.extend(["--limit", str(args.limit)])
    
    if args.db_path:
        cmd.extend(["--db-path", str(args.db_path)])
    
    if args.performance:
        cmd.append("--performance")
    
    if args.parallel:
        cmd.append("--parallel")
    
    if args.threads:
        cmd.extend(["--threads", str(args.threads)])
    
    # Run command
    try:
        logging.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Parse result
        output = result.stdout
        
        # Extract performance summary
        performance_summary = {}
        in_summary = False
        
        for line in output.splitlines():
            if "===== Performance Summary =====" in line:
                in_summary = True
                continue
            
            if in_summary and "===============================" in line:
                in_summary = False
                continue
            
            if in_summary:
                if ":" in line:
                    key, value = line.split(":", 1)
                    performance_summary[key.strip()] = value.strip()
        
        # Create result object
        extraction_result = {
            'success': True,
            'output': output,
            'performance_summary': performance_summary,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save result to file
        with open('data/twitter_extraction_result.json', 'w') as f:
            json.dump(extraction_result, f, indent=2)
        
        logging.info("Twitter data extraction completed successfully")
        
        return extraction_result
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Twitter data extraction failed: {e}")
        
        # Create error result
        error_result = {
            'success': False,
            'error': str(e),
            'output': e.stdout,
            'error_output': e.stderr,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save error result to file
        with open('data/twitter_extraction_error.json', 'w') as f:
            json.dump(error_result, f, indent=2)
        
        return error_result

def run_mysql_sync(args):
    """Run MySQL synchronization with monitoring"""
    logging.info("Running MySQL synchronization with monitoring")
    
    # Build command
    cmd = ["python3", "scripts/sync/sync_to_mysql.py"]
    
    # Add arguments
    if args.limit:
        cmd.extend(["--limit", str(args.limit)])
    
    if args.test:
        cmd.append("--test")
    
    if args.kol_only:
        cmd.append("--kol-only")
    
    if args.tweets_only:
        cmd.append("--tweets-only")
    
    if args.since_days:
        cmd.extend(["--since-days", str(args.since_days)])
    
    # Run command
    try:
        logging.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Parse result
        output = result.stdout
        
        # Extract synchronization summary
        sync_summary = {}
        in_summary = False
        
        for line in output.splitlines():
            if "Synchronization Summary:" in line:
                in_summary = True
                continue
            
            if in_summary:
                if ":" in line:
                    key, value = line.split(":", 1)
                    sync_summary[key.strip()] = value.strip()
        
        # Create result object
        sync_result = {
            'success': True,
            'output': output,
            'sync_summary': sync_summary,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save result to file
        with open('data/mysql_sync_result.json', 'w') as f:
            json.dump(sync_result, f, indent=2)
        
        logging.info("MySQL synchronization completed successfully")
        
        return sync_result
        
    except subprocess.CalledProcessError as e:
        logging.error(f"MySQL synchronization failed: {e}")
        
        # Create error result
        error_result = {
            'success': False,
            'error': str(e),
            'output': e.stdout,
            'error_output': e.stderr,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save error result to file
        with open('data/mysql_sync_error.json', 'w') as f:
            json.dump(error_result, f, indent=2)
        
        return error_result

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Monitoring wrapper for Twitter data extraction and MySQL synchronization')
    
    # Twitter extraction arguments
    parser.add_argument('--batch-size', type=int, help='Batch size for processing URLs')
    parser.add_argument('--sleep', type=int, help='Sleep time between URLs (seconds)')
    parser.add_argument('--max-tweets', type=int, help='Maximum number of tweets per URL')
    parser.add_argument('--max-replies', type=int, help='Maximum number of reply tweets per URL')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--db-path', type=str, help='Path to the local database')
    parser.add_argument('--performance', action='store_true', help='Enable detailed performance monitoring')
    parser.add_argument('--parallel', action='store_true', help='Enable parallel processing of URLs')
    parser.add_argument('--threads', type=int, help='Number of threads for parallel processing')
    
    # MySQL synchronization arguments
    parser.add_argument('--test', action='store_true', help='Test mode - do not insert or update records in MySQL')
    parser.add_argument('--kol-only', action='store_true', help='Only synchronize KOL info')
    parser.add_argument('--tweets-only', action='store_true', help='Only synchronize tweets')
    parser.add_argument('--since-days', type=int, help='Only process tweets from the last N days')
    
    # Monitoring arguments
    parser.add_argument('--skip-extraction', action='store_true', help='Skip Twitter data extraction')
    parser.add_argument('--skip-sync', action='store_true', help='Skip MySQL synchronization')
    parser.add_argument('--email-alerts', action='store_true', help='Enable email alerts')
    
    args = parser.parse_args()
    
    # Initialize monitoring components
    if args.email_alerts:
        logging.info("Initializing email alert system")
        alert_system = EmailAlertSystem()
    else:
        alert_system = None
    
    logging.info("Initializing failure monitoring system")
    failure_monitor = FailureMonitor(alert_system=alert_system)
    
    # Run Twitter data extraction
    extraction_result = None
    if not args.skip_extraction:
        extraction_result = run_twitter_extraction(args)
        
        # Check for failures
        failure_monitor.check_twitter_extraction(extraction_result)
    
    # Run MySQL synchronization
    sync_result = None
    if not args.skip_sync:
        sync_result = run_mysql_sync(args)
        
        # Check for failures
        failure_monitor.check_mysql_sync(sync_result)
    
    # Print monitoring state
    monitoring_state = failure_monitor.get_state()
    logging.info(f"Monitoring state: {json.dumps(monitoring_state, indent=2)}")
    
    # Return success if both operations succeeded
    if (args.skip_extraction or extraction_result.get('success', False)) and \
       (args.skip_sync or sync_result.get('success', False)):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
