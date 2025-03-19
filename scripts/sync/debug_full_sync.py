#!/usr/bin/env python3

import os
import sys
import logging
import argparse
import sqlite3
import pymysql
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_sqlite_connection(db_path):
    """Get SQLite connection"""
    return sqlite3.connect(db_path)

def get_mysql_connection():
    """Get MySQL connection"""
    mysql_host = os.getenv('MYSQL_HOST', '43.135.26.222')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'z1050493759')
    mysql_database = os.getenv('MYSQL_DATABASE', 'kol_info')
    
    # Connect to MySQL
    conn = pymysql.connect(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_database
    )
    return conn

def get_mysql_table_columns(mysql_conn, table_name):
    """Get column names from MySQL table"""
    cursor = mysql_conn.cursor()
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns

def get_sqlite_table_columns(sqlite_conn, table_name):
    """Get column names from SQLite table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    cursor.close()
    return columns

def compare_kol_records(sqlite_conn, mysql_conn, handle=None, kol_id=None):
    """Compare KOL records between SQLite and MySQL databases"""
    try:
        # Get column names
        sqlite_url_columns = get_sqlite_table_columns(sqlite_conn, "url_tracking")
        mysql_kol_columns = get_mysql_table_columns(mysql_conn, "kol_info")
        
        # Get SQLite record
        sqlite_cursor = sqlite_conn.cursor()
        if handle:
            # Find by URL containing the handle
            sqlite_cursor.execute(
                "SELECT * FROM url_tracking WHERE url LIKE ?",
                (f"%twitter.com/{handle}%",)
            )
        elif kol_id:
            sqlite_cursor.execute(
                "SELECT * FROM url_tracking WHERE user_id = ?",
                (kol_id,)
            )
        else:
            logging.error("Either handle or kol_id must be provided")
            return
            
        sqlite_record = sqlite_cursor.fetchone()
        
        if not sqlite_record:
            logging.error(f"No record found in SQLite for {'handle: ' + handle if handle else 'kol_id: ' + kol_id}")
            return
        
        # Convert to dictionary
        sqlite_dict = dict(zip(sqlite_url_columns, sqlite_record))
        
        # Get MySQL record
        mysql_cursor = mysql_conn.cursor()
        if handle:
            mysql_cursor.execute(
                "SELECT * FROM kol_info WHERE kol_screen_name = %s",
                (handle,)
            )
        elif kol_id:
            mysql_cursor.execute(
                "SELECT * FROM kol_info WHERE kol_id = %s",
                (kol_id,)
            )
            
        mysql_record = mysql_cursor.fetchone()
        
        if not mysql_record:
            logging.error(f"No record found in MySQL for {'handle: ' + handle if handle else 'kol_id: ' + kol_id}")
            return
        
        # Convert to dictionary
        mysql_dict = dict(zip(mysql_kol_columns, mysql_record))
        
        # Compare fields
        print(f"\n=== Comparing KOL records for {handle if handle else kol_id} ===")
        print(f"SQLite record ID: {sqlite_dict.get('id')}")
        print(f"MySQL record ID: {mysql_dict.get('id')}")
        
        # Field mapping between SQLite and MySQL
        field_mapping = {
            'user_id': 'kol_id',
            'screen_name': 'kol_screen_name',
            'description': 'description',
            'followers_count': 'followers_count',
            'following_count': 'following_count',
            'tweet_count': 'statuses_count',
            'type': 'first_category',
            'subtype': 'second_category',
            'kol_name': 'kol_name',
            'profile_image_url': 'profile_image_url',
            'profile_banner_url': 'profile_banner_url',
            'verified': 'verified',
            'location': 'location',
            'created_at': 'created_at'
        }
        
        for sqlite_field, mysql_field in field_mapping.items():
            if sqlite_field in sqlite_dict and mysql_field in mysql_dict:
                sqlite_value = sqlite_dict[sqlite_field]
                mysql_value = mysql_dict[mysql_field]
                
                print(f"{sqlite_field}/{mysql_field}:")
                print(f"  SQLite: '{sqlite_value}'")
                print(f"  MySQL:  '{mysql_value}'")
                
                if str(sqlite_value) != str(mysql_value) and sqlite_value and mysql_value:
                    print(f"  ** MISMATCH **")
                elif not sqlite_value and mysql_value:
                    print(f"  ** Empty in SQLite but not in MySQL **")
                elif sqlite_value and not mysql_value:
                    print(f"  ** Empty in MySQL but not in SQLite **")
                print()
        
        return sqlite_dict, mysql_dict
    
    except Exception as e:
        logging.error(f"Error comparing KOL records: {str(e)}")
        return None, None

def compare_tweet_records(sqlite_conn, mysql_conn, tweet_id):
    """Compare tweet records between SQLite and MySQL databases"""
    try:
        # Get column names
        sqlite_tweets_columns = get_sqlite_table_columns(sqlite_conn, "tweets")
        mysql_tweets_columns = get_mysql_table_columns(mysql_conn, "kol_tweet")
        
        # Get SQLite record
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(
            "SELECT * FROM tweets WHERE tweet_id = ?",
            (tweet_id,)
        )
        sqlite_record = sqlite_cursor.fetchone()
        
        if not sqlite_record:
            logging.error(f"No record found in SQLite for tweet_id: {tweet_id}")
            return None, None
        
        # Convert to dictionary
        sqlite_dict = dict(zip(sqlite_tweets_columns, sqlite_record))
        
        # Get MySQL record
        mysql_cursor = mysql_conn.cursor()
        mysql_cursor.execute(
            "SELECT * FROM kol_tweet WHERE tweet_id = %s",
            (tweet_id,)
        )
        mysql_record = mysql_cursor.fetchone()
        
        if not mysql_record:
            logging.error(f"No record found in MySQL for tweet_id: {tweet_id}")
            return sqlite_dict, None
        
        # Convert to dictionary
        mysql_dict = dict(zip(mysql_tweets_columns, mysql_record))
        
        # Compare fields
        print(f"\n=== Comparing tweet records for tweet_id: {tweet_id} ===")
        
        # Field mapping between SQLite and MySQL
        field_mapping = {
            'tweet_id': 'tweet_id',
            'user_id': 'kol_id',
            'author': 'kol_screen_name',
            'content': 'tweet_text',
            'created_at': 'created_at',
            'likes': 'favorite_count',
            'retweets': 'retweet_count',
            'replies': 'reply_count',
            'views': 'view_count',
            'lang': 'lang',
            'is_reply': 'is_reply',
            'is_retweet': 'is_retweet',
            'is_quote': 'is_quote',
            'media_urls': 'media_urls',
            'quoted_tweet_id': 'quoted_tweet_id',
            'in_reply_to_tweet_id': 'in_reply_to_tweet_id',
            'in_reply_to_user_id': 'in_reply_to_user_id'
        }
        
        for sqlite_field, mysql_field in field_mapping.items():
            if sqlite_field in sqlite_dict and mysql_field in mysql_dict:
                sqlite_value = sqlite_dict[sqlite_field]
                mysql_value = mysql_dict[mysql_field]
                
                print(f"{sqlite_field}/{mysql_field}:")
                print(f"  SQLite: '{sqlite_value}'")
                print(f"  MySQL:  '{mysql_value}'")
                
                if str(sqlite_value) != str(mysql_value) and sqlite_value and mysql_value:
                    print(f"  ** MISMATCH **")
                elif not sqlite_value and mysql_value:
                    print(f"  ** Empty in SQLite but not in MySQL **")
                elif sqlite_value and not mysql_value:
                    print(f"  ** Empty in MySQL but not in SQLite **")
                print()
        
        return sqlite_dict, mysql_dict
    
    except Exception as e:
        logging.error(f"Error comparing tweet records: {str(e)}")
        return None, None

def list_recent_tweets(sqlite_conn, limit=10):
    """List recent tweets from SQLite database"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(
            """
            SELECT tweet_id, user_id, author, created_at, content
            FROM tweets
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("No tweets found in SQLite database")
            return
        
        print(f"\n=== Recent {limit} tweets in SQLite database ===")
        for row in rows:
            tweet_id, user_id, author, created_at, content = row
            print(f"Tweet ID: {tweet_id}")
            print(f"User ID: {user_id}")
            print(f"Author: {author}")
            print(f"Created at: {created_at}")
            print(f"Content: {content[:50]}..." if len(content) > 50 else f"Content: {content}")
            print()
        
    except Exception as e:
        logging.error(f"Error listing recent tweets: {str(e)}")

def list_kol_handles(sqlite_conn, limit=10):
    """List KOL handles from SQLite database"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(
            """
            SELECT rowid, url, user_id, type, subtype
            FROM url_tracking
            WHERE type = 'kol'
            ORDER BY rowid DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("No KOL handles found in SQLite database")
            return
        
        print(f"\n=== Recent {limit} KOL handles in SQLite database ===")
        for row in rows:
            rowid, url, user_id, type, subtype = row
            # Extract screen name from URL
            screen_name = None
            if url and 'twitter.com/' in url:
                parts = url.split('twitter.com/')
                if len(parts) > 1:
                    screen_name = parts[1].split('/')[0].split('?')[0]
            
            print(f"ID: {rowid}")
            print(f"URL: {url}")
            print(f"User ID: {user_id}")
            print(f"Screen name: {screen_name}")
            print(f"Type: {type}")
            print(f"Subtype: {subtype}")
            print()
        
    except Exception as e:
        logging.error(f"Error listing KOL handles: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Debug synchronization between SQLite and MySQL')
    parser.add_argument('--db-path', type=str, default='/home/ubuntu/nitterlocal/data/local_database.db', help='Path to SQLite database')
    parser.add_argument('--handle', type=str, help='Twitter handle to compare')
    parser.add_argument('--kol-id', type=str, help='KOL ID to compare')
    parser.add_argument('--tweet-id', type=str, help='Tweet ID to compare')
    parser.add_argument('--list-tweets', action='store_true', help='List recent tweets')
    parser.add_argument('--list-kols', action='store_true', help='List KOL handles')
    parser.add_argument('--limit', type=int, default=10, help='Limit for listing tweets or KOLs')
    
    args = parser.parse_args()
    
    # Connect to databases
    sqlite_conn = get_sqlite_connection(args.db_path)
    mysql_conn = get_mysql_connection()
    
    try:
        # List recent tweets
        if args.list_tweets:
            list_recent_tweets(sqlite_conn, args.limit)
        
        # List KOL handles
        if args.list_kols:
            list_kol_handles(sqlite_conn, args.limit)
        
        # Compare KOL records
        if args.handle or args.kol_id:
            compare_kol_records(sqlite_conn, mysql_conn, args.handle, args.kol_id)
        
        # Compare tweet records
        if args.tweet_id:
            compare_tweet_records(sqlite_conn, mysql_conn, args.tweet_id)
        
        # If no specific action is requested, show usage
        if not (args.handle or args.kol_id or args.tweet_id or args.list_tweets or args.list_kols):
            parser.print_help()
    
    finally:
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()

if __name__ == "__main__":
    main()
