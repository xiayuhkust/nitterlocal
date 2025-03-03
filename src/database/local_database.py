#!/usr/bin/env python3
"""
Local database module.
This module provides a local database for storing tweets extracted using agent-twitter-client.
"""

import os
import sys
import logging
import sqlite3
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LocalDatabase:
    """Local database for storing tweets extracted using agent-twitter-client"""
    
    def __init__(self, db_path='data/local_database.db'):
        """Initialize the local database"""
        logging.info(f"Initializing local database at {db_path}")
        
        self.db_path = db_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize the database
        self._init_db()
        
        logging.info("Database initialization complete")
    
    def _init_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create the URL tracking table
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
            last_error TEXT
        )
        ''')
        
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
        
        # Create the hashtags table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hashtags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_id TEXT,
            hashtag TEXT,
            FOREIGN KEY (tweet_id) REFERENCES tweets (tweet_id) ON DELETE CASCADE
        )
        ''')
        
        # Create an index on the hashtag column for faster queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_hashtags_hashtag ON hashtags (hashtag)
        ''')
        
        # Create the backup log table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS backup_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            operation TEXT,
            details TEXT,
            success INTEGER DEFAULT 1
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_urls(self, status=None, limit=None):
        """Get URLs from the local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute("SELECT * FROM url_tracking WHERE status = ? LIMIT ?", (status, limit or -1))
            else:
                cursor.execute("SELECT * FROM url_tracking LIMIT ?", (limit or -1,))
            
            columns = [column[0] for column in cursor.description]
            urls = []
            
            for row in cursor.fetchall():
                url_data = dict(zip(columns, row))
                urls.append(url_data)
            
            conn.close()
            
            return urls
            
        except Exception as e:
            logging.error(f"Error getting URLs from local database: {str(e)}")
            return []
    
    def get_tweets(self, source_url=None, limit=None):
        """Get tweets from the local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if source_url:
                cursor.execute("SELECT * FROM tweets WHERE source_url = ? LIMIT ?", (source_url, limit or -1))
            else:
                cursor.execute("SELECT * FROM tweets LIMIT ?", (limit or -1,))
            
            columns = [column[0] for column in cursor.description]
            tweets = []
            
            for row in cursor.fetchall():
                tweet_data = dict(zip(columns, row))
                tweets.append(tweet_data)
            
            conn.close()
            
            return tweets
            
        except Exception as e:
            logging.error(f"Error getting tweets from local database: {str(e)}")
            return []
    
    def store_tweets(self, tweets, source_url):
        """Store tweets in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stored_count = 0
            updated_count = 0
            
            for tweet in tweets:
                try:
                    # Check if tweet already exists
                    cursor.execute("SELECT 1 FROM tweets WHERE tweet_id = ?", (tweet['tweet_id'],))
                    if cursor.fetchone():
                        # Update existing tweet's metadata
                        cursor.execute('''
                        UPDATE tweets 
                        SET likes = ?, retweets = ?, replies = ?, views = ?
                        WHERE tweet_id = ?
                        ''', (
                            tweet['likes'],
                            tweet['retweets'],
                            tweet['replies'],
                            tweet['views'],
                            tweet['tweet_id']
                        ))
                        
                        # Delete existing hashtags for this tweet
                        cursor.execute("DELETE FROM hashtags WHERE tweet_id = ?", (tweet['tweet_id'],))
                        
                        updated_count += 1
                    else:
                        # Insert new tweet
                        cursor.execute('''
                        INSERT INTO tweets (
                            tweet_id, source_url, content, created_at, author, likes, retweets, replies, views
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            tweet['tweet_id'],
                            source_url,
                            tweet['content'],
                            tweet['created_at'],
                            tweet['author'],
                            tweet['likes'],
                            tweet['retweets'],
                            tweet['replies'],
                            tweet['views']
                        ))
                        
                        stored_count += 1
                    
                    # Store hashtags for the tweet
                    if 'hashtags' in tweet and tweet['hashtags']:
                        for hashtag in tweet['hashtags']:
                            cursor.execute('''
                            INSERT INTO hashtags (tweet_id, hashtag)
                            VALUES (?, ?)
                            ''', (tweet['tweet_id'], hashtag))
                        
                except Exception as e:
                    logging.warning(f"Error storing/updating tweet {tweet['tweet_id']}: {str(e)}")
                    continue
            
            # Update the tweet count for the URL (only count new tweets, not updates)
            cursor.execute('''
            UPDATE url_tracking 
            SET tweet_count = tweet_count + ?, last_scraped = ?
            WHERE url = ?
            ''', (stored_count, datetime.now().isoformat(), source_url))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Stored {stored_count} new tweets and updated {updated_count} existing tweets for URL: {source_url}")
            
            return stored_count + updated_count
            
        except Exception as e:
            logging.error(f"Error storing tweets: {str(e)}")
            return 0
    
    def add_url(self, url, description="", url_type="kol"):
        """Add a URL to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if URL already exists
            cursor.execute("SELECT 1 FROM url_tracking WHERE url = ?", (url,))
            if cursor.fetchone():
                conn.close()
                return True
            
            # Add URL
            now = datetime.now().isoformat()
            cursor.execute('''
            INSERT INTO url_tracking (
                url, description, status, last_checked, error_count, tweet_count, type, added_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                url,
                description,
                'active',
                now,
                0,
                0,
                url_type,
                now
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logging.error(f"Error adding URL {url}: {str(e)}")
            return False
    
    def update_url_status(self, url, status, error=None):
        """Update the status of a URL"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            if error:
                cursor.execute('''
                UPDATE url_tracking 
                SET status = ?, last_checked = ?, error_count = error_count + 1, last_error = ?
                WHERE url = ?
                ''', (status, now, error, url))
            else:
                cursor.execute('''
                UPDATE url_tracking 
                SET status = ?, last_checked = ?
                WHERE url = ?
                ''', (status, now, url))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logging.error(f"Error updating URL status for {url}: {str(e)}")
            return False
    
    def generate_stats(self):
        """Generate statistics for the local database"""
        logging.info("Generating statistics for local database")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total URL count
            cursor.execute("SELECT COUNT(*) FROM url_tracking")
            total_urls = cursor.fetchone()[0]
            
            # Get active URL count
            cursor.execute("SELECT COUNT(*) FROM url_tracking WHERE status = 'active'")
            active_urls = cursor.fetchone()[0]
            
            # Get total tweet count
            cursor.execute("SELECT COUNT(*) FROM tweets")
            total_tweets = cursor.fetchone()[0]
            
            # Get tweet count by URL
            cursor.execute('''
                SELECT source_url, COUNT(*) as tweet_count 
                FROM tweets 
                GROUP BY source_url 
                ORDER BY tweet_count DESC
            ''')
            url_tweet_counts = {}
            for url, count in cursor.fetchall():
                url_tweet_counts[url] = count
            
            # Generate statistics
            stats = {
                'total_urls': total_urls,
                'active_urls': active_urls,
                'total_tweets': total_tweets,
                'url_tweet_counts': url_tweet_counts,
                'generated_at': datetime.now().isoformat()
            }
            
            # Save statistics to file
            with open('data/local_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
            
            conn.close()
            
            logging.info(f"Statistics generated: {total_urls} URLs, {total_tweets} tweets")
            
            return stats
            
        except Exception as e:
            logging.error(f"Error generating statistics: {str(e)}")
            return None
    
    def get_tweets_by_hashtag(self, hashtag, limit=None):
        """Get tweets that contain a specific hashtag"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT t.* FROM tweets t
            JOIN hashtags h ON t.tweet_id = h.tweet_id
            WHERE h.hashtag = ?
            LIMIT ?
            ''', (hashtag, limit or -1))
            
            columns = [column[0] for column in cursor.description]
            tweets = []
            
            for row in cursor.fetchall():
                tweet_data = dict(zip(columns, row))
                tweets.append(tweet_data)
            
            conn.close()
            
            return tweets
            
        except Exception as e:
            logging.error(f"Error getting tweets by hashtag {hashtag}: {str(e)}")
            return []
    
    def get_popular_hashtags(self, limit=10):
        """Get the most popular hashtags"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT hashtag, COUNT(*) as count
            FROM hashtags
            GROUP BY hashtag
            ORDER BY count DESC
            LIMIT ?
            ''', (limit,))
            
            hashtags = []
            
            for hashtag, count in cursor.fetchall():
                hashtags.append({
                    'hashtag': hashtag,
                    'count': count
                })
            
            conn.close()
            
            return hashtags
            
        except Exception as e:
            logging.error(f"Error getting popular hashtags: {str(e)}")
            return []
    
    def _log_operation(self, operation, details, success=1):
        """Log an operation to the backup log table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO backup_log (operation, details, success)
            VALUES (?, ?, ?)
            ''', (operation, details, success))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Error logging operation: {str(e)}")
