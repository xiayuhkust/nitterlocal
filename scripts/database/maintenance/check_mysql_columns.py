import pymysql
import os

def main():
    try:
        # Connect to MySQL
        conn = pymysql.connect(
            host='43.135.26.222',
            port=3306,
            user='root',
            password='z1050493759',
            database='kol_info'
        )
        
        # Get column names from MySQL
        cursor = conn.cursor()
        cursor.execute('SHOW COLUMNS FROM kol_info')
        print("MySQL kol_info columns:")
        for row in cursor.fetchall():
            print(row)
        
        cursor.close()
        conn.close()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
