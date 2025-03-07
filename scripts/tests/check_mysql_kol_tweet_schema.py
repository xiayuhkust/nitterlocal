#!/usr/bin/env python3
"""
Script to check the schema of the kol_tweet table in the MySQL database.
"""

import os
import sys
import logging

# Try to import dotenv for environment variable management
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed, using environment variables directly")
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# MySQL connection parameters
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "kol_info")

def check_mysql_kol_tweet_schema():
    """Check the schema of the kol_tweet table in the MySQL database"""
    try:
        import mysql.connector
        print(f"Connecting to MySQL database at {MYSQL_HOST}:{MYSQL_PORT}...")
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        
        print("Successfully connected to MySQL database!")
        
        # Check if kol_tweet table exists
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'kol_tweet'")
        if cursor.fetchone():
            print("\nkol_tweet table exists. Checking schema...")
            cursor.execute("DESCRIBE kol_tweet")
            columns = cursor.fetchall()
            
            print("\nkol_tweet table schema:")
            for column in columns:
                print(f"- {column[0]} ({column[1]})")
            
            # Check if there are any records in the table
            cursor.execute("SELECT COUNT(*) FROM kol_tweet")
            count = cursor.fetchone()[0]
            print(f"\nkol_tweet table has {count} records")
            
            if count > 0:
                # Get a sample record
                cursor.execute("SELECT * FROM kol_tweet LIMIT 1")
                sample = cursor.fetchone()
                column_names = [i[0] for i in cursor.description]
                
                print("\nSample record:")
                for i, name in enumerate(column_names):
                    print(f"- {name}: {sample[i]}")
        else:
            print("\nkol_tweet table does not exist")
        
        conn.close()
        print("\nConnection closed")
        return True
    except ImportError:
        print("MySQL Connector for Python is not installed. Please install it with 'pip install mysql-connector-python'")
        return False
    except Exception as e:
        print(f"Error connecting to MySQL database: {str(e)}")
        return False

if __name__ == "__main__":
    print("Checking MySQL kol_tweet table schema")
    print(f"MySQL Host: {MYSQL_HOST}")
    print(f"MySQL Port: {MYSQL_PORT}")
    print(f"MySQL User: {MYSQL_USER}")
    print(f"MySQL Database: {MYSQL_DATABASE}")
    
    success = check_mysql_kol_tweet_schema()
    
    if success:
        print("\nMySQL kol_tweet schema check successful!")
        sys.exit(0)
    else:
        print("\nMySQL kol_tweet schema check failed!")
        sys.exit(1)
