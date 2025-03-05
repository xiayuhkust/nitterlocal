#!/usr/bin/env python3
"""
Script to compare and merge URLs from CoinMarketCap with existing URLs in sample_urls.json.
This script identifies missing URLs and adds them to sample_urls.json.
"""

import os
import sys
import logging
import json
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_twitter_handle(url):
    """Extract Twitter handle from a nitter URL"""
    if not url or 'nitter.net/' not in url:
        return None
    
    try:
        # Extract the handle from the URL
        parts = url.split('nitter.net/')
        if len(parts) > 1:
            handle = parts[1].split('?')[0].strip('/')
            if handle:
                return handle.lower()
    except Exception:
        pass
    
    return None

def merge_urls(sample_urls_file, coinmarketcap_urls_file, output_file=None):
    """Compare and merge URLs from CoinMarketCap with existing URLs in sample_urls.json"""
    logging.info(f"Comparing and merging URLs from {coinmarketcap_urls_file} with {sample_urls_file}")
    
    try:
        # Load sample URLs
        with open(sample_urls_file, 'r') as f:
            sample_data = json.load(f)
        
        # Load CoinMarketCap URLs
        with open(coinmarketcap_urls_file, 'r') as f:
            coinmarketcap_data = json.load(f)
        
        # Extract Twitter handles from sample URLs
        sample_handles = set()
        for url_data in sample_data.get('urls', []):
            if isinstance(url_data, dict) and 'url' in url_data:
                handle = extract_twitter_handle(url_data['url'])
                if handle:
                    sample_handles.add(handle)
        
        logging.info(f"Found {len(sample_handles)} unique Twitter handles in {sample_urls_file}")
        
        # Identify missing URLs
        missing_urls = []
        for url_data in coinmarketcap_data.get('urls', []):
            if isinstance(url_data, dict) and 'url' in url_data:
                handle = extract_twitter_handle(url_data['url'])
                if handle and handle not in sample_handles:
                    # Add current timestamp
                    url_data['last_checked'] = datetime.now().isoformat()
                    url_data['status'] = 'active'
                    url_data['error_count'] = 0
                    url_data['tweet_count'] = 0
                    
                    missing_urls.append(url_data)
                    sample_handles.add(handle)  # Add to set to avoid duplicates
        
        logging.info(f"Found {len(missing_urls)} missing URLs from CoinMarketCap")
        
        # Add missing URLs to sample data
        sample_data['urls'].extend(missing_urls)
        
        # Save merged data
        if output_file:
            output_path = output_file
        else:
            output_path = sample_urls_file
        
        with open(output_path, 'w') as f:
            json.dump(sample_data, f, indent=4)
        
        logging.info(f"Merged data saved to {output_path}")
        
        return {
            'total_sample_urls': len(sample_data.get('urls', [])),
            'total_coinmarketcap_urls': len(coinmarketcap_data.get('urls', [])),
            'missing_urls': len(missing_urls),
            'merged_urls': len(sample_data.get('urls', []))
        }
        
    except Exception as e:
        logging.error(f"Error merging URLs: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Compare and merge URLs from CoinMarketCap with existing URLs in sample_urls.json')
    parser.add_argument('--sample-urls', type=str, default='data/sample_urls.json', help='Path to the sample URLs JSON file')
    parser.add_argument('--coinmarketcap-urls', type=str, default='data/coinmarketcap_urls.json', help='Path to the CoinMarketCap URLs JSON file')
    parser.add_argument('--output', type=str, help='Output file path (defaults to sample-urls if not specified)')
    
    args = parser.parse_args()
    
    # Merge URLs
    result = merge_urls(args.sample_urls, args.coinmarketcap_urls, args.output)
    
    if result:
        print(f"Merge completed successfully:")
        print(f"  Total sample URLs: {result['total_sample_urls']}")
        print(f"  Total CoinMarketCap URLs: {result['total_coinmarketcap_urls']}")
        print(f"  Missing URLs added: {result['missing_urls']}")
        print(f"  Total merged URLs: {result['merged_urls']}")

if __name__ == "__main__":
    main()
