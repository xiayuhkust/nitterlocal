#!/usr/bin/env python3
"""
Script to check the MySQL database schema.
This script helps diagnose synchronization issues by showing the table structure.
"""

import os
import sys
import mysql.connector
import dotenv
from datetime import datetime

# Load environment variables
dotenv.load_dotenv()

# MySQL connection parameters
MYSQL_HOST = os.environ.get("MYSQL_HOST", "43.135.26.222")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "kol_info")

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        return conn
    except Exception as e:
        print(f"Error connecting to MySQL: {str(e)}")
        sys.exit(1)

def check_table_schema(table_name):
    """Check the schema of a MySQL table"""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    print(f"MySQL Host: {MYSQL_HOST}")
    print(f"MySQL Database: {MYSQL_DATABASE}")
    print(f"\n=== Schema for table '{table_name}' ===")
    
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"Table '{table_name}' not found or has no columns.")
        else:
            print(f"{'Field':<20} {'Type':<20} {'Null':<6} {'Key':<6} {'Default':<15} {'Extra'}")
            print("-" * 80)
            for column in columns:
                print(f"{column[0]:<20} {column[1]:<20} {column[2]:<6} {column[3]:<6} {str(column[4]):<15} {column[5]}")
    except Exception as e:
        print(f"Error describing table: {str(e)}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
    else:
        table_name = "kol_info"
    
    check_table_schema(table_name)
