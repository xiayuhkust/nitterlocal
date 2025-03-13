#!/usr/bin/env python3
"""
Failure monitoring system for Twitter data extraction.
This module provides functionality for detecting and alerting on failures.
"""

import os
import sys
import logging
import json
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FailureMonitor:
    """Failure monitoring system for Twitter data extraction"""
    
    def __init__(self, state_path='data/failure_monitor_state.json', alert_system=None):
        """Initialize the failure monitoring system"""
        logging.info(f"Initializing failure monitoring system with state at {state_path}")
        
        self.state_path = state_path
        self.alert_system = alert_system
        self.state = self._load_state()
        
        # Set default thresholds
        self.thresholds = {
            'twitter_extraction': {
                'consecutive_failures': 3,
                'error_rate': 0.5,  # 50% error rate
                'min_processed': 10  # Minimum number of URLs to process before checking error rate
            },
            'mysql_sync': {
                'consecutive_failures': 2,
                'error_rate': 0.3,  # 30% error rate
                'min_processed': 5   # Minimum number of records to process before checking error rate
            }
        }
        
        logging.info("Failure monitoring system initialization complete")
    
    def _load_state(self):
        """Load the monitoring state from a JSON file"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            
            # Check if state file exists
            if not os.path.exists(self.state_path):
                # Create default state
                default_state = {
                    'twitter_extraction': {
                        'last_success': None,
                        'last_failure': None,
                        'consecutive_failures': 0,
                        'total_runs': 0,
                        'total_failures': 0,
                        'last_alert': None
                    },
                    'mysql_sync': {
                        'last_success': None,
                        'last_failure': None,
                        'consecutive_failures': 0,
                        'total_runs': 0,
                        'total_failures': 0,
                        'last_alert': None
                    },
                    'last_updated': datetime.now().isoformat()
                }
                
                # Save default state
                with open(self.state_path, 'w') as f:
                    json.dump(default_state, f, indent=2)
                
                logging.info(f"Created default monitoring state at {self.state_path}")
                
                return default_state
            
            # Load state from file
            with open(self.state_path, 'r') as f:
                state = json.load(f)
            
            logging.info(f"Loaded monitoring state from {self.state_path}")
            
            return state
            
        except Exception as e:
            logging.error(f"Error loading monitoring state: {str(e)}")
            
            # Return default state
            return {
                'twitter_extraction': {
                    'last_success': None,
                    'last_failure': None,
                    'consecutive_failures': 0,
                    'total_runs': 0,
                    'total_failures': 0,
                    'last_alert': None
                },
                'mysql_sync': {
                    'last_success': None,
                    'last_failure': None,
                    'consecutive_failures': 0,
                    'total_runs': 0,
                    'total_failures': 0,
                    'last_alert': None
                },
                'last_updated': datetime.now().isoformat()
            }
    
    def _save_state(self):
        """Save the monitoring state to a JSON file"""
        try:
            # Update last updated timestamp
            self.state['last_updated'] = datetime.now().isoformat()
            
            # Save state to file
            with open(self.state_path, 'w') as f:
                json.dump(self.state, f, indent=2)
            
            logging.info(f"Saved monitoring state to {self.state_path}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error saving monitoring state: {str(e)}")
            return False
    
    def check_twitter_extraction(self, result):
        """Check Twitter extraction result for failures"""
        logging.info("Checking Twitter extraction result for failures")
        
        # Update state
        self.state['twitter_extraction']['total_runs'] += 1
        
        # Check for errors
        if 'error' in result:
            # Update failure state
            self.state['twitter_extraction']['last_failure'] = datetime.now().isoformat()
            self.state['twitter_extraction']['consecutive_failures'] += 1
            self.state['twitter_extraction']['total_failures'] += 1
            
            logging.warning(f"Twitter extraction failed: {result['error']}")
            
            # Check if we need to send an alert
            if self.state['twitter_extraction']['consecutive_failures'] >= self.thresholds['twitter_extraction']['consecutive_failures']:
                self._send_twitter_extraction_alert(result)
        else:
            # Check for high error rate
            processed_count = result.get('processed_count', 0)
            error_count = result.get('error_count', 0)
            
            if processed_count >= self.thresholds['twitter_extraction']['min_processed']:
                error_rate = error_count / processed_count if processed_count > 0 else 0
                
                if error_rate >= self.thresholds['twitter_extraction']['error_rate']:
                    logging.warning(f"Twitter extraction error rate too high: {error_rate:.2f}")
                    
                    # Update failure state
                    self.state['twitter_extraction']['last_failure'] = datetime.now().isoformat()
                    self.state['twitter_extraction']['consecutive_failures'] += 1
                    self.state['twitter_extraction']['total_failures'] += 1
                    
                    # Check if we need to send an alert
                    if self.state['twitter_extraction']['consecutive_failures'] >= self.thresholds['twitter_extraction']['consecutive_failures']:
                        result['high_error_rate'] = error_rate
                        self._send_twitter_extraction_alert(result)
                else:
                    # Update success state
                    self.state['twitter_extraction']['last_success'] = datetime.now().isoformat()
                    self.state['twitter_extraction']['consecutive_failures'] = 0
                    
                    logging.info(f"Twitter extraction successful with error rate: {error_rate:.2f}")
            else:
                # Update success state
                self.state['twitter_extraction']['last_success'] = datetime.now().isoformat()
                self.state['twitter_extraction']['consecutive_failures'] = 0
                
                logging.info("Twitter extraction successful")
        
        # Save state
        self._save_state()
    
    def check_mysql_sync(self, result):
        """Check MySQL synchronization result for failures"""
        logging.info("Checking MySQL synchronization result for failures")
        
        # Update state
        self.state['mysql_sync']['total_runs'] += 1
        
        # Check for errors
        if 'error' in result:
            # Update failure state
            self.state['mysql_sync']['last_failure'] = datetime.now().isoformat()
            self.state['mysql_sync']['consecutive_failures'] += 1
            self.state['mysql_sync']['total_failures'] += 1
            
            logging.warning(f"MySQL synchronization failed: {result['error']}")
            
            # Check if we need to send an alert
            if self.state['mysql_sync']['consecutive_failures'] >= self.thresholds['mysql_sync']['consecutive_failures']:
                self._send_mysql_sync_alert(result)
        else:
            # Check for high error rate
            processed_count = result.get('processed_count', 0)
            error_count = result.get('error_count', 0)
            
            if processed_count >= self.thresholds['mysql_sync']['min_processed']:
                error_rate = error_count / processed_count if processed_count > 0 else 0
                
                if error_rate >= self.thresholds['mysql_sync']['error_rate']:
                    logging.warning(f"MySQL synchronization error rate too high: {error_rate:.2f}")
                    
                    # Update failure state
                    self.state['mysql_sync']['last_failure'] = datetime.now().isoformat()
                    self.state['mysql_sync']['consecutive_failures'] += 1
                    self.state['mysql_sync']['total_failures'] += 1
                    
                    # Check if we need to send an alert
                    if self.state['mysql_sync']['consecutive_failures'] >= self.thresholds['mysql_sync']['consecutive_failures']:
                        result['high_error_rate'] = error_rate
                        self._send_mysql_sync_alert(result)
                else:
                    # Update success state
                    self.state['mysql_sync']['last_success'] = datetime.now().isoformat()
                    self.state['mysql_sync']['consecutive_failures'] = 0
                    
                    logging.info(f"MySQL synchronization successful with error rate: {error_rate:.2f}")
            else:
                # Update success state
                self.state['mysql_sync']['last_success'] = datetime.now().isoformat()
                self.state['mysql_sync']['consecutive_failures'] = 0
                
                logging.info("MySQL synchronization successful")
        
        # Save state
        self._save_state()
    
    def _send_twitter_extraction_alert(self, result):
        """Send an alert for Twitter extraction failure"""
        if not self.alert_system:
            logging.warning("No alert system configured, cannot send Twitter extraction alert")
            return False
        
        # Check if we've already sent an alert recently
        if self.state['twitter_extraction']['last_alert']:
            last_alert = datetime.fromisoformat(self.state['twitter_extraction']['last_alert'])
            if datetime.now() - last_alert < timedelta(hours=1):
                logging.info("Skipping Twitter extraction alert, already sent one recently")
                return False
        
        # Prepare alert message
        subject = "Twitter Extraction Failure"
        message = f"Twitter extraction has failed {self.state['twitter_extraction']['consecutive_failures']} times in a row."
        
        # Send alert
        success = self.alert_system.send_alert(subject, message, error=result.get('error'), data=result)
        
        if success:
            # Update last alert timestamp
            self.state['twitter_extraction']['last_alert'] = datetime.now().isoformat()
            self._save_state()
        
        return success
    
    def _send_mysql_sync_alert(self, result):
        """Send an alert for MySQL synchronization failure"""
        if not self.alert_system:
            logging.warning("No alert system configured, cannot send MySQL synchronization alert")
            return False
        
        # Check if we've already sent an alert recently
        if self.state['mysql_sync']['last_alert']:
            last_alert = datetime.fromisoformat(self.state['mysql_sync']['last_alert'])
            if datetime.now() - last_alert < timedelta(hours=1):
                logging.info("Skipping MySQL synchronization alert, already sent one recently")
                return False
        
        # Prepare alert message
        subject = "MySQL Synchronization Failure"
        message = f"MySQL synchronization has failed {self.state['mysql_sync']['consecutive_failures']} times in a row."
        
        # Send alert
        success = self.alert_system.send_alert(subject, message, error=result.get('error'), data=result)
        
        if success:
            # Update last alert timestamp
            self.state['mysql_sync']['last_alert'] = datetime.now().isoformat()
            self._save_state()
        
        return success
    
    def get_state(self):
        """Get the current monitoring state"""
        return self.state
    
    def reset_state(self):
        """Reset the monitoring state"""
        self.state = {
            'twitter_extraction': {
                'last_success': None,
                'last_failure': None,
                'consecutive_failures': 0,
                'total_runs': 0,
                'total_failures': 0,
                'last_alert': None
            },
            'mysql_sync': {
                'last_success': None,
                'last_failure': None,
                'consecutive_failures': 0,
                'total_runs': 0,
                'total_failures': 0,
                'last_alert': None
            },
            'last_updated': datetime.now().isoformat()
        }
        
        self._save_state()
        
        logging.info("Reset monitoring state")
        
        return self.state
