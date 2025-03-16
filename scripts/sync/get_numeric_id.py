#!/usr/bin/env python3
"""
Helper function to get numeric ID for Twitter handles.
This script provides a function to look up the numeric ID for a Twitter handle in the MySQL database.
"""

import logging
import mysql.connector
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

def get_numeric_id_for_handle(mysql_conn, handle):
    """Get the numeric ID for a Twitter handle from the kol_info table"""
    try:
        cursor = mysql_conn.cursor()
        cursor.execute(
            "SELECT kol_id FROM kol_info WHERE kol_screen_name = %s",
            (handle,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return result[0]
        
        # If not found by exact match, try case-insensitive match
        cursor = mysql_conn.cursor()
        cursor.execute(
            "SELECT kol_id FROM kol_info WHERE LOWER(kol_screen_name) = LOWER(%s)",
            (handle,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            logging.info(f"Found kol_id for {handle} using case-insensitive match")
            return result[0]
            
        return None
    
    except Exception as e:
        logging.error(f"Error getting numeric ID for handle {handle}: {str(e)}")
        return None

if __name__ == "__main__":
    # This script can be run standalone to test the function
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 get_numeric_id.py <twitter_handle>")
        sys.exit(1)
    
    handle = sys.argv[1]
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Get MySQL connection parameters from environment variables
    mysql_host = os.getenv('MYSQL_HOST', '43.135.26.222')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', '')
    mysql_database = os.getenv('MYSQL_DATABASE', 'kol_info')
    
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        
        # Get numeric ID
        kol_id = get_numeric_id_for_handle(conn, handle)
        
        if kol_id:
            print(f"Numeric ID for {handle}: {kol_id}")
        else:
            print(f"No numeric ID found for {handle}")
        
        # Close connection
        conn.close()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
