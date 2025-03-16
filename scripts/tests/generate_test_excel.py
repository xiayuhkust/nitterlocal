#!/usr/bin/env python3
"""
Script to generate a test Excel file with cz_binance data for testing the integrated workflow.
"""

import os
import sys
import logging
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def generate_test_excel():
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
    output_path = '/tmp/test_profile_workflow.xlsx'
    df.to_excel(output_path, index=False)
    
    logging.info(f"Generated test Excel file at {output_path}")
    print(f"Generated test Excel file at {output_path}")
    return output_path

if __name__ == "__main__":
    generate_test_excel()
