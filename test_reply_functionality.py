#!/usr/bin/env python3
"""
Test script for reply functionality.
This script tests the ability to extract, store, and query replies.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the database module
from src.database.local_database import LocalDatabase
from src.twitter_client.twitter_scraper import TwitterScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_reply_functionality():
    """Test the reply functionality"""
    logging.info("Testing reply functionality")
    
    try:
        # Initialize the database with a test path
        db_path = 'data/test_reply_database.db'
        if os.path.exists(db_path):
            os.remove(db_path)
        
        logging.info(f"Creating test database at {db_path}")
        db = LocalDatabase(db_path=db_path)
        
        # Add a test URL
        test_url = 'https://twitter.com/elonmusk'
        db.add_url(test_url, description="Elon Musk", url_type="kol")
        
        # Initialize the Twitter scraper
        scraper = TwitterScraper()
        
        # Test scraping user's replies to others
        logging.info("Testing scraping user's replies to others")
        user_replies = scraper.scrape_user_replies(test_url, max_tweets=5)
        
        if user_replies:
            logging.info(f"Found {len(user_replies)} replies from user")
            
            # Store the replies
            db.store_tweets(user_replies, test_url)
            
            # Verify that the replies were stored
            stored_replies = db.get_tweets(source_url=test_url)
            reply_count = sum(1 for reply in stored_replies if reply.get('is_reply'))
            logging.info(f"Retrieved {reply_count} stored replies out of {len(stored_replies)} total tweets")
            
            # Verify reply metadata
            for reply in stored_replies:
                if reply.get('is_reply'):
                    logging.info(f"Reply ID: {reply['tweet_id']}")
                    logging.info(f"In reply to: {reply.get('in_reply_to_status_id')}")
                    logging.info(f"Conversation ID: {reply.get('conversation_id')}")
        else:
            logging.warning("No replies found from user")
        
        # Test scraping replies to the user
        logging.info("Testing scraping replies to the user")
        replies_to_user = scraper.scrape_replies_to_user(test_url, max_tweets=5)
        
        if replies_to_user:
            logging.info(f"Found {len(replies_to_user)} replies to user")
            
            # Store the replies
            db.store_tweets(replies_to_user, test_url)
            
            # Verify that the replies were stored
            all_stored_tweets = db.get_tweets(source_url=test_url)
            all_reply_count = sum(1 for reply in all_stored_tweets if reply.get('is_reply'))
            logging.info(f"Retrieved {all_reply_count} total stored replies out of {len(all_stored_tweets)} total tweets")
            
            # Verify reply metadata for replies to user
            for reply in replies_to_user:
                logging.info(f"Reply to user - ID: {reply['tweet_id']}")
                logging.info(f"Reply to user - Author: {reply['author']}")
                logging.info(f"Reply to user - In reply to: {reply.get('in_reply_to_status_id')}")
                logging.info(f"Reply to user - Conversation ID: {reply.get('conversation_id')}")
        else:
            logging.warning("No replies found to user")
        
        # Test querying replies
        logging.info("Testing querying replies")
        
        # Add a method to get replies
        def get_replies(db, is_reply=True):
            """Get replies from the database"""
            try:
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM tweets WHERE is_reply = ? LIMIT 100", (1 if is_reply else 0,))
                
                columns = [column[0] for column in cursor.description]
                replies = []
                
                for row in cursor.fetchall():
                    reply_data = dict(zip(columns, row))
                    replies.append(reply_data)
                
                conn.close()
                
                return replies
                
            except Exception as e:
                logging.error(f"Error getting replies from database: {str(e)}")
                return []
        
        # Get all replies
        import sqlite3
        all_replies = get_replies(db)
        logging.info(f"Retrieved {len(all_replies)} replies using direct query")
        
        # Get replies by conversation ID
        if all_replies:
            conversation_id = all_replies[0].get('conversation_id')
            if conversation_id:
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM tweets WHERE conversation_id = ?", (conversation_id,))
                
                columns = [column[0] for column in cursor.description]
                conversation_replies = []
                
                for row in cursor.fetchall():
                    reply_data = dict(zip(columns, row))
                    conversation_replies.append(reply_data)
                
                conn.close()
                
                logging.info(f"Retrieved {len(conversation_replies)} replies in conversation {conversation_id}")
        
        logging.info("Reply functionality test completed")
        return True
        
    except Exception as e:
        logging.error(f"Error testing reply functionality: {str(e)}")
        return False

if __name__ == "__main__":
    test_reply_functionality()
