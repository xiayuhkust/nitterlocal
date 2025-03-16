#!/usr/bin/env python3
"""
Test script to verify the integrated Excel processing workflow using both scraper and profile methods.
"""

import os
import sys
import logging
import pandas as pd
import tempfile
import subprocess

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_test_excel():
    """Create a test Excel file with cz_binance data"""
    logging.info("Creating test Excel file")
    
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
    output_path = '/tmp/test_integrated_workflow.xlsx'
    df.to_excel(output_path, index=False)
    
    logging.info(f"Created test Excel file at {output_path}")
    return output_path

def test_integrated_workflow():
    """Test the integrated Excel processing workflow"""
    try:
        # Create a test Excel file
        excel_path = create_test_excel()
        
        # Create a temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        logging.info(f"Created temporary database at {db_path}")
        
        # Process the Excel file using the integrated script
        logging.info("Processing Excel file using integrated script")
        process_result = subprocess.run([
            'python3', '/home/ubuntu/nitterlocal/scripts/database/process_excel_with_profile.py',
            '--excel', excel_path,
            '--db-path', db_path,
            '--display', 'cz_binance'
        ], check=True, capture_output=True, text=True)
        
        # Print the output
        print("\n--- Process Output ---")
        print(process_result.stdout)
        
        # Directly display the results using the display_results function
        print("\n--- Direct Database Query Results ---")
        try:
            # Import the display_results function from the process_excel_with_profile script
            sys.path.append('/home/ubuntu/nitterlocal/scripts/database')
            from process_excel_with_profile import display_results
            
            # Display results for cz_binance
            display_results(db_path, 'cz_binance')
        except Exception as e:
            logging.error(f"Error displaying results directly: {str(e)}")
        
        # Clean up
        if os.path.exists(excel_path):
            os.remove(excel_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        
        logging.info("Test completed successfully")
        return True
    except Exception as e:
        logging.error(f"Error in test: {str(e)}")
        return False

if __name__ == "__main__":
    test_integrated_workflow()
