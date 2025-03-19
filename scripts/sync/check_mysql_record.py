#!/usr/bin/env python3

import pymysql
import argparse

def main():
    parser = argparse.ArgumentParser(description='Check MySQL record for a specific kol_id')
    parser.add_argument('--kol-id', type=str, required=True, help='KOL ID to check')
    args = parser.parse_args()
    
    try:
        # Connect to MySQL
        conn = pymysql.connect(
            host='43.135.26.222',
            port=3306,
            user='root',
            password='z1050493759',
            database='kol_info'
        )
        
        # Get record from MySQL
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM kol_info WHERE kol_id = %s",
            (args.kol_id,)
        )
        record = cursor.fetchone()
        
        # Get column names
        cursor.execute("SHOW COLUMNS FROM kol_info")
        columns = [column[0] for column in cursor.fetchall()]
        
        # Print record with column names
        if record:
            print("MySQL record for kol_id:", args.kol_id)
            for i, value in enumerate(record):
                if i < len(columns):
                    print(f"{columns[i]}: {value}")
                else:
                    print(f"Column {i}: {value}")
        else:
            print(f"No record found for kol_id: {args.kol_id}")
        
        cursor.close()
        conn.close()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
