#!/usr/bin/env python3
"""
Script to create a test Excel file with cz_binance data and process it.
This script demonstrates the complete workflow from Excel creation to database storage.
"""

import os
import sys
import logging
import sqlite3
import pandas as pd
import tempfile
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_excel():
    """Create a test Excel file with cz_binance data"""
    logging.info("Creating test Excel file with cz_binance data")
    
    # Create a DataFrame with cz_binance data
    data = {
        'Twitter url': ['https://twitter.com/cz_binance'],
        'first category': ['KOL'],
        'second_category': ['-'],
        'bio': ['Binance创始人赵长鹏'],
        'lore': ['Active in crypto since 2017, known for founding Binance'],
        'knowledge': ['Crypto Trading: Expert in blockchain and exchanges'],
        'postExamples': ['BTC testing 70K resistance'],
        'topics': ['Crypto Trading: Shares insights on market trends'],
        'style_all': ['Analytical: Focuses on data and trends'],
        'style_chat': ['Concise: Short, informative replies'],
        'style_post': ['Brief: Quick market updates'],
        'adjectives': ['Analytical, Precise, Practical']
    }
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(data)
    
    # Create a temporary file for the Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
        excel_path = temp_file.name
    
    df.to_excel(excel_path, index=False)
    
    logging.info(f"Created test Excel file at {excel_path}")
    return excel_path

def process_excel_file(excel_path, db_path):
    """Process an Excel file with KOL character data"""
    logging.info(f"Processing Excel file: {excel_path}")
    
    try:
        # Import the process_excel_with_profile function
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
        from process_excel_with_profile import process_excel_file as process_excel
        
        # Process the Excel file
        process_excel(excel_path, db_path)
        
        logging.info(f"Processed Excel file: {excel_path}")
        return True
    except Exception as e:
        logging.error(f"Error processing Excel file: {str(e)}")
        return False

def display_results(db_path, handle):
    """Display the results of Excel processing for a specific handle"""
    logging.info(f"Displaying results for handle: {handle}")
    
    try:
        # Import the display_url_tracking_record function
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
        from display_url_tracking_record import display_joined_record
        
        # Display the results
        display_joined_record(db_path, handle)
        
        return True
    except Exception as e:
        logging.error(f"Error displaying results: {str(e)}")
        return False

def main():
    """Main function"""
    # Set the database path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/local_database.db'))
    
    # Set the handle to check
    handle = 'cz_binance'
    
    # Create a test Excel file
    excel_path = create_test_excel()
    
    # Process the Excel file
    if not process_excel_file(excel_path, db_path):
        logging.error("Failed to process Excel file, exiting")
        return 1
    
    # Display results
    if not display_results(db_path, handle):
        logging.error("Failed to display results, exiting")
        return 1
    
    # Clean up
    if os.path.exists(excel_path):
        os.remove(excel_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
