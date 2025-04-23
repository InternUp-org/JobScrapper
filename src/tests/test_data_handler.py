"""
Tests for the data handler module.
"""
import os
import unittest
import tempfile
import pandas as pd
import shutil

# Add the project root to the path so we can import our modules
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.scrapers.core.data_handler import save_to_excel, save_to_json

class TestDataHandler(unittest.TestCase):
    """Test cases for the data handler functions."""
    
    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_to_excel(self):
        """Test saving data to Excel."""
        # Create test data
        data = {
            'Title': ['Job 1', 'Job 2'],
            'Company': ['Company 1', 'Company 2'],
            'Salary': ['$100,000', '$120,000']
        }
        
        # Save to Excel
        output_file = os.path.join(self.output_dir, 'test_excel.xlsx')
        result = save_to_excel(data, output_file=output_file)
        
        # Verify result
        self.assertEqual(result, output_file)
        self.assertTrue(os.path.exists(output_file))
        
        # Verify content
        df = pd.read_excel(output_file)
        self.assertEqual(len(df), 2)
        self.assertEqual(df['Title'][0], 'Job 1')
        self.assertEqual(df['Company'][1], 'Company 2')
    
    def test_append_to_excel(self):
        """Test appending data to an existing Excel file."""
        # Create initial data
        data1 = {
            'Title': ['Job 1'],
            'Company': ['Company 1'],
            'Salary': ['$100,000']
        }
        
        # Create additional data
        data2 = {
            'Title': ['Job 2'],
            'Company': ['Company 2'],
            'Salary': ['$120,000']
        }
        
        # Save initial data
        output_file = os.path.join(self.output_dir, 'test_append.xlsx')
        save_to_excel(data1, output_file=output_file)
        
        # Append additional data
        save_to_excel(data2, output_file=output_file)
        
        # Verify content
        df = pd.read_excel(output_file)
        self.assertEqual(len(df), 2)
        self.assertEqual(df['Title'][0], 'Job 1')
        self.assertEqual(df['Title'][1], 'Job 2')
    
    def test_save_to_json(self):
        """Test saving data to JSON."""
        # Create test data
        data = {
            'Title': ['Job 1', 'Job 2'],
            'Company': ['Company 1', 'Company 2'],
            'Salary': ['$100,000', '$120,000']
        }
        
        # Save to JSON
        output_file = os.path.join(self.output_dir, 'test_json.json')
        result = save_to_json(data, output_file=output_file)
        
        # Verify result
        self.assertEqual(result, output_file)
        self.assertTrue(os.path.exists(output_file))
        
        # Verify content
        df = pd.read_json(output_file)
        self.assertEqual(len(df), 2)
        self.assertTrue('Title' in df.columns)
        self.assertTrue('Company' in df.columns)

if __name__ == '__main__':
    unittest.main()
