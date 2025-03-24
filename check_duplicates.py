#!/usr/bin/env python3
"""
Script to check for duplicate kol_id values in the MySQL database.
"""
import os
import sys
import logging
import pymysql
import pymysql.cursors
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_mysql_connection(host, user, password, database):
    """
    Get a connection to the MySQL database
    """
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        return conn
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {e}")
        return None

def check_duplicates(host, user, password, database):
    """
    Check for duplicate kol_id values in the kol_character table
    """
    conn = get_mysql_connection(host, user, password, database)
    if not conn:
        return
    
    try:
        with conn.cursor() as cursor:
            # Find duplicate kol_id values
            cursor.execute("""
                SELECT kol_id, COUNT(*) as count 
                FROM kol_character 
                GROUP BY kol_id 
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            
            if not duplicates:
                logging.info("No duplicate kol_id values found.")
                return
            
            logging.info(f"Found {len(duplicates)} kol_id values with duplicates:")
            for dup in duplicates:
                # Using index instead of dictionary access since we're not using DictCursor
                kol_id = dup[0]
                count = dup[1]
                logging.info(f"kol_id: {kol_id}, count: {count}")
                
                # Get details of the duplicate records
                cursor.execute("""
                    SELECT id, kol_id, kol_screen_name 
                    FROM kol_character 
                    WHERE kol_id = %s
                    ORDER BY id
                """, (kol_id,))
                records = cursor.fetchall()
                
                for rec in records:
                    # Using index instead of dictionary access
                    rec_id = rec[0]
                    rec_kol_id = rec[1]
                    rec_kol_screen_name = rec[2]
                    logging.info(f"  id: {rec_id}, kol_id: {rec_kol_id}, kol_screen_name: {rec_kol_screen_name}")
    
    except Exception as e:
        logging.error(f"Error checking duplicates: {e}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Check for duplicate kol_id values in MySQL')
    parser.add_argument('--host', default='43.135.26.222', help='MySQL host')
    parser.add_argument('--user', default='root', help='MySQL user')
    parser.add_argument('--password', required=True, help='MySQL password')
    parser.add_argument('--database', default='kol_info', help='MySQL database')
    
    args = parser.parse_args()
    
    check_duplicates(args.host, args.user, args.password, args.database)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Error: MySQL password is required")
        print("Usage: python check_duplicates.py --password YOUR_PASSWORD")
        sys.exit(1)
    main()
