#!/usr/bin/env python3
"""
Dynamic update script for Twitter data extraction.
This script uses activity levels to dynamically adjust tweet quantities.
"""

import os
import sys
import logging
import argparse
import time
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required modules
from src.database.activity_manager import ActivityManager
from src.database.local_database import LocalDatabase
from src.database.url_manager import URLManager
from src.twitter_client.twitter_scraper import TwitterScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/dynamic_update.log"),
        logging.StreamHandler()
    ]
)

class DynamicUpdate:
    """Dynamic update for Twitter data extraction"""
    
    def __init__(self, db_path='data/local_database.db'):
        """Initialize the dynamic update"""
        logging.info(f"Initializing dynamic update with database at {db_path}")
        
        self.db_path = db_path
        
        # Initialize components
        self.database = LocalDatabase(db_path=db_path)
        self.url_manager = URLManager(db_path=db_path)
        self.activity_manager = ActivityManager(db_path=db_path)
        self.scraper = TwitterScraper()
        
        logging.info("Dynamic update initialization complete")
    
    def run(self, batch_size=10, sleep_between_urls=2, limit=None, 
            performance_monitoring=False, parallel=False, num_threads=2):
        """Run the dynamic update"""
        logging.info("Starting dynamic update")
        logging.info(f"Time: {datetime.now().isoformat()}")
        logging.info(f"Batch size: {batch_size}, Sleep between URLs: {sleep_between_urls} seconds")
        logging.info(f"Parallel processing: {parallel}, Number of threads: {num_threads}")
        
        # Initialize performance metrics if monitoring is enabled
        performance_metrics = {}
        if performance_monitoring:
            performance_metrics = {
                'total_start_time': time.time(),
                'url_processing_time': 0,
                'tweet_scraping_time': 0,
                'db_storage_time': 0,
                'url_status_update_time': 0,
                'sleep_time': 0,
                'stats_generation_time': 0,
                'url_times': []
            }
        
        try:
            # Get active URLs
            if performance_monitoring:
                url_fetch_start = time.time()
                
            urls = self.url_manager.get_urls(status='active')
            
            if limit:
                urls = urls[:limit]
            
            total_urls = len(urls)
            logging.info(f"Found {total_urls} active URLs to process")
            
            if performance_monitoring:
                url_fetch_time = time.time() - url_fetch_start
                performance_metrics['url_fetch_time'] = f"{url_fetch_time:.2f} seconds"
            
            # Process URLs in batches
            processed_count = 0
            success_count = 0
            error_count = 0
            total_tweets = 0
            
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i+batch_size]
                logging.info(f"Processing batch {i//batch_size + 1}/{(total_urls + batch_size - 1)//batch_size}")
                
                # Process the batch of URLs
                if parallel:
                    # Use parallel processing
                    self._process_batch_parallel(batch, performance_monitoring, performance_metrics, 
                                               sleep_between_urls, num_threads)
                else:
                    # Use sequential processing
                    self._process_batch_sequential(batch, performance_monitoring, performance_metrics, 
                                                 sleep_between_urls)
                
                # Sleep between batches
                if i + batch_size < len(urls):
                    logging.info(f"Sleeping for {sleep_between_urls} seconds between batches")
                    
                    if performance_monitoring:
                        sleep_start_time = time.time()
                        
                    time.sleep(sleep_between_urls)
                    
                    if performance_monitoring:
                        sleep_time = time.time() - sleep_start_time
                        performance_metrics['sleep_time'] += sleep_time
            
            # Generate statistics
            logging.info("Generating statistics")
            
            if performance_monitoring:
                stats_start_time = time.time()
                
            stats = self.database.generate_stats()
            
            if performance_monitoring:
                stats_time = time.time() - stats_start_time
                performance_metrics['stats_generation_time'] = f"{stats_time:.2f} seconds"
            
            # Log completion
            logging.info("Dynamic update completed successfully")
            
            if stats:
                logging.info(f"Total URLs in database: {stats['total_urls']}")
                logging.info(f"Total tweets in database: {stats['total_tweets']}")
            
            # Calculate total time if performance monitoring is enabled
            if performance_monitoring:
                total_time = time.time() - performance_metrics['total_start_time']
                performance_metrics['total_time'] = f"{total_time:.2f} seconds"
                
                # Log performance metrics
                logging.info(f"Performance metrics: {performance_metrics}")
            
            result = {
                'processed_count': processed_count,
                'success_count': success_count,
                'error_count': error_count,
                'total_tweets': total_tweets,
                'completed_at': datetime.now().isoformat()
            }
            
            # Add performance metrics to result if monitoring is enabled
            if performance_monitoring:
                result['performance_details'] = performance_metrics
            
            return result
            
        except Exception as e:
            logging.error(f"Error in dynamic update: {str(e)}")
            return {
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            }
    
    def _process_batch_parallel(self, batch, performance_monitoring, performance_metrics, 
                              sleep_between_urls, num_threads):
        """Process a batch of URLs in parallel"""
        import concurrent.futures
        
        logging.info(f"Processing {len(batch)} URLs in parallel with {num_threads} threads")
        
        # Extract just the URLs from the batch
        batch_urls = [url_data['url'] for url_data in batch]
        
        # Define a worker function for each thread
        def process_url(url):
            try:
                # Get activity level for the URL
                activity_data = self.activity_manager.get_activity_level(url)
                
                if not activity_data:
                    logging.warning(f"No activity data for URL: {url}")
                    return {
                        'url': url,
                        'success': False,
                        'error': "No activity data",
                        'tweets': []
                    }
                
                # Get dynamic tweet quantities
                max_tweets = activity_data.get('max_tweets', 1)
                max_replies = activity_data.get('max_replies', 1)
                
                logging.info(f"Dynamic quantities for {url}: max_tweets={max_tweets}, max_replies={max_replies}")
                
                # Scrape the URL
                tweets = self.scraper.scrape_url(url, max_tweets=max_tweets, max_replies=max_replies)
                
                return {
                    'url': url,
                    'success': True,
                    'tweets': tweets
                }
            except Exception as e:
                logging.error(f"Error processing URL {url}: {str(e)}")
                return {
                    'url': url,
                    'success': False,
                    'error': str(e),
                    'tweets': []
                }
        
        # Use ThreadPoolExecutor to process URLs in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all URLs to the thread pool
            future_to_url = {executor.submit(process_url, url): url for url in batch_urls}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    
                    if result['success']:
                        # Store the tweets in the database
                        tweets = result['tweets']
                        if tweets:
                            stored_count = self.database.store_tweets(tweets, url)
                            logging.info(f"Stored {stored_count} tweets for URL: {url}")
                        else:
                            logging.warning(f"No tweets found for URL: {url}")
                        
                        # Update the URL status
                        self.url_manager.update_last_scraped(url)
                    else:
                        logging.error(f"Failed to process URL {url}: {result.get('error')}")
                        self.url_manager.update_url_status(url, 'error', result.get('error'))
                except Exception as e:
                    logging.error(f"Exception occurred while processing URL {url}: {str(e)}")
    
    def _process_batch_sequential(self, batch, performance_monitoring, performance_metrics, 
                                sleep_between_urls):
        """Process a batch of URLs sequentially"""
        for url_data in batch:
            url = url_data['url']
            
            try:
                logging.info(f"Processing URL: {url}")
                
                url_start_time = time.time()
                url_metrics = {'url': url} if performance_monitoring else None
                
                # Get activity level for the URL
                activity_data = self.activity_manager.get_activity_level(url)
                
                if not activity_data:
                    logging.warning(f"No activity data for URL: {url}")
                    continue
                
                # Get dynamic tweet quantities
                max_tweets = activity_data.get('max_tweets', 1)
                max_replies = activity_data.get('max_replies', 1)
                
                logging.info(f"Dynamic quantities for {url}: max_tweets={max_tweets}, max_replies={max_replies}")
                
                # Scrape the URL
                if performance_monitoring:
                    scrape_start_time = time.time()
                    
                tweets = self.scraper.scrape_url(url, max_tweets=max_tweets, max_replies=max_replies)
                
                if performance_monitoring:
                    scrape_time = time.time() - scrape_start_time
                    performance_metrics['tweet_scraping_time'] += scrape_time
                    if url_metrics:
                        url_metrics['scrape_time'] = f"{scrape_time:.2f} seconds"
                
                if tweets:
                    # Store the tweets in the database
                    if performance_monitoring:
                        db_start_time = time.time()
                        
                    stored_count = self.database.store_tweets(tweets, url)
                    
                    if performance_monitoring:
                        db_time = time.time() - db_start_time
                        performance_metrics['db_storage_time'] += db_time
                        if url_metrics:
                            url_metrics['db_time'] = f"{db_time:.2f} seconds"
                    
                    logging.info(f"Stored {stored_count} tweets for URL: {url}")
                else:
                    logging.warning(f"No tweets found for URL: {url}")
                
                # Update the URL status
                if performance_monitoring:
                    update_start_time = time.time()
                    
                self.url_manager.update_last_scraped(url)
                
                if performance_monitoring:
                    update_time = time.time() - update_start_time
                    performance_metrics['url_status_update_time'] += update_time
                    if url_metrics:
                        url_metrics['update_time'] = f"{update_time:.2f} seconds"
                
                # Calculate total time for this URL
                if performance_monitoring:
                    url_total_time = time.time() - url_start_time
                    if url_metrics:
                        url_metrics['total_time'] = f"{url_total_time:.2f} seconds"
                    performance_metrics['url_times'].append(url_metrics)
                
                # Sleep between URLs
                if sleep_between_urls > 0:
                    logging.info(f"Sleeping for {sleep_between_urls} seconds")
                    
                    if performance_monitoring:
                        sleep_start_time = time.time()
                        
                    time.sleep(sleep_between_urls)
                    
                    if performance_monitoring:
                        sleep_time = time.time() - sleep_start_time
                        performance_metrics['sleep_time'] += sleep_time
                
            except Exception as e:
                logging.error(f"Error processing URL {url}: {str(e)}")
                self.url_manager.update_url_status(url, 'error', str(e))

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Dynamic update for Twitter data extraction')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for URL processing')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between URLs (seconds)')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--threads', type=int, default=2, help='Number of threads for parallel processing')
    parser.add_argument('--performance', action='store_true', help='Enable performance monitoring')
    
    args = parser.parse_args()
    
    # Initialize and run the dynamic update
    updater = DynamicUpdate()
    result = updater.run(
        batch_size=args.batch_size,
        sleep_between_urls=args.sleep,
        limit=args.limit,
        performance_monitoring=args.performance,
        parallel=args.parallel,
        num_threads=args.threads
    )
    
    # Print summary
    print("\nDynamic Update Summary:")
    print(f"Completed at: {result.get('completed_at')}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Processed URLs: {result.get('processed_count', 0)}")
        print(f"Success: {result.get('success_count', 0)}")
        print(f"Errors: {result.get('error_count', 0)}")
        print(f"Total tweets: {result.get('total_tweets', 0)}")
        
        if args.performance and 'performance_details' in result:
            perf = result['performance_details']
            print("\nPerformance Details:")
            print(f"Total time: {perf.get('total_time', 'N/A')}")
            print(f"URL fetch time: {perf.get('url_fetch_time', 'N/A')}")
            print(f"Tweet scraping time: {perf.get('tweet_scraping_time', 0):.2f} seconds")
            print(f"Database storage time: {perf.get('db_storage_time', 0):.2f} seconds")
            print(f"URL status update time: {perf.get('url_status_update_time', 0):.2f} seconds")
            print(f"Sleep time: {perf.get('sleep_time', 0):.2f} seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
