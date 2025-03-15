#!/usr/bin/env python3
"""
Detailed logging module for tracking data additions across different tables.
This module provides functions for logging detailed information about data operations.
"""

import os
import logging
import json
from datetime import datetime

# Configure logging
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/logs')
os.makedirs(LOGS_DIR, exist_ok=True)

SYNC_DETAILS_LOG = os.path.join(LOGS_DIR, 'sync_details.log')

# Initialize the log file if it doesn't exist
if not os.path.exists(SYNC_DETAILS_LOG):
    with open(SYNC_DETAILS_LOG, 'w') as f:
        f.write(f"# Sync Details Log - Created {datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')}\n\n")

def log_data_operation(operation_type, table_name, record_count, details=None):
    """Log a data operation with detailed information"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_entry = {
        'timestamp': timestamp,
        'operation': operation_type,
        'table': table_name,
        'count': record_count
    }
    
    if details:
        log_entry['details'] = details
    
    with open(SYNC_DETAILS_LOG, 'a') as f:
        f.write(f"{json.dumps(log_entry)}\n")
    
    # Also log to standard logging
    logging.info(f"{operation_type}: {record_count} records in {table_name}")

def log_sync_summary(tables_updated, total_records, duration, success=True):
    """Log a summary of a synchronization operation"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_entry = {
        'timestamp': timestamp,
        'operation': 'sync_summary',
        'tables_updated': tables_updated,
        'total_records': total_records,
        'duration_seconds': duration,
        'success': success
    }
    
    with open(SYNC_DETAILS_LOG, 'a') as f:
        f.write(f"{json.dumps(log_entry)}\n")
    
    # Also log to standard logging
    logging.info(f"Sync summary: {total_records} records across {len(tables_updated)} tables in {duration:.2f} seconds")
