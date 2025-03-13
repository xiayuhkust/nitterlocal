#!/usr/bin/env python3
"""
Email alert system for Twitter data extraction.
This module provides functionality for sending email alerts when failures occur.
"""

import os
import sys
import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EmailAlertSystem:
    """Email alert system for Twitter data extraction"""
    
    def __init__(self, config_path='config/email_config.json'):
        """Initialize the email alert system"""
        logging.info(f"Initializing email alert system with config at {config_path}")
        
        self.config_path = config_path
        self.config = self._load_config()
        
        logging.info("Email alert system initialization complete")
    
    def _load_config(self):
        """Load the email configuration from a JSON file"""
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Check if config file exists
            if not os.path.exists(self.config_path):
                # Create default config using environment variables
                default_config = {
                    'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
                    'smtp_username': os.environ.get('SMTP_USERNAME', ''),
                    'from_email': os.environ.get('FROM_EMAIL', ''),
                    'to_email': os.environ.get('TO_EMAIL', 'xiayuyosemi@gmail.com'),
                    'subject_prefix': os.environ.get('SUBJECT_PREFIX', '[Twitter Alert]')
                }
                
                # Check if SMTP_PASSWORD is set in environment
                if 'SMTP_PASSWORD' in os.environ:
                    default_config['smtp_password'] = os.environ.get('SMTP_PASSWORD')
                else:
                    default_config['smtp_password'] = ''
                    logging.warning("SMTP_PASSWORD environment variable not set. Email alerts will not work.")
                
                # Save default config
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                logging.warning(f"Created default email config at {self.config_path}. Please update with your SMTP credentials.")
                
                return default_config
            
            # Load config from file
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            logging.info(f"Loaded email config from {self.config_path}")
            
            return config
            
        except Exception as e:
            logging.error(f"Error loading email config: {str(e)}")
            
            # Return default config using environment variables
            default_config = {
                'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
                'smtp_username': os.environ.get('SMTP_USERNAME', ''),
                'from_email': os.environ.get('FROM_EMAIL', ''),
                'to_email': os.environ.get('TO_EMAIL', 'xiayuyosemi@gmail.com'),
                'subject_prefix': os.environ.get('SUBJECT_PREFIX', '[Twitter Alert]')
            }
            
            # Check if SMTP_PASSWORD is set in environment
            if 'SMTP_PASSWORD' in os.environ:
                default_config['smtp_password'] = os.environ.get('SMTP_PASSWORD')
            else:
                default_config['smtp_password'] = ''
                logging.warning("SMTP_PASSWORD environment variable not set. Email alerts will not work.")
                
            return default_config
    
    def send_alert(self, subject, message, error=None, data=None):
        """Send an email alert"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config['from_email']
            msg['To'] = self.config['to_email']
            msg['Subject'] = f"{self.config['subject_prefix']} {subject}"
            
            # Add timestamp to message
            body = f"Timestamp: {datetime.now().isoformat()}\n\n"
            body += f"Message: {message}\n\n"
            
            # Add error details if provided
            if error:
                body += f"Error: {str(error)}\n\n"
            
            # Add data if provided
            if data:
                body += f"Data: {json.dumps(data, indent=2)}\n\n"
            
            # Add server information
            body += f"Server: {os.uname().nodename}\n"
            body += f"Process ID: {os.getpid()}\n"
            
            # Attach body to message
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['smtp_username'], self.config['smtp_password'])
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logging.info(f"Sent email alert: {subject}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error sending email alert: {str(e)}")
            return False
