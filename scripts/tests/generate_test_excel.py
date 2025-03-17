#!/usr/bin/env python3
"""
Script to generate a test Excel file with cz_binance data for testing the integrated workflow.
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

def generate_test_excel(output_path='/tmp/test_excel.xlsx', rows=1):
    """Generate a test Excel file with cz_binance data"""
    logging.info("Generating test Excel file")
    
    # Create a DataFrame with cz_binance data
    data = {
        'Twitter url': ['https://twitter.com/cz_binance'],
        'first category': ['KOL'],
        'second_category': ['-'],
        'bio': ['Founder of Binance, crypto exchange leader'],
        'lore': ['Born in China, started crypto in 2013, founded Binance in 2017'],
        'knowledge': ['Crypto Trading: Expert in exchange ops. Markets: Analyzes BTC trends. Regulation: Addresses policy'],
        'postExamples': ['"Bitcoin is controlled by math" 2025/2/20 "BNB adoption grows" 2025/1/15 "Crypto needs clarity" 2024/12/10 "Stay safe in trading" 2024/11/5'],
        'topics': ['Crypto Exchanges: Runs Binance. Market Trends: Tracks BTC. Regulation: Discusses rules'],
        'style_all': ['Bold: Confident market takes. Analytical: Ties to trends. Direct: Clear, no-nonsense tone'],
        'style_chat': ['Concise: Brief replies. Confident: Firm stance. Supportive: Helps community'],
        'style_post': ['Concise: Sharp posts. Bold: Strong statements. Informative: Shares updates'],
        'adjectives': ['Bold, Analytical, Direct']
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    
    logging.info(f"Generated test Excel file at {output_path}")
    print(f"Generated test Excel file at {output_path}")
    return output_path

def main():
    """Main function to parse arguments and generate Excel file"""
    parser = argparse.ArgumentParser(description="Generate a test Excel file with Twitter profile data")
    parser.add_argument("--output", default="/tmp/test_excel.xlsx", help="Path to save the Excel file")
    parser.add_argument("--rows", type=int, default=1, help="Number of rows to generate (currently only supports 1)")
    parser.add_argument("--use-x-domain", action="store_true", help="Use x.com domain instead of twitter.com")
    
    args = parser.parse_args()
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    # Generate the Excel file at the specified path
    output_path = generate_test_excel(args.output, args.rows)
    
    # Modify URL based on domain preference
    if args.use_x_domain:
        try:
            # Replace twitter.com with x.com in the Excel file
            df = pd.read_excel(output_path)
            df['Twitter url'] = df['Twitter url'].str.replace('twitter.com', 'x.com')
            df.to_excel(output_path, index=False)
            logging.info(f"Updated URLs to use x.com domain in {output_path}")
            print(f"Updated URLs to use x.com domain in {output_path}")
        except Exception as e:
            logging.error(f"Error updating URLs to x.com domain: {str(e)}")
            print(f"Error updating URLs to x.com domain: {str(e)}")
    
    # Verify the file was created
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"File created successfully at {output_path} (size: {file_size} bytes)")
    else:
        print(f"ERROR: Failed to create file at {output_path}")

if __name__ == "__main__":
    main()
