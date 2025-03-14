#!/usr/bin/env python3
"""
Script to test MySQL connection parameters.
"""

import os
import sys
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_mysql_connection():
    """Test MySQL connection parameters"""
    try:
        # Try to import MySQL connector
        import mysql.connector
        
        # Get MySQL connection parameters from environment variables
        mysql_host = os.environ.get("MYSQL_HOST", "localhost")
        mysql_port = int(os.environ.get("MYSQL_PORT", "3306"))
        mysql_user = os.environ.get("MYSQL_USER", "root")
        mysql_password = os.environ.get("MYSQL_PASSWORD", "")
        mysql_database = os.environ.get("MYSQL_DATABASE", "kol_info")
        
        # Print connection parameters (without password)
        print(f"MySQL Host: {mysql_host}")
        print(f"MySQL Port: {mysql_port}")
        print(f"MySQL User: {mysql_user}")
        print(f"MySQL Database: {mysql_database}")
        
        # Try to connect to MySQL
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        
        print("Successfully connected to MySQL database!")
        
        # Check if required tables exist
        cursor = conn.cursor()
        
        # Check kol_info table
        cursor.execute("SHOW TABLES LIKE 'kol_info'")
        if cursor.fetchone():
            print("kol_info table exists")
        else:
            print("kol_info table does not exist")
        
        # Check kol_character table
        cursor.execute("SHOW TABLES LIKE 'kol_character'")
        if cursor.fetchone():
            print("kol_character table exists")
        else:
            print("kol_character table does not exist")
        
        # Check kol_tweet table
        cursor.execute("SHOW TABLES LIKE 'kol_tweet'")
        if cursor.fetchone():
            print("kol_tweet table exists")
        else:
            print("kol_tweet table does not exist")
        
        # Close the connection
        conn.close()
        
        return True
    except ImportError:
        print("MySQL Connector for Python is not installed. Please install it with 'pip install mysql-connector-python'")
        return False
    except Exception as e:
        print(f"Error connecting to MySQL database: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test MySQL connection parameters')
    
    args = parser.parse_args()
    
    # Test MySQL connection
    success = test_mysql_connection()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
