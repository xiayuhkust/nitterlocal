#!/usr/bin/env python3
"""
Script to check environment variables for MySQL connection.
"""

import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Check environment variables for MySQL connection"""
    mysql_host = os.environ.get("MYSQL_HOST", "Not set")
    mysql_port = os.environ.get("MYSQL_PORT", "Not set")
    mysql_user = os.environ.get("MYSQL_USER", "Not set")
    mysql_password = os.environ.get("MYSQL_PASSWORD", "Not set")
    mysql_database = os.environ.get("MYSQL_DATABASE", "Not set")
    
    print("MySQL Environment Variables:")
    print(f"MYSQL_HOST: {mysql_host}")
    print(f"MYSQL_PORT: {mysql_port}")
    print(f"MYSQL_USER: {mysql_user}")
    print(f"MYSQL_PASSWORD: {'*****' if mysql_password != 'Not set' else 'Not set'}")
    print(f"MYSQL_DATABASE: {mysql_database}")

if __name__ == "__main__":
    main()
