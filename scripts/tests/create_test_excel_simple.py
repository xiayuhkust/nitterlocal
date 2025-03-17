#!/usr/bin/env python3
"""
Simple script to generate a test Excel file at the exact specified path.
This script ensures the file is created at the exact path provided.
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

def main():
    """Generate a test Excel file at the specified path"""
    parser = argparse.ArgumentParser(description="Generate a test Excel file with Twitter profile data")
    parser.add_argument("--output", default="/tmp/test_excel.xlsx", help="Path to save the Excel file")
    
    args = parser.parse_args()
    output_path = args.output
    
    logging.info(f"Generating test Excel file at {output_path}")
    
    # Create a DataFrame with cz_binance data
    data = {
        'Twitter url': ['https://twitter.com/cz_binance'],
        'first category': ['KOL'],
        'second_category': ['-'],
        'bio': ['Founder of Binance, crypto exchange leader'],
        'lore': ['Born in China, started crypto in 2013, founded Binance in 2017']
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    
    logging.info(f"Successfully generated test Excel file at {output_path}")
    print(f"Successfully generated test Excel file at {output_path}")
    
    # Verify the file exists
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        logging.info(f"File size: {file_size} bytes")
        print(f"File size: {file_size} bytes")
    else:
        logging.error(f"File was not created at {output_path}")
        print(f"ERROR: File was not created at {output_path}")

if __name__ == "__main__":
    main()
