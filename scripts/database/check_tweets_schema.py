#!/usr/bin/env python3
"""
Script to check the schema of the tweets table in the SQLite database.
"""

import os
import sqlite3
import json

# Path to the SQLite database
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')

def get_table_schema(table_name):
    """Get the schema of a table in the SQLite database"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    # Get sample data
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
    sample_data = cursor.fetchone()
    
    conn.close()
    
    return columns, sample_data

def main():
    """Main function"""
    print(f"Checking schema of tweets table in {SQLITE_DB_PATH}")
    
    # Get schema and sample data
    columns, sample_data = get_table_schema('tweets')
    
    # Print schema
    print("\nTweets Table Schema:")
    print("--------------------")
    for col in columns:
        col_id, name, type_, notnull, default_value, pk = col
        print(f"{name} ({type_}){' PRIMARY KEY' if pk else ''}{' NOT NULL' if notnull else ''}{f' DEFAULT {default_value}' if default_value is not None else ''}")
    
    # Print sample data if available
    if sample_data:
        print("\nSample Data:")
        print("------------")
        sample_dict = {}
        for i, col in enumerate(columns):
            col_id, name, type_, notnull, default_value, pk = col
            sample_dict[name] = sample_data[i]
        
        print(json.dumps(sample_dict, indent=2))
    else:
        print("\nNo sample data available.")

if __name__ == "__main__":
    main()
