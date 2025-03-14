import sqlite3
import os

# Connect to the SQLite database
db_path = '/home/ubuntu/nitterlocal/data/local_database.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Close connection
    conn.close()
else:
    print(f"Database file not found at {db_path}")
