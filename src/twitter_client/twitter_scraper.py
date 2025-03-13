#!/usr/bin/env python3
"""
Twitter scraper module.
This module provides functionality for scraping tweets using agent-twitter-client.
"""

import os
import sys
import json
import logging
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TwitterScraper:
    """Twitter scraper using agent-twitter-client"""
    
    def __init__(self, client_dir=None):
        """Initialize the Twitter scraper"""
        # Set the client directory
        if client_dir is None:
            # Use the directory of this file
            self.client_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.client_dir = client_dir
        
        # Check if the client directory exists
        if not os.path.exists(self.client_dir):
            raise ValueError(f"Client directory {self.client_dir} does not exist")
        
        # Check if the Twitter client exists
        self.client_path = os.path.join(self.client_dir, 'twitter_client.js')
        if not os.path.exists(self.client_path):
            raise ValueError(f"Twitter client {self.client_path} does not exist")
        
        # Check if Node.js is installed
        try:
            subprocess.run(['node', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise ValueError("Node.js is not installed or not in PATH")
        
        # Install dependencies if needed
        if not os.path.exists(os.path.join(self.client_dir, 'node_modules')):
            logging.info("Installing dependencies...")
            subprocess.run(['npm', 'install'], cwd=self.client_dir, check=True)
    
    def extract_username_from_url(self, url):
        """Extract the username from a URL"""
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        if not path_parts:
            logging.error(f"Invalid URL format: {url}")
            return None
        
        username = path_parts[0]
        logging.info(f"Extracted username: {username}")
        return username
    
    def scrape_url(self, url, max_tweets=10, max_replies=30):
        """Scrape tweets from a URL"""
        logging.info(f"Scraping URL: {url} (max tweets: {max_tweets}, max replies: {max_replies})")
        
        # Extract the username from the URL
        username = self.extract_username_from_url(url)
        if not username:
            return []
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            output_file = temp_file.name
        
        try:
            # Run the Twitter client
            logging.info(f"Running Twitter client for {username}...")
            process = subprocess.run(
                ['node', self.client_path, username, str(max_tweets), str(max_replies), output_file],
                cwd=self.client_dir,
                check=True,
                capture_output=True,
                text=True
            )
            
            logging.info(process.stdout)
            
            # Check if the output file exists
            if not os.path.exists(output_file):
                logging.error(f"Output file {output_file} does not exist")
                return []
            
            # Load the tweets from the output file
            with open(output_file, 'r') as f:
                result = json.load(f)
            
            # Get tweets and user ID from the result
            tweets = result.get('tweets', [])
            user_id = result.get('userId')
            
            if user_id:
                logging.info(f"Got user ID for {username}: {user_id}")
                
                # Update the URL with the user ID
                self.update_url_user_id(url, user_id)
            
            # Convert the tweets to our format
            formatted_tweets = []
            for tweet in tweets:
                formatted_tweet = {
                    'tweet_id': tweet.get('id', ''),
                    'content': tweet.get('text', ''),
                    'author': username,
                    'created_at': tweet.get('timeParsed') or datetime.now().isoformat(),
                    'likes': tweet.get('likes', 0),
                    'retweets': tweet.get('retweets', 0),
                    'replies': tweet.get('replies', 0),
                    'views': tweet.get('views', 0),
                    'source_url': url,
                    'user_id': user_id,  # Add user_id to the formatted tweet
                    'hashtags': tweet.get('hashtags', []),
                    'is_reply': 1 if tweet.get('isReply', False) else 0,  # Add is_reply field
                    'reply_to': tweet.get('replyToId', None),  # Add reply_to field
                    'conversation_id': tweet.get('conversationId', None)  # Add conversation_id field
                }
                formatted_tweets.append(formatted_tweet)
            
            logging.info(f"Extracted {len(formatted_tweets)} tweets from {url}")
            
            return formatted_tweets
            
        except Exception as e:
            logging.error(f"Error scraping URL {url}: {str(e)}")
            return []
        finally:
            # Remove the temporary file
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def update_url_user_id(self, url, user_id):
        """Update the user ID for a URL"""
        try:
            # Connect to the database
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data/local_database.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Update the user ID
            cursor.execute('''
            UPDATE url_tracking 
            SET user_id = ?
            WHERE url = ?
            ''', (user_id, url))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Updated user ID for URL {url}: {user_id}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error updating user ID for URL {url}: {str(e)}")
            return False
    
    def extract_user_id_from_handle(self, handle):
        """Extract the user ID from a Twitter handle without scraping tweets"""
        logging.info(f"Extracting user ID for handle: {handle}")
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            output_file = temp_file.name
        
        try:
            # Run a modified version of the Twitter client that only gets the user ID
            logging.info(f"Running Twitter client to get user ID for {handle}...")
            process = subprocess.run(
                ['node', self.client_path, handle, '1', output_file],
                cwd=self.client_dir,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Check if the output file exists
            if not os.path.exists(output_file):
                logging.error(f"Output file {output_file} does not exist")
                return None
            
            # Load the result from the output file
            with open(output_file, 'r') as f:
                result = json.load(f)
            
            # Get user ID from the result
            user_id = result.get('userId')
            
            if user_id:
                logging.info(f"Got user ID for {handle}: {user_id}")
                return user_id
            else:
                logging.warning(f"Could not get user ID for {handle}")
                return None
                
        except Exception as e:
            logging.error(f"Error extracting user ID for handle {handle}: {str(e)}")
            return None
        finally:
            # Remove the temporary file
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def scrape_urls(self, urls, max_tweets=10, max_replies=5, batch_size=10, sleep_between_urls=2):
        """Scrape tweets from multiple URLs"""
        logging.info(f"Scraping {len(urls)} URLs...")
        
        all_tweets = []
        
        for i, url in enumerate(urls):
            logging.info(f"Scraping URL {i+1}/{len(urls)}: {url}")
            
            # Scrape the URL
            tweets = self.scrape_url(url, max_tweets, max_replies)
            all_tweets.extend(tweets)
            
            # Sleep between URLs
            if i < len(urls) - 1 and sleep_between_urls > 0:
                logging.info(f"Sleeping for {sleep_between_urls} seconds...")
                import time
                time.sleep(sleep_between_urls)
        
        logging.info(f"Scraped {len(all_tweets)} tweets from {len(urls)} URLs")
        
        return all_tweets
        
    def scrape_urls_parallel(self, urls, max_tweets=10, max_replies=5, num_threads=2, sleep_between_urls=2):
        """Scrape tweets from multiple URLs in parallel using multiple threads"""
        import concurrent.futures
        import time
        
        logging.info(f"Scraping {len(urls)} URLs in parallel with {num_threads} threads...")
        
        all_tweets = []
        processed_count = 0
        
        # Define a worker function for each thread
        def scrape_worker(url):
            try:
                logging.info(f"Thread processing URL: {url}")
                tweets = self.scrape_url(url, max_tweets=max_tweets, max_replies=max_replies)
                
                # Sleep between URLs to avoid rate limiting
                if sleep_between_urls > 0:
                    time.sleep(sleep_between_urls)
                
                return {
                    'url': url,
                    'tweets': tweets,
                    'success': True,
                    'error': None
                }
            except Exception as e:
                logging.error(f"Error in thread processing URL {url}: {str(e)}")
                return {
                    'url': url,
                    'tweets': [],
                    'success': False,
                    'error': str(e)
                }
        
        # Use ThreadPoolExecutor to process URLs in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all URLs to the thread pool
            future_to_url = {executor.submit(scrape_worker, url): url for url in urls}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    processed_count += 1
                    
                    if result['success']:
                        all_tweets.extend(result['tweets'])
                        logging.info(f"Processed {processed_count}/{len(urls)} URLs. Got {len(result['tweets'])} tweets from {result['url']}")
                    else:
                        logging.error(f"Failed to process URL {result['url']}: {result['error']}")
                except Exception as e:
                    logging.error(f"Exception occurred while processing URL {url}: {str(e)}")
        
        logging.info(f"Parallel scraping completed. Scraped {len(all_tweets)} tweets from {len(urls)} URLs using {num_threads} threads")
        
        return all_tweets
