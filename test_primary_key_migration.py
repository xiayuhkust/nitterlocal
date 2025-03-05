#!/usr/bin/env python3
"""
Test script for primary key migration.
This script tests the migration from url to user_id as primary key.
"""

import os
import sys
import logging
import sqlite3
import shutil
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the database module and migration script
from src.database.local_database import LocalDatabase
from scripts.migrations.change_primary_key_to_user_id import migrate_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_test_database():
    """Set up a test database with sample data"""
    # Create a test database path
    db_path = 'data/test_primary_key_migration.db'
    
    # Remove the database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Initialize the database with the old schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the URL tracking table with url as primary key (old schema)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS url_tracking (
        url TEXT PRIMARY KEY,
        description TEXT,
        status TEXT DEFAULT 'active',
        last_checked TEXT,
        error_count INTEGER DEFAULT 0,
        tweet_count INTEGER DEFAULT 0,
        type TEXT,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_scraped TEXT,
        last_error TEXT,
        user_id TEXT
    )
    ''')
    
    # Add sample data
    now = datetime.now().isoformat()
    sample_data = [
        ('https://twitter.com/user1', 'User 1', 'active', now, 0, 10, 'kol', now, now, None, '12345'),
        ('https://twitter.com/user2', 'User 2', 'active', now, 0, 5, 'kol', now, now, None, '67890'),
        ('https://twitter.com/user3', 'User 3', 'active', now, 0, 15, 'kol', now, now, None, None),
        ('https://twitter.com/user4', 'User 4', 'active', now, 0, 20, 'kol', now, now, None, '54321'),
        ('https://twitter.com/user5', 'User 5', 'active', now, 0, 25, 'kol', now, now, None, '09876')
    ]
    
    cursor.executemany('''
    INSERT INTO url_tracking (
        url, description, status, last_checked, error_count, tweet_count, type, added_at, last_scraped, last_error, user_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_data)
    
    # Create the tweets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tweets (
        tweet_id TEXT PRIMARY KEY,
        source_url TEXT,
        content TEXT,
        created_at TEXT,
        author TEXT,
        likes INTEGER DEFAULT 0,
        retweets INTEGER DEFAULT 0,
        replies INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        stored_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_url) REFERENCES url_tracking (url)
    )
    ''')
    
    # Add sample tweets
    sample_tweets = [
        ('tweet1', 'https://twitter.com/user1', 'Tweet 1 content', now, 'user1', 10, 5, 2, 100, now),
        ('tweet2', 'https://twitter.com/user1', 'Tweet 2 content', now, 'user1', 15, 7, 3, 150, now),
        ('tweet3', 'https://twitter.com/user2', 'Tweet 3 content', now, 'user2', 20, 10, 5, 200, now),
        ('tweet4', 'https://twitter.com/user3', 'Tweet 4 content', now, 'user3', 25, 12, 6, 250, now),
        ('tweet5', 'https://twitter.com/user4', 'Tweet 5 content', now, 'user4', 30, 15, 8, 300, now)
    ]
    
    cursor.executemany('''
    INSERT INTO tweets (
        tweet_id, source_url, content, created_at, author, likes, retweets, replies, views, stored_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_tweets)
    
    conn.commit()
    conn.close()
    
    return db_path

def test_migration():
    """Test the migration from url to user_id as primary key"""
    logging.info("Testing primary key migration")
    
    # Set up the test database
    db_path = setup_test_database()
    logging.info(f"Set up test database at {db_path}")
    
    # Create a backup of the database before migration
    backup_path = f"{db_path}.backup"
    shutil.copy2(db_path, backup_path)
    logging.info(f"Created backup at {backup_path}")
    
    # Run the migration
    result = migrate_database(db_path, backup=False)
    logging.info(f"Migration result: {result}")
    
    if not result:
        logging.error("Migration failed")
        return False
    
    # Verify the migration
    try:
        # Connect to the migrated database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check the schema of the url_tracking table
        cursor.execute("PRAGMA table_info(url_tracking)")
        columns = cursor.fetchall()
        
        # Verify that user_id is the primary key
        primary_key_column = None
        for column in columns:
            if column[5] == 1:  # 5 is the index of the pk flag
                primary_key_column = column[1]  # 1 is the index of the column name
                break
        
        if primary_key_column != 'user_id':
            logging.error(f"Primary key is {primary_key_column}, expected user_id")
            return False
        
        # Verify that url is unique
        cursor.execute("PRAGMA index_list(url_tracking)")
        indexes = cursor.fetchall()
        
        has_url_index = False
        for index in indexes:
            if 'url' in index[1]:  # 1 is the index of the index name
                has_url_index = True
                break
        
        if not has_url_index:
            logging.error("No index found for url column")
            return False
        
        # Verify that the data was migrated correctly
        cursor.execute("SELECT COUNT(*) FROM url_tracking")
        count = cursor.fetchone()[0]
        
        if count != 4:  # One record should be skipped because it has no user_id
            logging.error(f"Expected 4 records, found {count}")
            return False
        
        # Verify that the tweets are still accessible
        cursor.execute("SELECT COUNT(*) FROM tweets")
        tweet_count = cursor.fetchone()[0]
        
        if tweet_count != 5:
            logging.error(f"Expected 5 tweets, found {tweet_count}")
            return False
        
        conn.close()
        
        # Test the LocalDatabase class with the migrated database
        db = LocalDatabase(db_path=db_path)
        
        # Test getting URLs
        urls = db.get_urls()
        if len(urls) != 4:
            logging.error(f"Expected 4 URLs, found {len(urls)}")
            return False
        
        # Test getting URL by user_id
        url_data = db.get_url_by_user_id('12345')
        if not url_data or url_data['url'] != 'https://twitter.com/user1':
            logging.error(f"Failed to get URL by user_id 12345")
            return False
        
        # Test getting tweets for a URL
        tweets = db.get_tweets(source_url='https://twitter.com/user1')
        if len(tweets) != 2:
            logging.error(f"Expected 2 tweets for user1, found {len(tweets)}")
            return False
        
        # Test adding a new URL with user_id
        result = db.add_url('https://twitter.com/user6', 'User 6', 'kol', user_id='11111')
        if not result:
            logging.error("Failed to add new URL with user_id")
            return False
        
        # Verify the new URL was added
        url_data = db.get_url_by_user_id('11111')
        if not url_data or url_data['url'] != 'https://twitter.com/user6':
            logging.error(f"Failed to get newly added URL by user_id 11111")
            return False
        
        logging.info("Primary key migration test passed!")
        return True
        
    except Exception as e:
        logging.error(f"Error testing migration: {str(e)}")
        return False

if __name__ == "__main__":
    test_migration()
