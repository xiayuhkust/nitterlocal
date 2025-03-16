#!/usr/bin/env python3
"""
Script to display the current url_tracking schema and data for cz_binance.
"""

import os
import sys
import logging
import sqlite3
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def display_url_tracking_schema(db_path):
    """Display the schema of the url_tracking table"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the schema
        cursor.execute("PRAGMA table_info(url_tracking)")
        schema = cursor.fetchall()
        
        print("\n=== Schema for table 'url_tracking' ===")
        print("ID    Name                 Type            NotNull  Default         PK")
        print("----------------------------------------------------------------------")
        for column in schema:
            print(f"{column[0]:<5} {column[1]:<20} {column[2]:<15} {column[3]:<8} {str(column[4]):<15} {column[5]}")
        
        return True
    except Exception as e:
        logging.error(f"Error displaying schema: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def display_cz_binance_data(db_path):
    """Display data for cz_binance in url_tracking and kol_character tables"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get data from url_tracking table
        cursor.execute("SELECT * FROM url_tracking WHERE screen_name = ? OR url LIKE ?", 
                      ('cz_binance', '%cz_binance%'))
        url_record = cursor.fetchone()
        
        if url_record:
            url_data = dict(url_record)
            
            print("\n=== Data for cz_binance in url_tracking table ===")
            
            # Display basic fields
            basic_fields = ['id', 'url', 'user_id', 'status', 'type', 'subtype', 'screen_name']
            for field in basic_fields:
                if field in url_data:
                    print(f"{field}: {url_data[field]}")
            
            # Display profile fields
            print("\n=== Profile Data in url_tracking table ===")
            profile_fields = [
                'followers_count', 'following_count', 'tweet_count',
                'profile_image_url', 'profile_banner_url', 'verified',
                'location', 'description', 'created_at', 'profile_updated_at'
            ]
            for field in profile_fields:
                if field in url_data and url_data[field] is not None:
                    print(f"{field}: {url_data[field]}")
            
            # Get data from kol_character table
            if 'id' in url_data:
                cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ? OR kol_screen_name = ?", 
                              (url_data['id'], 'cz_binance'))
                kol_record = cursor.fetchone()
                
                if kol_record:
                    print("\n=== Data for cz_binance in kol_character table ===")
                    kol_data = dict(kol_record)
                    for key, value in kol_data.items():
                        print(f"{key}: {value}")
                else:
                    print("\nNo corresponding record found in kol_character table")
        else:
            print(f"\nNo data found for cz_binance in url_tracking table")
        
        return True
    except Exception as e:
        logging.error(f"Error displaying data: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Display url_tracking schema and cz_binance data')
    parser.add_argument('--db-path', default='/home/ubuntu/nitterlocal/data/local_database.db', 
                       help='Path to SQLite database')
    args = parser.parse_args()
    
    # Display the schema
    display_url_tracking_schema(args.db_path)
    
    # Display cz_binance data
    display_cz_binance_data(args.db_path)

if __name__ == "__main__":
    main()
