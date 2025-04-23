"""
Data handling utility for scrapers.
Provides functions to save data to Excel and other formats.
"""
import os
import pandas as pd
from datetime import datetime

from src.scrapers.core.logger import get_logger

logger = get_logger(__name__)

def save_to_excel(data, output_file=None, output_dir=None, prefix='results', sheet_name='Sheet1'):
    """
    Save data to Excel file.
    
    Args:
        data (dict): Dictionary containing data to save
        output_file (str): Output file path (optional)
        output_dir (str): Output directory (optional)
        prefix (str): Prefix for output filename
        sheet_name (str): Sheet name
        
    Returns:
        str: Path to the saved file
    """
    try:
        if not data:
            logger.warning("No data to save")
            return None
            
        # Create dataframe from data
        df = pd.DataFrame(data)
        
        # Create output file path if not provided
        if output_file is None:
            if output_dir is None:
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'output')
                
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
            output_file = os.path.join(output_dir, f'{prefix}_{timestamp}.xlsx')
        
        # Check if file exists and append if it does
        if os.path.exists(output_file):
            with pd.ExcelWriter(output_file, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                # Get the existing sheet to determine the next row
                book = writer.book
                if sheet_name in book.sheetnames:
                    start_row = book[sheet_name].max_row
                    df.to_excel(writer, index=False, header=False, sheet_name=sheet_name, startrow=start_row)
                else:
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
        else:
            df.to_excel(output_file, index=False, sheet_name=sheet_name)
            
        logger.info(f"Data saved to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Error saving data to Excel: {e}")
        return None

def save_to_json(data, output_file=None, output_dir=None, prefix='results'):
    """
    Save data to JSON file.
    
    Args:
        data (dict or list): Data to save
        output_file (str): Output file path (optional)
        output_dir (str): Output directory (optional)
        prefix (str): Prefix for output filename
        
    Returns:
        str: Path to the saved file
    """
    try:
        # Create output file path if not provided
        if output_file is None:
            if output_dir is None:
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'output')
                
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
            output_file = os.path.join(output_dir, f'{prefix}_{timestamp}.json')
        
        # Convert DataFrame to dict if needed
        if isinstance(data, pd.DataFrame):
            data = data.to_dict(orient='records')
            
        # Save to JSON
        pd.DataFrame(data).to_json(output_file, orient='records', indent=4)
        
        logger.info(f"Data saved to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Error saving data to JSON: {e}")
        return None
