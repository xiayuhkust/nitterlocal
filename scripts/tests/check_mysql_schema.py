#!/usr/bin/env python3
"""
Script to check MySQL schema and test the synchronization fix.
"""

import os
import sys
import logging
import mysql.connector
import sqlite3
import dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
dotenv.load_dotenv()

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        # Get MySQL connection parameters from environment variables
        mysql_host = os.getenv('MYSQL_HOST', '43.135.26.222')
        mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
        mysql_user = os.getenv('MYSQL_USER', 'root')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'z1050493759')
        mysql_database = os.getenv('MYSQL_DATABASE', 'kol_info')
        
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {str(e)}")
        raise

def get_sqlite_connection(db_path='/home/ubuntu/nitterlocal/data/local_database.db'):
    """Get a connection to the SQLite database"""
    try:
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        return conn
    
    except Exception as e:
        logging.error(f"Error connecting to SQLite: {str(e)}")
        raise

def check_mysql_schema():
    """Check the schema of the MySQL database"""
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    try:
        # Get tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        logging.info(f"MySQL tables:")
        for table in tables:
            table_name = table[0]
            logging.info(f"  {table_name}")
            
            # Get columns
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            logging.info(f"  Schema for {table_name}:")
            for column in columns:
                logging.info(f"    {column[0]} - {column[1]}")
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
            rows = cursor.fetchall()
            
            if rows:
                column_names = [column[0] for column in cursor.description]
                
                logging.info(f"  Sample data from {table_name}:")
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    logging.info(f"    {row_dict}")
            
            logging.info("")
    
    finally:
        cursor.close()
        conn.close()

def check_sqlite_schema():
    """Check the schema of the SQLite database"""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    try:
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        logging.info(f"SQLite tables:")
        for table in tables:
            table_name = table[0]
            logging.info(f"  {table_name}")
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            logging.info(f"  Schema for {table_name}:")
            for column in columns:
                logging.info(f"    {column[1]} - {column[2]}")
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
            rows = cursor.fetchall()
            
            if rows:
                column_names = [column[0] for column in cursor.description]
                
                logging.info(f"  Sample data from {table_name}:")
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    logging.info(f"    {row_dict}")
            
            logging.info("")
    
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function"""
    logging.info("Checking MySQL schema...")
    check_mysql_schema()
    
    logging.info("Checking SQLite schema...")
    check_sqlite_schema()
    
    logging.info("Schema check completed")

if __name__ == "__main__":
    main()
