#!/usr/bin/env python3
"""
Test script to verify connection to the MySQL database.
"""

import os
import mysql.connector
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Try to import dotenv for environment variable management
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
    logging.info("Loaded environment variables from .env file")
except ImportError:
    logging.info("python-dotenv not installed, using environment variables directly")
    pass

# MySQL connection parameters
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")

def test_mysql_connection():
    """Test connection to the MySQL database"""
    try:
        # Connect to the MySQL database
        logging.info(f"Connecting to MySQL database at {MYSQL_HOST}:{MYSQL_PORT}...")
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        
        if connection.is_connected():
            logging.info("Successfully connected to MySQL database")
            db_info = connection.get_server_info()
            logging.info(f"MySQL server version: {db_info}")
            
            # Test if we can execute a query
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES;")
            databases = cursor.fetchall()
            logging.info("Available databases:")
            for db in databases:
                logging.info(f"  - {db[0]}")
            
            return True
    except Exception as e:
        logging.error(f"Error connecting to MySQL database: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            logging.info("MySQL connection closed")

if __name__ == "__main__":
    test_mysql_connection()
