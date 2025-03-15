#!/usr/bin/env python3
"""
Script to view and analyze the detailed sync logs.
This script provides a summary of the data operations logged in the sync_details.log file.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the detailed logger
from src.utils.detailed_logger import SYNC_DETAILS_LOG

def parse_log_entries(since_hours=None):
    """Parse the log entries from the sync_details.log file"""
    entries = []
    
    if not os.path.exists(SYNC_DETAILS_LOG):
        print(f"Log file not found: {SYNC_DETAILS_LOG}")
        return entries
    
    with open(SYNC_DETAILS_LOG, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                entry = json.loads(line)
                
                # Filter by time if specified
                if since_hours:
                    entry_time = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
                    cutoff_time = datetime.now() - timedelta(hours=since_hours)
                    if entry_time < cutoff_time:
                        continue
                
                entries.append(entry)
            except json.JSONDecodeError:
                print(f"Error parsing log entry: {line}")
                continue
    
    return entries

def summarize_entries(entries):
    """Summarize the log entries"""
    if not entries:
        print("No log entries found.")
        return
    
    # Group by operation and table
    operation_summary = {}
    table_summary = {}
    
    for entry in entries:
        operation = entry.get('operation')
        table = entry.get('table')
        count = entry.get('count', 0)
        
        if operation:
            if operation not in operation_summary:
                operation_summary[operation] = {
                    'count': 0,
                    'entries': 0
                }
            
            operation_summary[operation]['count'] += count
            operation_summary[operation]['entries'] += 1
        
        if table:
            if table not in table_summary:
                table_summary[table] = {
                    'count': 0,
                    'entries': 0
                }
            
            table_summary[table]['count'] += count
            table_summary[table]['entries'] += 1
    
    # Print summary
    print("\nOperation Summary:")
    print("------------------")
    for operation, data in operation_summary.items():
        print(f"{operation}: {data['count']} records in {data['entries']} operations")
    
    print("\nTable Summary:")
    print("-------------")
    for table, data in table_summary.items():
        print(f"{table}: {data['count']} records in {data['entries']} operations")
    
    # Print the most recent entries
    print("\nMost Recent Entries:")
    print("-------------------")
    for entry in entries[-5:]:
        timestamp = entry.get('timestamp', 'Unknown')
        operation = entry.get('operation', 'Unknown')
        table = entry.get('table', 'Unknown')
        count = entry.get('count', 0)
        
        print(f"{timestamp} - {operation} - {table}: {count} records")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='View and analyze the detailed sync logs')
    parser.add_argument('--since-hours', type=int, default=24, help='Only show entries from the last N hours')
    
    args = parser.parse_args()
    
    print(f"Viewing sync details log: {SYNC_DETAILS_LOG}")
    print(f"Showing entries from the last {args.since_hours} hours")
    
    entries = parse_log_entries(args.since_hours)
    summarize_entries(entries)

if __name__ == "__main__":
    main()
