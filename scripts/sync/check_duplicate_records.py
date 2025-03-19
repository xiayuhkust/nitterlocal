#!/usr/bin/env python3

import pymysql
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_duplicate_records():
    """Check for duplicate records in MySQL with the same kol_screen_name"""
    try:
        # Connect to MySQL
        conn = pymysql.connect(
            host='43.135.26.222',
            port=3306,
            user='root',
            password='z1050493759',
            database='kol_info'
        )
        
        # Get cursor
        cursor = conn.cursor()
        
        # Find duplicate kol_screen_name values
        cursor.execute("""
            SELECT kol_screen_name, COUNT(*) as count
            FROM kol_info
            WHERE kol_screen_name IS NOT NULL AND kol_screen_name != ''
            GROUP BY kol_screen_name
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"Found {len(duplicates)} kol_screen_name values with multiple records:")
            for screen_name, count in duplicates:
                print(f"  {screen_name}: {count} records")
                
                # Get details for each duplicate
                cursor.execute("""
                    SELECT id, kol_id, kol_name, kol_screen_name, description
                    FROM kol_info
                    WHERE kol_screen_name = %s
                    ORDER BY id
                """, (screen_name,))
                
                records = cursor.fetchall()
                for i, record in enumerate(records):
                    print(f"    Record {i+1}:")
                    print(f"      id: {record[0]}")
                    print(f"      kol_id: {record[1]}")
                    print(f"      kol_name: {record[2]}")
                    print(f"      kol_screen_name: {record[3]}")
                    print(f"      description: {record[4][:50]}..." if record[4] and len(record[4]) > 50 else f"      description: {record[4]}")
                print()
        else:
            print("No duplicate kol_screen_name values found.")
        
        # Check specifically for cz_binance
        cursor.execute("""
            SELECT id, kol_id, kol_name, kol_screen_name, description
            FROM kol_info
            WHERE kol_screen_name = 'cz_binance'
            ORDER BY id
        """)
        
        records = cursor.fetchall()
        
        if records:
            print(f"\nFound {len(records)} records for cz_binance:")
            for i, record in enumerate(records):
                print(f"  Record {i+1}:")
                print(f"    id: {record[0]}")
                print(f"    kol_id: {record[1]}")
                print(f"    kol_name: {record[2]}")
                print(f"    kol_screen_name: {record[3]}")
                print(f"    description: {record[4][:50]}..." if record[4] and len(record[4]) > 50 else f"    description: {record[4]}")
        else:
            print("\nNo records found for cz_binance.")
        
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        logging.error(f"Error checking duplicate records: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Check for duplicate records in MySQL')
    args = parser.parse_args()
    
    check_duplicate_records()
    
    return 0

if __name__ == "__main__":
    main()
