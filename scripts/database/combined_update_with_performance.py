#!/usr/bin/env python3
"""
Combined script to update SQLite tweets and sync to MySQL with performance logging.
This script:
1. Updates the SQLite database with tweets (10 regular tweets and 10 replies per URL)
2. Syncs the updated data to MySQL
3. Logs performance metrics for each step
"""

import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Import required modules
try:
    from src.database.local_database import LocalDatabase
    from src.database.url_manager import URLManager
    from src.twitter_client.twitter_scraper import TwitterScraper
    from dotenv import load_dotenv
except ImportError as e:
    logging.error(f"Error importing required modules: {str(e)}")
    sys.exit(1)

class PerformanceLogger:
    """Class to log performance metrics"""
    
    def __init__(self, log_file='data/performance_log.json'):
        """Initialize the performance logger"""
        self.log_file = log_file
        self.start_time = time.time()
        self.checkpoints = []
        self.metrics = {
            'start_time': datetime.now().isoformat(),
            'total_duration': 0,
            'sqlite_update': {
                'duration': 0,
                'urls_processed': 0,
                'tweets_processed': 0,
                'errors': 0
            },
            'mysql_sync': {
                'duration': 0,
                'urls_synced': 0,
                'tweets_synced': 0,
                'errors': 0
            },
            'steps': []
        }
    
    def checkpoint(self, name):
        """Record a checkpoint"""
        checkpoint_time = time.time()
        
        if self.checkpoints:
            last_checkpoint = self.checkpoints[-1]
            duration = checkpoint_time - last_checkpoint['time']
            
            self.metrics['steps'].append({
                'name': last_checkpoint['name'],
                'duration': duration,
                'end_time': datetime.now().isoformat()
            })
            
            logging.info(f"Step '{last_checkpoint['name']}' completed in {duration:.2f} seconds")
        
        self.checkpoints.append({
            'name': name,
            'time': checkpoint_time
        })
        
        logging.info(f"Starting step: {name}")
    
    def finalize(self):
        """Finalize the performance log"""
        end_time = time.time()
        
        if self.checkpoints:
            last_checkpoint = self.checkpoints[-1]
            duration = end_time - last_checkpoint['time']
            
            self.metrics['steps'].append({
                'name': last_checkpoint['name'],
                'duration': duration,
                'end_time': datetime.now().isoformat()
            })
            
            logging.info(f"Step '{last_checkpoint['name']}' completed in {duration:.2f} seconds")
        
        self.metrics['total_duration'] = end_time - self.start_time
        self.metrics['end_time'] = datetime.now().isoformat()
        
        logging.info(f"Total duration: {self.metrics['total_duration']:.2f} seconds")
        
        # Save metrics to file
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
            logging.info(f"Performance metrics saved to {self.log_file}")
        except Exception as e:
            logging.error(f"Error saving performance metrics: {str(e)}")
    
    def update_sqlite_metrics(self, urls_processed, tweets_processed, errors=0, duration=None):
        """Update SQLite metrics"""
        if duration is None:
            if len(self.metrics['steps']) > 0:
                duration = self.metrics['steps'][-1]['duration']
            else:
                duration = 0
        
        self.metrics['sqlite_update'] = {
            'duration': duration,
            'urls_processed': urls_processed,
            'tweets_processed': tweets_processed,
            'errors': errors
        }
    
    def update_mysql_metrics(self, urls_synced, tweets_synced, errors=0, duration=None):
        """Update MySQL metrics"""
        if duration is None:
            if len(self.metrics['steps']) > 1:
                duration = self.metrics['steps'][-1]['duration']
            else:
                duration = 0
        
        self.metrics['mysql_sync'] = {
            'duration': duration,
            'urls_synced': urls_synced,
            'tweets_synced': tweets_synced,
            'errors': errors
        }

def update_sqlite_database(performance_logger, limit=None, max_tweets=10, max_replies=10):
    """Update the SQLite database with tweets"""
    performance_logger.checkpoint("SQLite Update")
    
    try:
        # Initialize components
        db_path = 'data/local_database.db'
        database = LocalDatabase(db_path=db_path)
        url_manager = URLManager(db_path=db_path)
        scraper = TwitterScraper()
        
        # Get active URLs
        urls = url_manager.get_urls(status='active', limit=limit)
        
        if not urls:
            logging.warning("No active URLs found")
            performance_logger.update_sqlite_metrics(0, 0, 1)
            return False
        
        logging.info(f"Found {len(urls)} active URLs to process")
        
        # Process each URL
        processed_urls = 0
        total_tweets = 0
        errors = 0
        
        for url_data in urls:
            url = url_data['url']
            logging.info(f"Processing URL: {url}")
            
            try:
                # Scrape the URL
                tweets = scraper.scrape_url(url, max_tweets=max_tweets, max_replies=max_replies)
                
                if tweets:
                    # Store the tweets in the database
                    processed_count = database.store_tweets(tweets, url)
                    
                    if processed_count > 0:
                        logging.info(f"Processed {processed_count} tweets for URL: {url}")
                        total_tweets += processed_count
                    else:
                        logging.warning(f"No tweets processed for URL: {url}")
                else:
                    logging.warning(f"No tweets found for URL: {url}")
                
                # Update the URL status
                url_manager.update_last_scraped(url)
                processed_urls += 1
            
            except Exception as e:
                logging.error(f"Error processing URL {url}: {str(e)}")
                errors += 1
        
        # Generate statistics
        logging.info("Generating statistics")
        stats = database.generate_stats()
        
        if stats:
            logging.info(f"Total URLs in database: {stats['total_urls']}")
            logging.info(f"Total tweets in database: {stats['total_tweets']}")
        
        # Update performance metrics
        performance_logger.update_sqlite_metrics(processed_urls, total_tweets, errors)
        
        return True
    
    except Exception as e:
        logging.error(f"Error updating SQLite database: {str(e)}")
        import traceback
        traceback.print_exc()
        performance_logger.update_sqlite_metrics(0, 0, 1)
        return False

def sync_to_mysql(performance_logger, limit=None):
    """Sync data from SQLite to MySQL"""
    performance_logger.checkpoint("MySQL Sync")
    
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # MySQL connection parameters
        mysql_host = os.environ.get("MYSQL_HOST", "localhost")
        mysql_port = int(os.environ.get("MYSQL_PORT", "3306"))
        mysql_user = os.environ.get("MYSQL_USER", "root")
        mysql_password = os.environ.get("MYSQL_PASSWORD", "")
        mysql_database = os.environ.get("MYSQL_DATABASE", "kol_info")
        
        # Check if MySQL connector is installed
        try:
            import mysql.connector
        except ImportError:
            logging.error("MySQL Connector for Python is not installed. Please install it with 'pip install mysql-connector-python'")
            performance_logger.update_mysql_metrics(0, 0, 1)
            return False
        
        # Connect to MySQL
        try:
            mysql_conn = mysql.connector.connect(
                host=mysql_host,
                port=mysql_port,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database
            )
            mysql_cursor = mysql_conn.cursor()
        except Exception as e:
            logging.error(f"Error connecting to MySQL database: {str(e)}")
            performance_logger.update_mysql_metrics(0, 0, 1)
            return False
        
        # Connect to SQLite
        db_path = 'data/local_database.db'
        sqlite_conn = LocalDatabase(db_path=db_path).get_connection()
        sqlite_cursor = sqlite_conn.cursor()
        
        # Get URLs from SQLite
        sqlite_cursor.execute("SELECT url, description, type, user_id, subtype FROM url_tracking LIMIT ?", (limit or -1,))
        urls = sqlite_cursor.fetchall()
        
        if not urls:
            logging.warning("No URLs found in SQLite database")
            performance_logger.update_mysql_metrics(0, 0, 1)
            sqlite_conn.close()
            mysql_conn.close()
            return False
        
        logging.info(f"Found {len(urls)} URLs in SQLite database")
        
        # Sync KOL info to MySQL
        urls_synced = 0
        errors = 0
        
        for url_data in urls:
            url, description, url_type, user_id, subtype = url_data
            
            try:
                # Check if KOL info already exists in MySQL
                mysql_cursor.execute("SELECT id FROM kol_info WHERE user_id = %s", (user_id,))
                existing = mysql_cursor.fetchone()
                
                if existing:
                    # Update existing KOL info
                    mysql_cursor.execute("""
                    UPDATE kol_info 
                    SET url = %s, description = %s, type = %s, subtype = %s, updated_at = NOW()
                    WHERE user_id = %s
                    """, (url, description, url_type, subtype, user_id))
                    logging.info(f"Updated KOL info for URL: {url}")
                else:
                    # Insert new KOL info
                    mysql_cursor.execute("""
                    INSERT INTO kol_info (user_id, url, description, type, subtype, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    """, (user_id, url, description, url_type, subtype))
                    logging.info(f"Inserted KOL info for URL: {url}")
                
                urls_synced += 1
            
            except Exception as e:
                logging.error(f"Error syncing KOL info for URL {url}: {str(e)}")
                errors += 1
        
        # Commit KOL info changes
        mysql_conn.commit()
        
        # Get tweets from SQLite
        sqlite_cursor.execute("""
        SELECT t.tweet_id, t.source_url, t.content, t.created_at, t.author, t.likes, t.retweets, 
               t.replies, t.views, t.user_id, t.is_reply, t.reply_to, t.conversation_id,
               u.user_id as kol_user_id
        FROM tweets t
        JOIN url_tracking u ON t.source_url = u.url
        LIMIT ?
        """, (limit or -1,))
        tweets = sqlite_cursor.fetchall()
        
        if not tweets:
            logging.warning("No tweets found in SQLite database")
            performance_logger.update_mysql_metrics(urls_synced, 0, errors)
            sqlite_conn.close()
            mysql_conn.close()
            return False
        
        logging.info(f"Found {len(tweets)} tweets in SQLite database")
        
        # Sync tweets to MySQL
        tweets_synced = 0
        
        for tweet_data in tweets:
            (tweet_id, source_url, content, created_at, author, likes, retweets, 
             replies, views, user_id, is_reply, reply_to, conversation_id, kol_user_id) = tweet_data
            
            try:
                # Check if tweet already exists in MySQL
                mysql_cursor.execute("SELECT id FROM kol_tweet WHERE tweet_id = %s", (tweet_id,))
                existing = mysql_cursor.fetchone()
                
                if existing:
                    # Update existing tweet
                    mysql_cursor.execute("""
                    UPDATE kol_tweet 
                    SET content = %s, created_at = %s, author = %s, likes = %s, retweets = %s,
                        replies = %s, views = %s, user_id = %s, is_reply = %s, reply_to = %s,
                        conversation_id = %s, kol_user_id = %s, updated_at = NOW()
                    WHERE tweet_id = %s
                    """, (
                        content, created_at, author, likes, retweets, replies, views, 
                        user_id, is_reply, reply_to, conversation_id, kol_user_id, tweet_id
                    ))
                    logging.info(f"Updated tweet: {tweet_id}")
                else:
                    # Insert new tweet
                    mysql_cursor.execute("""
                    INSERT INTO kol_tweet (
                        tweet_id, source_url, content, created_at, author, likes, retweets,
                        replies, views, user_id, is_reply, reply_to, conversation_id,
                        kol_user_id, created_at_mysql, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """, (
                        tweet_id, source_url, content, created_at, author, likes, retweets,
                        replies, views, user_id, is_reply, reply_to, conversation_id, kol_user_id
                    ))
                    logging.info(f"Inserted tweet: {tweet_id}")
                
                tweets_synced += 1
            
            except Exception as e:
                logging.error(f"Error syncing tweet {tweet_id}: {str(e)}")
                errors += 1
        
        # Commit tweet changes
        mysql_conn.commit()
        
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()
        
        # Update performance metrics
        performance_logger.update_mysql_metrics(urls_synced, tweets_synced, errors)
        
        return True
    
    except Exception as e:
        logging.error(f"Error syncing to MySQL: {str(e)}")
        import traceback
        traceback.print_exc()
        performance_logger.update_mysql_metrics(0, 0, 1)
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Combined script to update SQLite tweets and sync to MySQL with performance logging')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--max-tweets', type=int, default=10, help='Maximum number of tweets to fetch per URL')
    parser.add_argument('--max-replies', type=int, default=10, help='Maximum number of replies to fetch per URL')
    parser.add_argument('--skip-sqlite', action='store_true', help='Skip SQLite update')
    parser.add_argument('--skip-mysql', action='store_true', help='Skip MySQL sync')
    parser.add_argument('--log-file', default='data/performance_log.json', help='Path to the performance log file')
    
    args = parser.parse_args()
    
    # Initialize performance logger
    performance_logger = PerformanceLogger(log_file=args.log_file)
    performance_logger.checkpoint("Initialization")
    
    try:
        # Update SQLite database
        if not args.skip_sqlite:
            update_sqlite_database(performance_logger, args.limit, args.max_tweets, args.max_replies)
        else:
            logging.info("Skipping SQLite update")
            performance_logger.checkpoint("SQLite Update (skipped)")
        
        # Sync to MySQL
        if not args.skip_mysql:
            sync_to_mysql(performance_logger, args.limit)
        else:
            logging.info("Skipping MySQL sync")
            performance_logger.checkpoint("MySQL Sync (skipped)")
        
        # Finalize performance log
        performance_logger.checkpoint("Finalization")
        performance_logger.finalize()
        
        logging.info("Combined update completed successfully")
        
        # Print summary
        print("\nPerformance Summary:")
        print(f"Total Duration: {performance_logger.metrics['total_duration']:.2f} seconds")
        print("\nSQLite Update:")
        print(f"  Duration: {performance_logger.metrics['sqlite_update']['duration']:.2f} seconds")
        print(f"  URLs Processed: {performance_logger.metrics['sqlite_update']['urls_processed']}")
        print(f"  Tweets Processed: {performance_logger.metrics['sqlite_update']['tweets_processed']}")
        print(f"  Errors: {performance_logger.metrics['sqlite_update']['errors']}")
        print("\nMySQL Sync:")
        print(f"  Duration: {performance_logger.metrics['mysql_sync']['duration']:.2f} seconds")
        print(f"  URLs Synced: {performance_logger.metrics['mysql_sync']['urls_synced']}")
        print(f"  Tweets Synced: {performance_logger.metrics['mysql_sync']['tweets_synced']}")
        print(f"  Errors: {performance_logger.metrics['mysql_sync']['errors']}")
        
        return 0
    
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Finalize performance log
        performance_logger.finalize()
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
