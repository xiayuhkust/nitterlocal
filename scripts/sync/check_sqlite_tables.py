#!/usr/bin/env python3
"""
Script to check the SQLite database tables and structure.
This script helps diagnose synchronization issues by showing the table structure.
"""

import os
import sys
import sqlite3
import json

# Path to the SQLite database
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')

def get_sqlite_connection():
    """Get a connection to the SQLite database"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        return conn
    except Exception as e:
        print(f"Error connecting to SQLite: {str(e)}")
        sys.exit(1)

def list_tables():
    """List all tables in the SQLite database"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    print(f"SQLite Database: {SQLITE_DB_PATH}")
    print("\n=== Tables in SQLite Database ===")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    if not tables:
        print("No tables found in the database.")
    else:
        for table in tables:
            print(f"- {table[0]}")
    
    conn.close()

def check_table_schema(table_name):
    """Check the schema of a SQLite table"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    print(f"\n=== Schema for table '{table_name}' ===")
    
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"Table '{table_name}' not found or has no columns.")
        else:
            print(f"{'ID':<5} {'Name':<20} {'Type':<15} {'NotNull':<8} {'Default':<15} {'PK'}")
            print("-" * 70)
            for column in columns:
                print(f"{column[0]:<5} {column[1]:<20} {column[2]:<15} {column[3]:<8} {str(column[4]):<15} {column[5]}")
    except Exception as e:
        print(f"Error describing table: {str(e)}")
    
    conn.close()

def count_records(table_name):
    """Count the number of records in a table"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\n=== Record Count for '{table_name}' ===")
        print(f"Total records: {count}")
    except Exception as e:
        print(f"Error counting records: {str(e)}")
    
    conn.close()

def show_sample_record(table_name, limit=1):
    """Show a sample record from the table"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"\nNo records found in table '{table_name}'.")
            return
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"\n=== Sample Record from '{table_name}' ===")
        
        for row in rows:
            record = dict(zip(columns, row))
            print(json.dumps(record, indent=2, default=str))
    except Exception as e:
        print(f"Error showing sample record: {str(e)}")
    
    conn.close()

if __name__ == "__main__":
    list_tables()
    
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
        check_table_schema(table_name)
        count_records(table_name)
        show_sample_record(table_name)
