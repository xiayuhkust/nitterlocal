#!/usr/bin/env python3
"""
Script to convert nitter URLs to Twitter URLs in sample_urls_with_cmc.json.
"""

import os
import sys
import logging
import json
import argparse

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

def convert_nitter_to_twitter(url):
    """Convert a nitter URL to a Twitter URL"""
    if not url or 'nitter.net/' not in url:
        return url
    
    try:
        # Replace nitter.net with twitter.com
        return url.replace('nitter.net/', 'twitter.com/')
    except Exception as e:
        logging.error(f"Error converting URL {url}: {str(e)}")
        return url

def update_urls_in_file(input_file, output_file=None):
    """Update URLs in the file from nitter to Twitter format"""
    if output_file is None:
        output_file = input_file
    
    # Load input file
    data = load_json_file(input_file)
    if not data:
        logging.error(f"Failed to load input file: {input_file}")
        return False
    
    # Convert URLs
    converted_count = 0
    for i, url_data in enumerate(data['urls']):
        if isinstance(url_data, dict) and 'url' in url_data:
            old_url = url_data['url']
            new_url = convert_nitter_to_twitter(old_url)
            
            if old_url != new_url:
                data['urls'][i]['url'] = new_url
                converted_count += 1
                logging.info(f"Converted: {old_url} -> {new_url}")
            
            # Also convert coinmarketcap_url if it exists and contains nitter
            if 'coinmarketcap_url' in url_data and 'nitter.net' in url_data['coinmarketcap_url']:
                old_cmc_url = url_data['coinmarketcap_url']
                new_cmc_url = convert_nitter_to_twitter(old_cmc_url)
                
                if old_cmc_url != new_cmc_url:
                    data['urls'][i]['coinmarketcap_url'] = new_cmc_url
                    logging.info(f"Converted CMC URL: {old_cmc_url} -> {new_cmc_url}")
        
        elif isinstance(url_data, str) and 'nitter.net' in url_data:
            old_url = url_data
            new_url = convert_nitter_to_twitter(old_url)
            
            if old_url != new_url:
                data['urls'][i] = new_url
                converted_count += 1
                logging.info(f"Converted: {old_url} -> {new_url}")
    
    logging.info(f"Converted {converted_count} URLs from nitter to Twitter format")
    
    # Save updated data
    return save_json_file(data, output_file)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Convert nitter URLs to Twitter URLs in sample_urls_with_cmc.json')
    parser.add_argument('--input', type=str, default='data/sample_urls_with_cmc.json', help='Input file')
    parser.add_argument('--output', type=str, help='Output file (defaults to input file)')
    
    args = parser.parse_args()
    
    # Update URLs in the file
    if update_urls_in_file(args.input, args.output):
        logging.info(f"Successfully updated URLs in {args.output or args.input}")
        return 0
    else:
        logging.error(f"Failed to update URLs in {args.input}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
