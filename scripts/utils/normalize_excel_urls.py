#!/usr/bin/env python3
"""
Script to normalize URLs in Excel files (convert x.com to twitter.com).
"""

import os
import sys
import logging
import pandas as pd
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def normalize_urls_in_excel(excel_path, output_path=None):
    """Normalize URLs in Excel file (convert x.com to twitter.com)"""
    try:
        # Read the Excel file
        df = pd.read_excel(excel_path)
        logging.info(f"Read Excel file: {excel_path}")
        
        # Find the URL column
        url_column = None
        for col in df.columns:
            if 'twitter' in col.lower() or 'url' in col.lower():
                url_column = col
                break
        
        if not url_column:
            logging.error("No URL column found in Excel file")
            return False
        
        # Count URLs before normalization
        x_count = 0
        twitter_count = 0
        for url in df[url_column]:
            if 'x.com' in str(url):
                x_count += 1
            elif 'twitter.com' in str(url):
                twitter_count += 1
        
        logging.info(f"Before normalization: {x_count} x.com URLs, {twitter_count} twitter.com URLs")
        
        # Normalize URLs (convert x.com to twitter.com)
        df[url_column] = df[url_column].apply(
            lambda url: str(url).replace('x.com', 'twitter.com') if pd.notna(url) else url
        )
        
        # Count URLs after normalization
        x_count = 0
        twitter_count = 0
        for url in df[url_column]:
            if 'x.com' in str(url):
                x_count += 1
            elif 'twitter.com' in str(url):
                twitter_count += 1
        
        logging.info(f"After normalization: {x_count} x.com URLs, {twitter_count} twitter.com URLs")
        
        # Save the normalized Excel file
        if output_path is None:
            output_path = excel_path.replace('.xlsx', '_normalized.xlsx')
        
        df.to_excel(output_path, index=False)
        logging.info(f"Saved normalized Excel file to: {output_path}")
        
        return output_path
    
    except Exception as e:
        logging.error(f"Error normalizing URLs in Excel file: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Normalize URLs in Excel file (convert x.com to twitter.com)')
    parser.add_argument('--input', type=str, required=True, help='Path to the input Excel file')
    parser.add_argument('--output', type=str, help='Path to the output Excel file')
    
    args = parser.parse_args()
    
    # Normalize URLs in Excel file
    normalize_urls_in_excel(args.input, args.output)

if __name__ == "__main__":
    main()
