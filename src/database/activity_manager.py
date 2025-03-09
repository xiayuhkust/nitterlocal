#!/usr/bin/env python3
"""
Activity manager module.
This module provides functionality for managing Twitter account activity levels.
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ActivityManager:
    """Activity manager for Twitter accounts"""
    
    def __init__(self, db_path='data/local_database.db'):
        """Initialize the activity manager"""
        logging.info(f"Initializing activity manager with database at {db_path}")
        
        self.db_path = db_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize the database
        self._init_db()
        
        logging.info("Activity manager initialization complete")
    
    def _init_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create the activity levels table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_levels (
            url TEXT PRIMARY KEY,
            activity_level TEXT,
            update_interval INTEGER DEFAULT 15,
            last_activity_check TEXT,
            post_frequency REAL,
            avg_interactions REAL,
            last_post_time TEXT,
            max_tweets INTEGER DEFAULT 10,
            max_replies INTEGER DEFAULT 5,
            FOREIGN KEY (url) REFERENCES url_tracking (url)
        )
        ''')
        
        # Create an index on the activity_level column for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_activity_levels_level ON activity_levels (activity_level)
        ''')
        
        conn.commit()
        conn.close()
        
    def analyze_activity(self, url, days=7):
        """Analyze the activity level of a URL"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the URL data
            cursor.execute("SELECT * FROM url_tracking WHERE url = ?", (url,))
            url_data = cursor.fetchone()
            
            if not url_data:
                logging.error(f"URL {url} not found")
                conn.close()
                return None
            
            # Convert to dict
            columns = [column[0] for column in cursor.description]
            url_data = dict(zip(columns, url_data))
            
            # Get tweets for this URL
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("""
            SELECT * FROM tweets 
            WHERE source_url = ? AND created_at >= ?
            ORDER BY created_at DESC
            """, (url, since_date))
            
            tweets = []
            for row in cursor.fetchall():
                columns = [column[0] for column in cursor.description]
                tweet = dict(zip(columns, row))
                tweets.append(tweet)
            
            # Calculate activity metrics
            post_frequency = len(tweets) / days if days > 0 else 0  # tweets per day
            
            # Calculate average interactions per tweet
            total_interactions = 0
            for tweet in tweets:
                interactions = (
                    int(tweet.get('likes', 0)) + 
                    int(tweet.get('retweets', 0)) + 
                    int(tweet.get('replies', 0)) + 
                    int(tweet.get('views', 0))
                )
                total_interactions += interactions
            
            avg_interactions = total_interactions / len(tweets) if tweets else 0
            
            # Get the timestamp of the most recent tweet
            last_post_time = tweets[0].get('created_at') if tweets else None
            
            # Determine activity level
            activity_level = self._determine_activity_level(post_frequency, avg_interactions, last_post_time)
            
            # Get tweet quantities based on activity level
            max_tweets, max_replies = self._get_tweet_quantities(activity_level)
            
            # Update or insert activity level
            now = datetime.now().isoformat()
            cursor.execute("""
            INSERT OR REPLACE INTO activity_levels (
                url, activity_level, last_activity_check, post_frequency, 
                avg_interactions, last_post_time, max_tweets, max_replies
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url, activity_level, now, post_frequency,
                avg_interactions, last_post_time, max_tweets, max_replies
            ))
            
            conn.commit()
            
            # Get the updated activity data
            cursor.execute("SELECT * FROM activity_levels WHERE url = ?", (url,))
            columns = [column[0] for column in cursor.description]
            activity_data = dict(zip(columns, cursor.fetchone()))
            
            conn.close()
            
            return activity_data
            
        except Exception as e:
            logging.error(f"Error analyzing activity for URL {url}: {str(e)}")
            return None
    
    def _determine_activity_level(self, post_frequency, avg_interactions, last_post_time):
        """Determine the activity level based on metrics"""
        # Default to inactive
        activity_level = "inactive"
        
        # Convert last_post_time to datetime
        last_post_datetime = None
        if last_post_time:
            try:
                # Handle different date formats
                if 'T' in last_post_time:
                    # ISO format
                    last_post_datetime = datetime.fromisoformat(last_post_time.split('+')[0])
                else:
                    # Simple format
                    last_post_datetime = datetime.strptime(last_post_time, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logging.error(f"Error parsing date {last_post_time}: {str(e)}")
        
        # Calculate hours since last post
        hours_since_last_post = None
        if last_post_datetime:
            delta = datetime.now() - last_post_datetime
            hours_since_last_post = delta.total_seconds() / 3600
        
        # Very high activity: >10 tweets/day, >1000 interactions/tweet, <1h since last activity
        if (post_frequency > 10 and avg_interactions > 1000 and 
            hours_since_last_post is not None and hours_since_last_post < 1):
            activity_level = "very_high"
        
        # High activity: 5-10 tweets/day, 500-1000 interactions/tweet, <3h
        elif (post_frequency >= 5 and post_frequency <= 10 and 
              avg_interactions >= 500 and avg_interactions <= 1000 and
              hours_since_last_post is not None and hours_since_last_post < 3):
            activity_level = "high"
        
        # Medium activity: 1-5 tweets/day, 100-500 interactions/tweet, <12h
        elif (post_frequency >= 1 and post_frequency <= 5 and 
              avg_interactions >= 100 and avg_interactions <= 500 and
              hours_since_last_post is not None and hours_since_last_post < 12):
            activity_level = "medium"
        
        # Low activity: 0.2-1 tweets/day, 10-100 interactions/tweet, <48h
        elif (post_frequency >= 0.2 and post_frequency <= 1 and 
              avg_interactions >= 10 and avg_interactions <= 100 and
              hours_since_last_post is not None and hours_since_last_post < 48):
            activity_level = "low"
        
        return activity_level
    
    def _get_tweet_quantities(self, activity_level):
        """Get tweet quantities based on activity level"""
        # Default values
        max_tweets = 1
        max_replies = 1
        
        if activity_level == "very_high":
            max_tweets = 10
            max_replies = 5
        elif activity_level == "high":
            max_tweets = 8
            max_replies = 4
        elif activity_level == "medium":
            max_tweets = 5
            max_replies = 3
        elif activity_level == "low":
            max_tweets = 3
            max_replies = 2
        
        return max_tweets, max_replies
    
    def get_activity_level(self, url):
        """Get the activity level for a URL"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM activity_levels WHERE url = ?", (url,))
            row = cursor.fetchone()
            
            if not row:
                # If no activity level exists, analyze it
                conn.close()
                return self.analyze_activity(url)
            
            # Convert to dict
            columns = [column[0] for column in cursor.description]
            activity_data = dict(zip(columns, row))
            
            conn.close()
            
            return activity_data
            
        except Exception as e:
            logging.error(f"Error getting activity level for URL {url}: {str(e)}")
            return None
    
    def get_activity_distribution(self):
        """Get the distribution of activity levels"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT activity_level, COUNT(*) as count
            FROM activity_levels
            GROUP BY activity_level
            ORDER BY count DESC
            """)
            
            distribution = {}
            for level, count in cursor.fetchall():
                distribution[level] = count
            
            conn.close()
            
            return distribution
            
        except Exception as e:
            logging.error(f"Error getting activity distribution: {str(e)}")
            return {}
