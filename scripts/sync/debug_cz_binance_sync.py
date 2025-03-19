#!/usr/bin/env python3

import os
import sys
import logging
import sqlite3
import pymysql
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_sqlite_connection(db_path):
    """Get SQLite connection"""
    return sqlite3.connect(db_path)

def get_mysql_connection():
    """Get MySQL connection"""
    mysql_host = os.getenv('MYSQL_HOST', '43.135.26.222')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'z1050493759')
    mysql_database = os.getenv('MYSQL_DATABASE', 'kol_info')
    
    # Connect to MySQL
    conn = pymysql.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )
    return conn

def get_mysql_table_columns(mysql_conn, table_name):
    """Get column names from MySQL table"""
    cursor = mysql_conn.cursor()
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns

def debug_cz_binance_sync(test_mode=True):
    """Debug synchronization of cz_binance record"""
    try:
        # Connect to databases
        sqlite_conn = get_sqlite_connection('/home/ubuntu/nitterlocal/data/local_database.db')
        mysql_conn = get_mysql_connection()
        
        # Get cz_binance record from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM url_tracking WHERE user_id = '902926941413453824'")
        row = sqlite_cursor.fetchone()
        
        if not row:
            logging.error("cz_binance record not found in SQLite")
            return False
        
        # Get column names from SQLite
        sqlite_columns = [column[0] for column in sqlite_cursor.description]
        row_dict = dict(zip(sqlite_columns, row))
        
        logging.info(f"Found cz_binance record in SQLite: {row_dict}")
        
        # Get MySQL table columns
        mysql_columns = get_mysql_table_columns(mysql_conn, "kol_info")
        logging.info(f"MySQL kol_info columns: {mysql_columns}")
        
        # Check if record exists in MySQL
        mysql_cursor = mysql_conn.cursor()
        mysql_cursor.execute(
            "SELECT * FROM kol_info WHERE kol_id = %s",
            (row_dict['user_id'],)
        )
        existing_record = mysql_cursor.fetchone()
        
        if existing_record:
            logging.info(f"Record exists in MySQL: {existing_record}")
            
            # Update existing record
            set_clauses = []
            update_params = []
            
            # Get Twitter handle from URL
            twitter_handle = None
            url = row_dict.get('url', '')
            if url and 'twitter.com/' in url:
                parts = url.split('twitter.com/')
                if len(parts) > 1:
                    twitter_handle = parts[1].split('/')[0].split('?')[0]
            
            # Add kol_screen_name
            if 'kol_screen_name' in mysql_columns:
                set_clauses.append("kol_screen_name = %s")
                update_params.append(twitter_handle or '')
            
            # Add description
            if 'description' in mysql_columns and 'description' in row_dict:
                set_clauses.append("description = %s")
                update_params.append(row_dict['description'] or '')
            
            # Add followers_count
            if 'followers_count' in mysql_columns and 'followers_count' in row_dict:
                set_clauses.append("followers_count = %s")
                update_params.append(row_dict['followers_count'] or '0')
            
            # Add following_count
            if 'following_count' in mysql_columns and 'following_count' in row_dict:
                set_clauses.append("following_count = %s")
                update_params.append(int(row_dict['following_count']) if row_dict['following_count'] else 0)
            
            # Add type as first_category
            if 'first_category' in mysql_columns and 'type' in row_dict:
                set_clauses.append("first_category = %s")
                update_params.append(row_dict['type'] or '')
            
            # Add subtype as second_category
            if 'second_category' in mysql_columns and 'subtype' in row_dict:
                set_clauses.append("second_category = %s")
                update_params.append(row_dict['subtype'] or '')
            
            # Add kol_name
            if 'kol_name' in mysql_columns and 'kol_name' in row_dict:
                set_clauses.append("kol_name = %s")
                update_params.append(row_dict['kol_name'] or '')
            
            # Only proceed if there are columns to update
            if set_clauses:
                set_clause = ", ".join(set_clauses)
                update_query = f"UPDATE kol_info SET {set_clause} WHERE kol_id = %s"
                update_params.append(row_dict['user_id'])
                
                logging.info(f"Update query: {update_query}")
                logging.info(f"Update params: {update_params}")
                
                if not test_mode:
                    mysql_cursor.execute(update_query, update_params)
                    mysql_conn.commit()
                    logging.info(f"Updated kol_info record for kol_id: {row_dict['user_id']}")
                else:
                    logging.info(f"Test mode: Would update kol_info record for kol_id: {row_dict['user_id']}")
            else:
                logging.info(f"No columns to update for kol_id: {row_dict['user_id']}")
        else:
            logging.info("Record does not exist in MySQL, will insert new record")
            
            # Insert new record
            insert_columns = ['kol_id']
            insert_values = [row_dict['user_id']]
            
            # Get Twitter handle from URL
            twitter_handle = None
            url = row_dict.get('url', '')
            if url and 'twitter.com/' in url:
                parts = url.split('twitter.com/')
                if len(parts) > 1:
                    twitter_handle = parts[1].split('/')[0].split('?')[0]
            
            # Add kol_screen_name
            if 'kol_screen_name' in mysql_columns:
                insert_columns.append('kol_screen_name')
                insert_values.append(twitter_handle or '')
            
            # Add created_at
            if 'created_at' in mysql_columns:
                insert_columns.append('created_at')
                insert_values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Add description
            if 'description' in mysql_columns and 'description' in row_dict:
                insert_columns.append('description')
                insert_values.append(row_dict['description'] or '')
            
            # Add followers_count
            if 'followers_count' in mysql_columns and 'followers_count' in row_dict:
                insert_columns.append('followers_count')
                insert_values.append(row_dict['followers_count'] or '0')
            
            # Add following_count
            if 'following_count' in mysql_columns and 'following_count' in row_dict:
                insert_columns.append('following_count')
                insert_values.append(int(row_dict['following_count']) if row_dict['following_count'] else 0)
            
            # Add type as first_category
            if 'first_category' in mysql_columns and 'type' in row_dict:
                insert_columns.append('first_category')
                insert_values.append(row_dict['type'] or '')
            
            # Add subtype as second_category
            if 'second_category' in mysql_columns and 'subtype' in row_dict:
                insert_columns.append('second_category')
                insert_values.append(row_dict['subtype'] or '')
            
            # Add kol_name
            if 'kol_name' in mysql_columns and 'kol_name' in row_dict:
                insert_columns.append('kol_name')
                insert_values.append(row_dict['kol_name'] or '')
            
            # Build the query
            columns_str = ", ".join(insert_columns)
            placeholders = ", ".join(["%s"] * len(insert_columns))
            insert_query = f"INSERT INTO kol_info ({columns_str}) VALUES ({placeholders})"
            
            logging.info(f"Insert query: {insert_query}")
            logging.info(f"Insert values: {insert_values}")
            
            if not test_mode:
                mysql_cursor.execute(insert_query, insert_values)
                mysql_conn.commit()
                logging.info(f"Inserted new kol_info record for kol_id: {row_dict['user_id']}")
            else:
                logging.info(f"Test mode: Would insert new kol_info record for kol_id: {row_dict['user_id']}")
        
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()
        
        return True
    
    except Exception as e:
        logging.error(f"Error debugging cz_binance sync: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug cz_binance synchronization')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no changes to MySQL)')
    args = parser.parse_args()
    
    debug_cz_binance_sync(args.test)
