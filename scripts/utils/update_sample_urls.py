#!/usr/bin/env python3
"""
Script to update sample_urls.json with exchange and meme token information.
This script checks existing URLs for exchange or meme token status and adds new ones.
"""

import os
import sys
import logging
import json
import argparse
import re

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_json_file(file_path):
    """Load a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {str(e)}")
        return None

def save_json_file(data, file_path):
    """Save data to a JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Data saved to {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving data to {file_path}: {str(e)}")
        return False

def extract_handle_from_url(url):
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
    except Exception as e:
        logging.error(f"Error extracting Twitter handle from {url}: {str(e)}")
    
    return None

def is_exchange_url(url, exchange_handles):
    """Check if a URL belongs to an exchange"""
    handle = extract_handle_from_url(url)
    return handle and handle.lower() in exchange_handles

def is_meme_token_url(url, meme_token_handles):
    """Check if a URL belongs to a meme token"""
    handle = extract_handle_from_url(url)
    return handle and handle.lower() in meme_token_handles

def update_sample_urls(input_file, coinmarketcap_file, output_file):
    """Update sample_urls.json with exchange and meme token information"""
    # Load input file
    sample_data = load_json_file(input_file)
    if not sample_data:
        logging.error(f"Failed to load input file: {input_file}")
        return False
    
    # Load CoinMarketCap data
    cmc_data = load_json_file(coinmarketcap_file)
    if not cmc_data:
        logging.error(f"Failed to load CoinMarketCap data: {coinmarketcap_file}")
        return False
    
    # Extract exchange and meme token handles
    exchange_data = {item['twitter_handle'].lower(): item for item in cmc_data.get('exchanges', [])}
    meme_token_data = {item['twitter_handle'].lower(): item for item in cmc_data.get('meme_tokens', [])}
    
    # Track existing URLs
    existing_urls = set()
    
    # Update existing URLs
    for i, url_data in enumerate(sample_data['urls']):
        if isinstance(url_data, dict):
            url = url_data.get('url', '')
            existing_urls.add(url)
            
            # Extract handle from URL
            handle = extract_handle_from_url(url)
            if not handle:
                continue
            
            handle = handle.lower()
            
            # Check if it's an exchange
            if handle in exchange_data:
                exchange = exchange_data[handle]
                sample_data['urls'][i]['type'] = 'institution'
                sample_data['urls'][i]['subtype'] = 'exchange'
                sample_data['urls'][i]['coinmarketcap_url'] = exchange['coinmarketcap_url']
                logging.info(f"Updated URL {url} as exchange")
            
            # Check if it's a meme token
            elif handle in meme_token_data:
                token = meme_token_data[handle]
                sample_data['urls'][i]['type'] = 'institution'
                sample_data['urls'][i]['subtype'] = 'meme'
                sample_data['urls'][i]['coinmarketcap_url'] = token['coinmarketcap_url']
                logging.info(f"Updated URL {url} as meme token")
    
    # Add new exchanges that don't exist in the sample data
    for handle, exchange in exchange_data.items():
        url = exchange['nitter_url']
        if url not in existing_urls:
            new_entry = {
                'url': url,
                'description': f"{exchange['name']} Exchange",
                'type': 'institution',
                'subtype': 'exchange',
                'coinmarketcap_url': exchange['coinmarketcap_url']
            }
            sample_data['urls'].append(new_entry)
            existing_urls.add(url)
            logging.info(f"Added new exchange URL: {url}")
    
    # Add new meme tokens that don't exist in the sample data
    for handle, token in meme_token_data.items():
        url = token['nitter_url']
        if url not in existing_urls:
            new_entry = {
                'url': url,
                'description': f"{token['name']} Meme Token",
                'type': 'institution',
                'subtype': 'meme',
                'coinmarketcap_url': token['coinmarketcap_url']
            }
            sample_data['urls'].append(new_entry)
            existing_urls.add(url)
            logging.info(f"Added new meme token URL: {url}")
    
    # Save updated data
    return save_json_file(sample_data, output_file)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Update sample_urls.json with exchange and meme token information')
    parser.add_argument('--input', type=str, default='data/sample_urls_original.json', help='Input sample_urls.json file')
    parser.add_argument('--cmc-data', type=str, default='data/coinmarketcap_urls.json', help='CoinMarketCap data file')
    parser.add_argument('--output', type=str, default='data/sample_urls_with_cmc.json', help='Output file')
    
    args = parser.parse_args()
    
    # Update sample URLs
    if update_sample_urls(args.input, args.cmc_data, args.output):
        logging.info(f"Successfully updated sample URLs: {args.output}")
        return 0
    else:
        logging.error("Failed to update sample URLs")
        return 1

if __name__ == "__main__":
    sys.exit(main())
