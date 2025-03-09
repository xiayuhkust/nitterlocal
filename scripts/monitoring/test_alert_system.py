#!/usr/bin/env python3
"""
Test script for the email alert system.
This script simulates different types of failures and tests the alert system's response.
"""

import os
import sys
import logging
import argparse
import random
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
        logging.FileHandler("data/alert_test.log"),
        logging.StreamHandler()
    ]
)

def simulate_twitter_extraction_failure():
    """Simulate a Twitter extraction failure"""
    logging.info("Simulating Twitter extraction failure")
    
    # Create error result
    error_result = {
        'success': False,
        'error': 'Simulated Twitter API error: Rate limit exceeded',
        'output': 'Error: Twitter API rate limit exceeded. Please try again later.',
        'error_output': 'Error: Twitter API rate limit exceeded. Please try again later.',
        'timestamp': datetime.now().isoformat()
    }
    
    return error_result

def simulate_mysql_sync_failure():
    """Simulate a MySQL synchronization failure"""
    logging.info("Simulating MySQL synchronization failure")
    
    # Create error result
    error_result = {
        'success': False,
        'error': 'Simulated MySQL connection error: Connection refused',
        'output': 'Error: Could not connect to MySQL server. Connection refused.',
        'error_output': 'Error: Could not connect to MySQL server. Connection refused.',
        'timestamp': datetime.now().isoformat()
    }
    
    return error_result

def simulate_partial_failure():
    """Simulate a partial failure (some URLs processed successfully, some failed)"""
    logging.info("Simulating partial failure")
    
    # Create partial failure result
    partial_result = {
        'success': True,  # Overall process completed
        'processed_count': 10,
        'success_count': 7,
        'error_count': 3,
        'error_urls': [
            {'url': 'https://twitter.com/user1', 'error': 'Rate limit exceeded'},
            {'url': 'https://twitter.com/user2', 'error': 'Account suspended'},
            {'url': 'https://twitter.com/user3', 'error': 'Network timeout'}
        ],
        'total_tweets': 70,
        'completed_at': datetime.now().isoformat()
    }
    
    return partial_result

def simulate_database_corruption():
    """Simulate a database corruption error"""
    logging.info("Simulating database corruption")
    
    # Create database corruption error
    error_result = {
        'success': False,
        'error': 'Simulated database corruption: SQLite database is malformed',
        'output': 'Error: SQLite database is malformed. The database disk image is malformed.',
        'error_output': 'Error: database disk image is malformed',
        'timestamp': datetime.now().isoformat()
    }
    
    return error_result

def simulate_network_failure():
    """Simulate a network failure"""
    logging.info("Simulating network failure")
    
    # Create network failure error
    error_result = {
        'success': False,
        'error': 'Simulated network failure: Connection timeout',
        'output': 'Error: Connection timeout when connecting to Twitter API.',
        'error_output': 'Error: Connection timeout',
        'timestamp': datetime.now().isoformat()
    }
    
    return error_result

def test_alert_system(args):
    """Test the alert system with simulated failures"""
    logging.info("Testing alert system with simulated failures")
    
    # Initialize the alert system
    alert_system = EmailAlertSystem(config_path=args.config)
    
    # Update email configuration for testing
    if args.email:
        alert_system.config['to_email'] = args.email
    
    # Initialize the failure monitor
    failure_monitor = FailureMonitor(alert_system=alert_system)
    
    # Test Twitter extraction failure
    if args.twitter or args.all:
        logging.info("Testing Twitter extraction failure alert")
        extraction_result = simulate_twitter_extraction_failure()
        failure_monitor.check_twitter_extraction(extraction_result)
        time.sleep(2)  # Wait for email to be sent
    
    # Test MySQL synchronization failure
    if args.mysql or args.all:
        logging.info("Testing MySQL synchronization failure alert")
        sync_result = simulate_mysql_sync_failure()
        failure_monitor.check_mysql_sync(sync_result)
        time.sleep(2)  # Wait for email to be sent
    
    # Test partial failure
    if args.partial or args.all:
        logging.info("Testing partial failure alert")
        partial_result = simulate_partial_failure()
        failure_monitor.check_twitter_extraction(partial_result)
        time.sleep(2)  # Wait for email to be sent
    
    # Test database corruption
    if args.database or args.all:
        logging.info("Testing database corruption alert")
        db_result = simulate_database_corruption()
        failure_monitor.check_twitter_extraction(db_result)
        time.sleep(2)  # Wait for email to be sent
    
    # Test network failure
    if args.network or args.all:
        logging.info("Testing network failure alert")
        network_result = simulate_network_failure()
        failure_monitor.check_twitter_extraction(network_result)
        time.sleep(2)  # Wait for email to be sent
    
    # Test consecutive failures
    if args.consecutive or args.all:
        logging.info("Testing consecutive failures")
        for i in range(3):
            logging.info(f"Simulating consecutive failure {i+1}/3")
            extraction_result = simulate_twitter_extraction_failure()
            failure_monitor.check_twitter_extraction(extraction_result)
            time.sleep(2)  # Wait for email to be sent
    
    # Print monitoring state
    monitoring_state = failure_monitor.get_state()
    logging.info(f"Monitoring state: {monitoring_state}")
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test the email alert system')
    parser.add_argument('--config', type=str, default='config/email_config.json', help='Path to email configuration file')
    parser.add_argument('--email', type=str, default='xiayuyosemi@gmail.com', help='Email address to send alerts to')
    parser.add_argument('--twitter', action='store_true', help='Test Twitter extraction failure alert')
    parser.add_argument('--mysql', action='store_true', help='Test MySQL synchronization failure alert')
    parser.add_argument('--partial', action='store_true', help='Test partial failure alert')
    parser.add_argument('--database', action='store_true', help='Test database corruption alert')
    parser.add_argument('--network', action='store_true', help='Test network failure alert')
    parser.add_argument('--consecutive', action='store_true', help='Test consecutive failures')
    parser.add_argument('--all', action='store_true', help='Test all failure scenarios')
    
    args = parser.parse_args()
    
    # If no specific tests are selected, test all
    if not any([args.twitter, args.mysql, args.partial, args.database, args.network, args.consecutive, args.all]):
        args.all = True
    
    # Run tests
    success = test_alert_system(args)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
