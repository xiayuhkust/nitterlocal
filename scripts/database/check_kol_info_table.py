#!/usr/bin/env python3
"""
Script to check the structure of the kol_info table in the MySQL database.
"""

import mysql.connector
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# MySQL connection parameters
MYSQL_HOST = "43.135.26.222"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "z1050493759"

def check_kol_info_table():
    """Check if the kol_info table exists and its structure"""
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
            
            # Check if the kol_info database exists
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES;")
            databases = cursor.fetchall()
            logging.info("Available databases:")
            for db in databases:
                logging.info(f"  - {db[0]}")
            
            # Check if we can connect to the kol_info database
            try:
                cursor.execute("USE kol_info;")
                logging.info("Connected to kol_info database")
                
                # Check if the kol_info table exists
                cursor.execute("SHOW TABLES;")
                tables = cursor.fetchall()
                logging.info("Tables in the kol_info database:")
                for table in tables:
                    logging.info(f"  - {table[0]}")
                
                # Check the structure of the kol_info table
                if ('kol_info',) in tables:
                    cursor.execute("DESCRIBE kol_info;")
                    columns = cursor.fetchall()
                    logging.info("Structure of the kol_info table:")
                    for column in columns:
                        logging.info(f"  - {column[0]}: {column[1]}")
                else:
                    logging.warning("kol_info table does not exist in the kol_info database")
            except mysql.connector.Error as e:
                logging.error(f"Error connecting to kol_info database: {e}")
            
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
    check_kol_info_table()
