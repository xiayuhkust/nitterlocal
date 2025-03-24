#!/usr/bin/env python3
"""
SQLite Database Setup Script for Server Migration

This script initializes or resets the local SQLite database with the required
structure for the nitterlocal project. It creates all necessary tables with
the correct schema for tracking Twitter URLs, storing tweets, and managing
KOL character information.

Usage:
    python scripts/database/setsqlite.py [--force]

Options:
    --force    Overwrite existing database without confirmation
"""

import os
import sys
import sqlite3
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Define the database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'local_database.db')
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def create_directory_if_not_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Created directory: {directory}")

def check_database_exists():
    """Check if the database file already exists"""
    return os.path.exists(DB_PATH)

def create_tables(conn):
    """Create all necessary tables in the database"""
    cursor = conn.cursor()
    
    # Create url_tracking table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS url_tracking (
        url TEXT PRIMARY KEY,
        user_id TEXT,
        description TEXT,
        status TEXT DEFAULT 'active',
        last_checked TEXT,
        error_count INTEGER DEFAULT 0,
        tweet_count INTEGER DEFAULT 0,
        type TEXT,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_scraped TEXT,
        last_error TEXT,
        subtype TEXT
    )
    ''')
    
    # Create tweets table
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
        user_id TEXT,
        is_reply INTEGER DEFAULT 0,
        reply_to TEXT,
        conversation_id TEXT,
        FOREIGN KEY (source_url) REFERENCES url_tracking (url)
    )
    ''')
    
    # Create kol_character table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kol_character (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kol_id TEXT,
        kol_screen_name TEXT NOT NULL,
        bio TEXT,
        lore TEXT,
        knowledge TEXT,
        postExamples TEXT,
        topics TEXT,
        style_all TEXT,
        style_chat TEXT,
        style_post TEXT,
        adjectives TEXT,
        url_tracking_id INTEGER,
        UNIQUE(kol_screen_name)
    )
    ''')
    
    # Create hashtags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hashtags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tweet_id INTEGER,
        hashtag TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tweet_id) REFERENCES tweets(id)
    )
    ''')
    
    # Create backup_log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS backup_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_type TEXT,
        backup_path TEXT,
        record_count INTEGER,
        status TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_tracking_url ON url_tracking(url)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_tracking_user_id ON url_tracking(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_user_id ON tweets(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kol_character_screen_name ON kol_character(kol_screen_name)')
    
    conn.commit()
    logging.info("All tables and indexes created successfully")

def add_sample_data(conn):
    """Add sample data to the database for testing"""
    cursor = conn.cursor()
    
    # Add sample URL tracking data
    sample_urls = [
        ('https://twitter.com/sample_user1', '123456789', 'Sample KOL account', 'active', 
         datetime.now().isoformat(), 0, 10, 'kol', datetime.now().isoformat(), 
         datetime.now().isoformat(), None, 'crypto'),
        ('https://twitter.com/sample_user2', '987654321', 'Sample exchange account', 'active', 
         datetime.now().isoformat(), 0, 15, 'exchange', datetime.now().isoformat(), 
         datetime.now().isoformat(), None, 'trading'),
        ('https://twitter.com/sample_user3', '456789123', 'Sample institution account', 'active', 
         datetime.now().isoformat(), 0, 20, 'institution', datetime.now().isoformat(), 
         datetime.now().isoformat(), None, 'defi')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO url_tracking 
    (url, user_id, description, status, last_checked, error_count, tweet_count, 
     type, added_at, last_scraped, last_error, subtype)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_urls)
    
    # Add sample tweets data
    current_time = datetime.now().isoformat()
    one_day_ago = datetime.now().replace(day=datetime.now().day-1).isoformat()
    two_days_ago = datetime.now().replace(day=datetime.now().day-2).isoformat()
    
    sample_tweets = [
        ('1234567890', 'https://twitter.com/sample_user1', 'This is a sample tweet from user 1', 
         one_day_ago, 'sample_user1', 100, 20, 5, 1000, current_time, '123456789', 0, None, 'conv1'),
        ('2345678901', 'https://twitter.com/sample_user2', 'This is a sample tweet from user 2', 
         two_days_ago, 'sample_user2', 200, 30, 10, 2000, current_time, '987654321', 0, None, 'conv2'),
        ('3456789012', 'https://twitter.com/sample_user3', 'This is a sample tweet from user 3', 
         current_time, 'sample_user3', 300, 40, 15, 3000, current_time, '456789123', 0, None, 'conv3')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO tweets 
    (tweet_id, source_url, content, created_at, author, likes, retweets, replies, views, 
     stored_at, user_id, is_reply, reply_to, conversation_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_tweets)
    
    # Add sample KOL character data
    sample_kols = [
        ('123456789', 'sample_user1', 'Sample bio 1', 'Sample lore', 'Sample knowledge', 
         'Post examples', 'crypto,blockchain', 'friendly,informative', 'casual', 'professional', 
         'knowledgeable,helpful', 1),
        ('987654321', 'sample_user2', 'Sample bio 2', 'Sample lore', 'Sample knowledge', 
         'Post examples', 'exchange,trading', 'analytical,precise', 'formal', 'technical', 
         'expert,detailed', 2),
        ('456789123', 'sample_user3', 'Sample bio 3', 'Sample lore', 'Sample knowledge', 
         'Post examples', 'defi,investment', 'enthusiastic,clear', 'friendly', 'educational', 
         'insightful,thorough', 3)
    ]
    
    for kol in sample_kols:
        cursor.execute('''
        INSERT OR IGNORE INTO kol_character 
        (kol_id, kol_screen_name, bio, lore, knowledge, postExamples, topics, 
         style_all, style_chat, style_post, adjectives, url_tracking_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', kol)
    
    conn.commit()
    logging.info(f"Added {len(sample_urls)} sample URLs and {len(sample_kols)} sample KOL characters")

def main():
    """Main function to set up the SQLite database"""
    parser = argparse.ArgumentParser(description='Set up SQLite database for nitterlocal')
    parser.add_argument('--force', action='store_true', help='Overwrite existing database without confirmation')
    parser.add_argument('--with-samples', action='store_true', help='Add sample data to the database')
    args = parser.parse_args()
    
    # Create data directory if it doesn't exist
    create_directory_if_not_exists(DATA_DIR)
    
    # Check if database already exists
    if check_database_exists() and not args.force:
        response = input(f"Database already exists at {DB_PATH}. Overwrite? (y/n): ")
        if response.lower() != 'y':
            logging.info("Operation cancelled by user")
            return
    
    # Create or connect to the database
    try:
        conn = sqlite3.connect(DB_PATH)
        logging.info(f"Connected to database at {DB_PATH}")
        
        # Create tables
        create_tables(conn)
        
        # Add sample data if requested
        if args.with_samples:
            add_sample_data(conn)
        
        conn.close()
        logging.info("Database setup completed successfully")
        
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
