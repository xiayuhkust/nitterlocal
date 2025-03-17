#!/usr/bin/env python3
"""
Script to display the complete database schema and sample data for all tables.
This helps verify the structure of the database and the available fields.
"""

import os
import sys
import sqlite3
import logging
import argparse
import pandas as pd
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def display_database_schema(db_path):
    """Display the complete schema for all tables in the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("\n=== Database Schema ===")
    for table in tables:
        print(f"\nTable: {table}")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Display column information
        print(f"{'ID':<5} {'Name':<25} {'Type':<15} {'NotNull':<10} {'Default':<15} {'PK':<5}")
        print("-" * 75)
        for col in columns:
            col_id, name, type_, not_null, default_val, primary_key = col
            print(f"{col_id:<5} {name:<25} {type_:<15} {not_null:<10} {str(default_val):<15} {primary_key:<5}")
    
    conn.close()

def display_sample_data(db_path, table_name, limit=5):
    """Display sample data for a specific table"""
    conn = sqlite3.connect(db_path)
    
    try:
        # Get column names
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Get sample data
        query = f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        
        print(f"\n=== Sample Data for Table: {table_name} ===")
        if not df.empty:
            # Format the output
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 200)
            pd.set_option('display.max_colwidth', 30)
            
            print(df.to_string())
            print(f"\nShowing {len(df)} of {conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]} records")
        else:
            print(f"No data found in table {table_name}")
    except Exception as e:
        logging.error(f"Error displaying sample data for table {table_name}: {str(e)}")
    
    conn.close()

def display_url_tracking_data(db_path, screen_name=None, limit=5):
    """Display url_tracking data for a specific screen name"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if url_tracking table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_tracking'")
    if not cursor.fetchone():
        logging.error("url_tracking table does not exist in the database")
        conn.close()
        return
    
    # Get all column names for url_tracking table
    cursor.execute("PRAGMA table_info(url_tracking)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Build query
    query = "SELECT * FROM url_tracking"
    params = []
    
    if screen_name:
        # Check if screen_name column exists
        if 'screen_name' in columns:
            query += " WHERE screen_name = ?"
            params = [screen_name]
        else:
            logging.warning("screen_name column does not exist in url_tracking table")
            # Try to find by URL containing the screen name
            query += " WHERE url LIKE ?"
            params = [f"%/{screen_name}%"]
    
    query += f" ORDER BY rowid DESC LIMIT {limit}"
    
    # Execute query
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Display results
    print(f"\n=== URL Tracking Data {f'for {screen_name}' if screen_name else ''} ===")
    if rows:
        # Create a DataFrame for better display
        df = pd.DataFrame(rows, columns=columns)
        
        # Format the output
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        pd.set_option('display.max_colwidth', 30)
        
        print(df.to_string())
        
        # Display column names and values for the first row in a more readable format
        if len(rows) > 0:
            print("\n=== Detailed View of First Record ===")
            for i, col in enumerate(columns):
                print(f"{col}: {rows[0][i]}")
    else:
        print(f"No records found in url_tracking table{f' for {screen_name}' if screen_name else ''}")
    
    conn.close()

def display_kol_character_data(db_path, screen_name=None, limit=5):
    """Display kol_character data for a specific screen name"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if kol_character table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kol_character'")
    if not cursor.fetchone():
        logging.error("kol_character table does not exist in the database")
        conn.close()
        return
    
    # Get all column names for kol_character table
    cursor.execute("PRAGMA table_info(kol_character)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Build query
    query = "SELECT * FROM kol_character"
    params = []
    
    if screen_name:
        # Check if kol_screen_name column exists
        if 'kol_screen_name' in columns:
            query += " WHERE kol_screen_name = ?"
            params = [screen_name]
        else:
            logging.warning("kol_screen_name column does not exist in kol_character table")
    
    query += f" ORDER BY rowid DESC LIMIT {limit}"
    
    # Execute query
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Display results
    print(f"\n=== KOL Character Data {f'for {screen_name}' if screen_name else ''} ===")
    if rows:
        # Create a DataFrame for better display
        df = pd.DataFrame(rows, columns=columns)
        
        # Format the output
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        pd.set_option('display.max_colwidth', 30)
        
        print(df.to_string())
        
        # Display column names and values for the first row in a more readable format
        if len(rows) > 0:
            print("\n=== Detailed View of First Record ===")
            for i, col in enumerate(columns):
                print(f"{col}: {rows[0][i]}")
    else:
        print(f"No records found in kol_character table{f' for {screen_name}' if screen_name else ''}")
    
    conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Display database schema and sample data")
    parser.add_argument("--db-path", default="data/local_database.db", help="Path to the SQLite database")
    parser.add_argument("--table", help="Display sample data for a specific table")
    parser.add_argument("--screen-name", help="Display data for a specific screen name")
    parser.add_argument("--limit", type=int, default=5, help="Limit the number of records to display")
    parser.add_argument("--schema-only", action="store_true", help="Display only the schema without sample data")
    
    args = parser.parse_args()
    
    # Check if the database exists
    if not os.path.exists(args.db_path):
        logging.error(f"Database file not found: {args.db_path}")
        return 1
    
    # Display database schema
    display_database_schema(args.db_path)
    
    if not args.schema_only:
        # Display sample data for a specific table if requested
        if args.table:
            display_sample_data(args.db_path, args.table, args.limit)
        
        # Display data for a specific screen name if requested
        if args.screen_name:
            display_url_tracking_data(args.db_path, args.screen_name, args.limit)
            display_kol_character_data(args.db_path, args.screen_name, args.limit)
        
        # If no specific table or screen name is requested, display sample data for main tables
        if not args.table and not args.screen_name:
            display_sample_data(args.db_path, "url_tracking", args.limit)
            display_sample_data(args.db_path, "kol_character", args.limit)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
