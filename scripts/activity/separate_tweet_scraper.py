#!/usr/bin/env python3
"""
Separate tweet scraper script for Twitter data extraction.
This script separates the tweet scraping and database storage functionality.
"""

import os
import sys
import logging
import argparse
import time
import json
from datetime import datetime
import sqlite3

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import required modules
from src.database.activity_manager import ActivityManager
from src.database.url_manager import URLManager
from src.twitter_client.twitter_scraper import TwitterScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/separate_tweet_scraper.log"),
        logging.StreamHandler()
    ]
)

class SeparateTweetScraper:
    """Separate tweet scraper for Twitter data extraction"""
    
    def __init__(self, db_path='data/local_database.db'):
        """Initialize the separate tweet scraper"""
        logging.info(f"Initializing separate tweet scraper with database at {db_path}")
        
        self.db_path = db_path
        
        # Initialize components
        self.url_manager = URLManager(db_path=db_path)
        self.activity_manager = ActivityManager(db_path=db_path)
        self.scraper = TwitterScraper()
        
        logging.info("Separate tweet scraper initialization complete")
    
    def run(self, batch_size=10, sleep_between_urls=2, limit=None, 
            performance_monitoring=False, parallel=False, num_threads=2,
            force_max_tweets=None):
        """Run the separate tweet scraper"""
        logging.info("Starting separate tweet scraper")
        logging.info(f"Time: {datetime.now().isoformat()}")
        logging.info(f"Batch size: {batch_size}, Sleep between URLs: {sleep_between_urls} seconds")
        logging.info(f"Parallel processing: {parallel}, Number of threads: {num_threads}")
        if force_max_tweets is not None:
            logging.info(f"Force max tweets: {force_max_tweets}")
        
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
                    batch_results = self._process_batch_parallel(batch, performance_monitoring, performance_metrics, 
                                               sleep_between_urls, num_threads, force_max_tweets)
                else:
                    # Use sequential processing
                    batch_results = self._process_batch_sequential(batch, performance_monitoring, performance_metrics, 
                                                 sleep_between_urls, force_max_tweets)
                
                # Store the results
                for result in batch_results:
                    processed_count += 1
                    if result['success']:
                        success_count += 1
                        total_tweets += len(result['tweets'])
                    else:
                        error_count += 1
                
                # Sleep between batches
                if i + batch_size < len(urls):
                    logging.info(f"Sleeping for {sleep_between_urls} seconds between batches")
                    
                    if performance_monitoring:
                        sleep_start_time = time.time()
                        
                    time.sleep(sleep_between_urls)
                    
                    if performance_monitoring:
                        sleep_time = time.time() - sleep_start_time
                        performance_metrics['sleep_time'] += sleep_time
            
            # Log completion
            logging.info("Separate tweet scraper completed successfully")
            logging.info(f"Processed {processed_count} URLs, {success_count} successful, {error_count} errors")
            logging.info(f"Total tweets extracted: {total_tweets}")
            
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
            logging.error(f"Error in separate tweet scraper: {str(e)}")
            return {
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            }
    
    def _process_batch_parallel(self, batch, performance_monitoring, performance_metrics, 
                              sleep_between_urls, num_threads, force_max_tweets=None):
        """Process a batch of URLs in parallel"""
        import concurrent.futures
        
        logging.info(f"Processing {len(batch)} URLs in parallel with {num_threads} threads")
        
        # Extract just the URLs from the batch
        batch_urls = [url_data['url'] for url_data in batch]
        batch_results = []
        
        # Define a worker function for each thread
        def process_url(url, force_max_tweets=force_max_tweets):
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
                
                # Override max_tweets if force_max_tweets is provided
                if force_max_tweets is not None:
                    max_tweets = force_max_tweets
                    logging.info(f"Overriding max_tweets with forced value: {max_tweets}")
                
                logging.info(f"Dynamic quantities for {url}: max_tweets={max_tweets}, max_replies={max_replies}")
                
                # Scrape the URL
                tweets = self.scraper.scrape_url(url, max_tweets=max_tweets, max_replies=max_replies)
                
                # Add source_url to each tweet
                for tweet in tweets:
                    tweet['source_url'] = url
                
                # Save tweets to a JSON file
                output_file = f"data/tweets/{url.split('/')[-1]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                
                with open(output_file, 'w') as f:
                    json.dump(tweets, f, indent=2)
                
                logging.info(f"Saved {len(tweets)} tweets to {output_file}")
                
                # Update the URL status
                self.url_manager.update_last_scraped(url)
                
                return {
                    'url': url,
                    'success': True,
                    'tweets': tweets,
                    'output_file': output_file
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
                    batch_results.append(result)
                except Exception as e:
                    logging.error(f"Exception occurred while processing URL {url}: {str(e)}")
                    batch_results.append({
                        'url': url,
                        'success': False,
                        'error': str(e),
                        'tweets': []
                    })
        
        return batch_results
    
    def _process_batch_sequential(self, batch, performance_monitoring, performance_metrics, 
                                sleep_between_urls, force_max_tweets=None):
        """Process a batch of URLs sequentially"""
        batch_results = []
        
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
                    batch_results.append({
                        'url': url,
                        'success': False,
                        'error': "No activity data",
                        'tweets': []
                    })
                    continue
                
                # Get dynamic tweet quantities
                max_tweets = activity_data.get('max_tweets', 1)
                max_replies = activity_data.get('max_replies', 1)
                
                # Override max_tweets if force_max_tweets is provided
                if force_max_tweets is not None:
                    max_tweets = force_max_tweets
                    logging.info(f"Overriding max_tweets with forced value: {max_tweets}")
                
                logging.info(f"Dynamic quantities for {url}: max_tweets={max_tweets}, max_replies={max_replies}")
                
                # Scrape the URL
                if performance_monitoring:
                    scrape_start_time = time.time()
                    
                tweets = self.scraper.scrape_url(url, max_tweets=max_tweets, max_replies=max_replies)
                
                # Add source_url to each tweet
                for tweet in tweets:
                    tweet['source_url'] = url
                
                if performance_monitoring:
                    scrape_time = time.time() - scrape_start_time
                    performance_metrics['tweet_scraping_time'] += scrape_time
                    if url_metrics:
                        url_metrics['scrape_time'] = f"{scrape_time:.2f} seconds"
                
                # Save tweets to a JSON file
                output_file = f"data/tweets/{url.split('/')[-1]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                
                with open(output_file, 'w') as f:
                    json.dump(tweets, f, indent=2)
                
                logging.info(f"Saved {len(tweets)} tweets to {output_file}")
                
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
                
                batch_results.append({
                    'url': url,
                    'success': True,
                    'tweets': tweets,
                    'output_file': output_file
                })
                
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
                batch_results.append({
                    'url': url,
                    'success': False,
                    'error': str(e),
                    'tweets': []
                })
        
        return batch_results

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Separate tweet scraper for Twitter data extraction')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for URL processing')
    parser.add_argument('--sleep', type=int, default=2, help='Sleep time between URLs (seconds)')
    parser.add_argument('--limit', type=int, help='Limit the number of URLs to process')
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--threads', type=int, default=2, help='Number of threads for parallel processing')
    parser.add_argument('--performance', action='store_true', help='Enable performance monitoring')
    parser.add_argument('--force-max-tweets', type=int, help='Force a specific number of tweets to retrieve per URL')
    
    args = parser.parse_args()
    
    # Initialize and run the separate tweet scraper
    scraper = SeparateTweetScraper()
    result = scraper.run(
        batch_size=args.batch_size,
        sleep_between_urls=args.sleep,
        limit=args.limit,
        performance_monitoring=args.performance,
        parallel=args.parallel,
        num_threads=args.threads,
        force_max_tweets=args.force_max_tweets
    )
    
    # Print summary
    print("\nSeparate Tweet Scraper Summary:")
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
            print(f"URL status update time: {perf.get('url_status_update_time', 0):.2f} seconds")
            print(f"Sleep time: {perf.get('sleep_time', 0):.2f} seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
