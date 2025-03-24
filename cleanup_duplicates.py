#!/usr/bin/env python3
"""
Script to clean up duplicate kol_id values in the MySQL database.
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
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        logging.error(f"Error connecting to MySQL: {e}")
        return None

def find_duplicates(cursor):
    """
    Find duplicate kol_id values in the kol_character table
    """
    cursor.execute("""
        SELECT kol_id, COUNT(*) as count 
        FROM kol_character 
        GROUP BY kol_id 
        HAVING count > 1
    """)
    return cursor.fetchall()

def cleanup_duplicates(host, user, password, database, dry_run=True):
    """
    Clean up duplicate kol_id values in the kol_character table
    """
    conn = get_mysql_connection(host, user, password, database)
    if not conn:
        return
    
    try:
        with conn.cursor() as cursor:
            # Find duplicate kol_id values
            duplicates = find_duplicates(cursor)
            
            if not duplicates:
                logging.info("No duplicate kol_id values found.")
                return
            
            logging.info(f"Found {len(duplicates)} kol_id values with duplicates:")
            
            for dup in duplicates:
                kol_id = dup['kol_id']
                count = dup['count']
                logging.info(f"kol_id: {kol_id}, count: {count}")
                
                # Get details of the duplicate records
                cursor.execute("""
                    SELECT id, kol_id, kol_screen_name 
                    FROM kol_character 
                    WHERE kol_id = %s
                    ORDER BY id
                """, (kol_id,))
                records = cursor.fetchall()
                
                # Log the duplicate records
                for rec in records:
                    logging.info(f"  id: {rec['id']}, kol_id: {rec['kol_id']}, kol_screen_name: {rec['kol_screen_name']}")
                
                # Keep the record with the lowest ID (oldest) and delete the rest
                keep_id = records[0]['id']
                delete_ids = [rec['id'] for rec in records[1:]]
                
                logging.info(f"  Keeping record with id: {keep_id}")
                logging.info(f"  Deleting records with ids: {delete_ids}")
                
                if not dry_run:
                    # Delete the duplicate records
                    for delete_id in delete_ids:
                        cursor.execute("DELETE FROM kol_character WHERE id = %s", (delete_id,))
                    
                    # Commit the changes
                    conn.commit()
                    logging.info(f"  Deleted {len(delete_ids)} duplicate records for kol_id: {kol_id}")
                else:
                    logging.info("  Dry run mode - no changes made")
            
            # Verify the cleanup
            if not dry_run:
                remaining_duplicates = find_duplicates(cursor)
                if remaining_duplicates:
                    logging.warning(f"There are still {len(remaining_duplicates)} kol_id values with duplicates after cleanup")
                else:
                    logging.info("All duplicates have been cleaned up successfully")
    
    except Exception as e:
        logging.error(f"Error cleaning up duplicates: {e}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Clean up duplicate kol_id values in MySQL')
    parser.add_argument('--host', default='43.135.26.222', help='MySQL host')
    parser.add_argument('--user', default='root', help='MySQL user')
    parser.add_argument('--password', required=True, help='MySQL password')
    parser.add_argument('--database', default='kol_info', help='MySQL database')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode - no changes will be made')
    
    args = parser.parse_args()
    
    cleanup_duplicates(args.host, args.user, args.password, args.database, args.dry_run)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Error: MySQL password is required")
        print("Usage: python cleanup_duplicates.py --password YOUR_PASSWORD [--dry-run]")
        sys.exit(1)
    main()
