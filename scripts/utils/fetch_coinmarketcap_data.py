#!/usr/bin/env python3
"""
Script to fetch top exchanges and meme tokens from CoinMarketCap and convert to nitter URLs.
This script fetches data from CoinMarketCap and adds the URLs to the database.
"""

import os
import sys
import logging
import json
import argparse
import requests
from bs4 import BeautifulSoup
import time
import random

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_twitter_handle_from_coinmarketcap(url):
    """Extract Twitter handle from a CoinMarketCap page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.warning(f"Failed to fetch {url}: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for Twitter links in the social media section
        social_links = soup.select('a[href*="twitter.com"]')
        
        for link in social_links:
            href = link.get('href', '')
            if 'twitter.com/' in href:
                # Extract the handle from the URL
                parts = href.split('twitter.com/')
                if len(parts) > 1:
                    handle = parts[1].split('?')[0].strip('/')
                    if handle and handle != 'share':
                        return handle
        
        logging.warning(f"No Twitter handle found for {url}")
        return None
        
    except Exception as e:
        logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
        return None

def fetch_top_exchanges(limit=50):
    """Fetch top exchanges from CoinMarketCap"""
    logging.info(f"Fetching top {limit} exchanges from CoinMarketCap")
    
    exchanges = []
    url = "https://coinmarketcap.com/rankings/exchanges/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to fetch exchanges: {response.status_code}")
            return exchanges
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find exchange rows in the table
        exchange_rows = soup.select('table tbody tr')
        
        count = 0
        for row in exchange_rows:
            if count >= limit:
                break
                
            try:
                # Extract exchange name and link
                name_cell = row.select_one('td:nth-child(2)')
                if not name_cell:
                    continue
                    
                link_element = name_cell.select_one('a')
                if not link_element:
                    continue
                    
                exchange_name = link_element.text.strip()
                exchange_link = link_element.get('href')
                
                if not exchange_link.startswith('http'):
                    exchange_link = f"https://coinmarketcap.com{exchange_link}"
                
                # Get Twitter handle
                twitter_handle = get_twitter_handle_from_coinmarketcap(exchange_link)
                
                if twitter_handle:
                    exchanges.append({
                        'name': exchange_name,
                        'twitter_handle': twitter_handle,
                        'coinmarketcap_url': exchange_link,
                        'nitter_url': f"https://nitter.net/{twitter_handle}",
                        'type': 'institution',
                        'subtype': 'exchange'
                    })
                    count += 1
                    logging.info(f"Found exchange {exchange_name} with Twitter handle @{twitter_handle}")
                
                # Add a small delay to avoid rate limiting
                time.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logging.error(f"Error processing exchange row: {str(e)}")
                continue
        
        logging.info(f"Found {len(exchanges)} exchanges with Twitter handles")
        return exchanges
        
    except Exception as e:
        logging.error(f"Error fetching exchanges: {str(e)}")
        return exchanges

def fetch_top_meme_tokens(limit=50):
    """Fetch top meme tokens from CoinMarketCap"""
    logging.info(f"Fetching top {limit} meme tokens from CoinMarketCap")
    
    meme_tokens = []
    url = "https://coinmarketcap.com/view/memes/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to fetch meme tokens: {response.status_code}")
            return meme_tokens
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find token rows in the table
        token_rows = soup.select('table tbody tr')
        
        count = 0
        for row in token_rows:
            if count >= limit:
                break
                
            try:
                # Extract token name and link
                name_cell = row.select_one('td:nth-child(3)')
                if not name_cell:
                    continue
                    
                link_element = name_cell.select_one('a')
                if not link_element:
                    continue
                    
                token_name = link_element.text.strip()
                token_link = link_element.get('href')
                
                if not token_link.startswith('http'):
                    token_link = f"https://coinmarketcap.com{token_link}"
                
                # Get Twitter handle
                twitter_handle = get_twitter_handle_from_coinmarketcap(token_link)
                
                if twitter_handle:
                    meme_tokens.append({
                        'name': token_name,
                        'twitter_handle': twitter_handle,
                        'coinmarketcap_url': token_link,
                        'nitter_url': f"https://nitter.net/{twitter_handle}",
                        'type': 'institution',
                        'subtype': 'meme'
                    })
                    count += 1
                    logging.info(f"Found meme token {token_name} with Twitter handle @{twitter_handle}")
                
                # Add a small delay to avoid rate limiting
                time.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logging.error(f"Error processing meme token row: {str(e)}")
                continue
        
        logging.info(f"Found {len(meme_tokens)} meme tokens with Twitter handles")
        return meme_tokens
        
    except Exception as e:
        logging.error(f"Error fetching meme tokens: {str(e)}")
        return meme_tokens

def save_to_json(data, output_file):
    """Save data to a JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Data saved to {output_file}")
        return True
    except Exception as e:
        logging.error(f"Error saving data to {output_file}: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Fetch top exchanges and meme tokens from CoinMarketCap')
    parser.add_argument('--exchanges', type=int, default=50, help='Number of top exchanges to fetch')
    parser.add_argument('--meme-tokens', type=int, default=50, help='Number of top meme tokens to fetch')
    parser.add_argument('--output', type=str, default='data/coinmarketcap_urls.json', help='Output file path')
    
    args = parser.parse_args()
    
    # Fetch exchanges
    exchanges = fetch_top_exchanges(args.exchanges)
    
    # Fetch meme tokens
    meme_tokens = fetch_top_meme_tokens(args.meme_tokens)
    
    # Combine results
    results = {
        'exchanges': exchanges,
        'meme_tokens': meme_tokens,
        'urls': [
            {
                'url': item['nitter_url'],
                'description': f"{item['name']} ({item['subtype']})",
                'type': 'institution',
                'subtype': item['subtype'],
                'twitter_handle': item['twitter_handle']
            }
            for item in exchanges + meme_tokens
        ]
    }
    
    # Save to JSON
    save_to_json(results, args.output)

if __name__ == "__main__":
    main()
