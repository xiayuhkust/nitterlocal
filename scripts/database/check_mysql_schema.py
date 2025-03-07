#!/usr/bin/env python3
"""
Script to check the MySQL schema for the kol_info and kol_tweet tables.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
load_dotenv()

# MySQL connection parameters
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "kol_info")

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        return conn
    except ImportError:
        logging.error("MySQL Connector for Python is not installed. Please install it with 'pip install mysql-connector-python'")
        sys.exit(1)
    except Exception as e:
        logging.error("Error connecting to MySQL database: {}".format(str(e)))
        sys.exit(1)

def check_table_schema(table_name):
    """Check the schema of a table"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("DESCRIBE {}".format(table_name))
        
        columns = []
        for column in cursor.fetchall():
            columns.append({
                'Field': column[0],
                'Type': column[1],
                'Null': column[2],
                'Key': column[3],
                'Default': column[4],
                'Extra': column[5]
            })
        
        conn.close()
        
        return columns
    except Exception as e:
        logging.error("Error checking schema for table {}: {}".format(table_name, str(e)))
        return None

def main():
    """Main function"""
    print("Checking MySQL schema for kol_info and kol_tweet tables")
    print("MySQL Host: {}".format(MYSQL_HOST))
    print("MySQL Port: {}".format(MYSQL_PORT))
    print("MySQL User: {}".format(MYSQL_USER))
    print("MySQL Database: {}".format(MYSQL_DATABASE))
    
    # Check kol_info table schema
    print("\nChecking kol_info table schema:")
    kol_info_schema = check_table_schema("kol_info")
    if kol_info_schema:
        for column in kol_info_schema:
            print("  {}: {} ({})".format(column['Field'], column['Type'], column['Key']))
    
    # Check kol_tweet table schema
    print("\nChecking kol_tweet table schema:")
    kol_tweet_schema = check_table_schema("kol_tweet")
    if kol_tweet_schema:
        for column in kol_tweet_schema:
            print("  {}: {} ({})".format(column['Field'], column['Type'], column['Key']))

if __name__ == "__main__":
    main()
