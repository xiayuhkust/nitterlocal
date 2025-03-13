#!/usr/bin/env python3
"""
Script to synchronize the kol_character table from SQLite to MySQL.
This script synchronizes data from the kol_character table in SQLite to MySQL.
"""

import os
import sys
import logging
import sqlite3
import argparse
from datetime import datetime

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

def get_sqlite_connection(db_path):
    """Get a connection to the SQLite database"""
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)

def get_mysql_connection():
    """Get a connection to the MySQL database"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            autocommit=False
        )
        return conn
    except ImportError:
        logging.error("MySQL Connector for Python is not installed. Please install it with 'pip install mysql-connector-python'")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error connecting to MySQL database: {str(e)}")
        sys.exit(1)

def get_kol_characters_from_sqlite(db_path, limit=None):
    """Get KOL characters from the SQLite database"""
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()
    
    query = "SELECT * FROM kol_character"
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    
    columns = [column[0] for column in cursor.description]
    kol_characters = []
    
    for row in cursor.fetchall():
        kol_data = dict(zip(columns, row))
        kol_characters.append(kol_data)
    
    conn.close()
    
    return kol_characters

def insert_or_update_kol_character(mysql_conn, kol_data):
    """Insert or update a KOL character in MySQL"""
    cursor = None
    try:
        # Check if the record already exists
        cursor = mysql_conn.cursor()
        cursor.execute(
            "SELECT id FROM kol_character WHERE kol_screen_name = %s",
            (kol_data['kol_screen_name'],)
        )
        
        result = cursor.fetchone()
        cursor.close()
        
        # Create a new cursor for the update or insert
        cursor = mysql_conn.cursor()
        
        # Convert kol_id to numeric if possible, otherwise use NULL
        kol_id = None
        if kol_data['kol_id'] and kol_data['kol_id'].isdigit():
            kol_id = int(kol_data['kol_id'])
        
        if result:
            # Update existing record
            update_query = """
            UPDATE kol_character SET
                kol_id = %s,
                bio = %s,
                lore = %s,
                knowledge = %s,
                postExamples = %s,
                topics = %s,
                style_all = %s,
                style_chat = %s,
                style_post = %s,
                adjectives = %s
            WHERE kol_screen_name = %s
            """
            
            cursor.execute(
                update_query,
                (
                    kol_id,
                    kol_data.get('bio', ''),
                    kol_data.get('lore', ''),
                    kol_data.get('knowledge', ''),
                    kol_data.get('postExamples', ''),
                    kol_data.get('topics', ''),
                    kol_data.get('style_all', ''),
                    kol_data.get('style_chat', ''),
                    kol_data.get('style_post', ''),
                    kol_data.get('adjectives', ''),
                    kol_data['kol_screen_name']
                )
            )
            
            logging.info(f"Updated record for kol_screen_name: {kol_data['kol_screen_name']}")
        else:
            # Insert new record
            insert_query = """
            INSERT INTO kol_character (
                kol_id, kol_screen_name, bio, lore, knowledge, postExamples,
                topics, style_all, style_chat, style_post, adjectives
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            cursor.execute(
                insert_query,
                (
                    kol_id,
                    kol_data['kol_screen_name'],
                    kol_data.get('bio', ''),
                    kol_data.get('lore', ''),
                    kol_data.get('knowledge', ''),
                    kol_data.get('postExamples', ''),
                    kol_data.get('topics', ''),
                    kol_data.get('style_all', ''),
                    kol_data.get('style_chat', ''),
                    kol_data.get('style_post', ''),
                    kol_data.get('adjectives', '')
                )
            )
            
            logging.info(f"Inserted new record for kol_screen_name: {kol_data['kol_screen_name']}")
        
        mysql_conn.commit()
        cursor.close()
        
    except Exception as e:
        logging.error(f"Error inserting or updating record for kol_screen_name {kol_data['kol_screen_name']}: {str(e)}")
        if mysql_conn:
            mysql_conn.rollback()
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Synchronize kol_character table from SQLite to MySQL')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db', help='Path to the SQLite database')
    parser.add_argument('--limit', type=int, help='Limit the number of records to process')
    parser.add_argument('--test', action='store_true', help='Test mode - do not insert or update records in MySQL')
    
    args = parser.parse_args()
    
    print("Starting kol_character synchronization")
    logging.info("Starting kol_character synchronization")
    
    # Print environment variables (without password)
    print(f"MySQL Host: {MYSQL_HOST}")
    print(f"MySQL Port: {MYSQL_PORT}")
    print(f"MySQL User: {MYSQL_USER}")
    print(f"MySQL Database: {MYSQL_DATABASE}")
    
    # Get KOL characters from SQLite
    kol_characters = get_kol_characters_from_sqlite(args.db_path, args.limit)
    logging.info(f"Got {len(kol_characters)} KOL characters from SQLite")
    
    # Connect to MySQL
    mysql_conn = None
    if not args.test:
        mysql_conn = get_mysql_connection()
        logging.info("Connected to MySQL database")
    
    # Process each KOL character
    processed_count = 0
    try:
        for kol_data in kol_characters:
            # Insert or update record in MySQL
            if not args.test:
                insert_or_update_kol_character(mysql_conn, kol_data)
            else:
                logging.info(f"Test mode - would insert or update record for kol_screen_name: {kol_data['kol_screen_name']}")
            
            processed_count += 1
    except Exception as e:
        logging.error(f"Error processing KOL characters: {str(e)}")
    finally:
        # Close MySQL connection
        if mysql_conn:
            mysql_conn.close()
            logging.info("Closed MySQL connection")
    
    logging.info(f"Processed {processed_count} KOL characters")
    logging.info("kol_character synchronization completed")

if __name__ == "__main__":
    main()
