"""
Tests for the configuration module.
"""
import os
import unittest
import tempfile
import json
import shutil
from pathlib import Path

# Add the project root to the path so we can import our modules
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.config.config import Config

class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""
    
    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, 'config')
        os.makedirs(self.config_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_config_initialization(self):
        """Test that Config initializes with default values."""
        config = Config(self.config_dir)
        
        # Check that config files were created
        self.assertTrue(os.path.exists(os.path.join(self.config_dir, 'config.ini')))
        self.assertTrue(os.path.exists(os.path.join(self.config_dir, 'credentials.json')))
    
    def test_get_setting(self):
        """Test getting settings from config."""
        # Create a config object with our test dir
        config = Config(self.config_dir)
        
        # Check a default setting
        headless = config.get_setting('general', 'headless', 'default')
        self.assertEqual(headless, 'false')
        
        # Check a non-existent setting with default
        test_value = config.get_setting('nonexistent', 'nonexistent', 'default_value')
        self.assertEqual(test_value, 'default_value')
    
    def test_get_credentials(self):
        """Test getting credentials."""
        # Create credentials file
        credentials = {
            'jobright': {
                'username': 'test_user',
                'password': 'test_pass'
            },
            'wellfound': {
                'username': 'wellfound_user',
                'password': 'wellfound_pass'
            }
        }
        
        with open(os.path.join(self.config_dir, 'credentials.json'), 'w') as f:
            json.dump(credentials, f)
        
        # Create config and test
        config = Config(self.config_dir)
        jobright_creds = config.get_credentials('jobright')
        
        self.assertEqual(jobright_creds['username'], 'test_user')
        self.assertEqual(jobright_creds['password'], 'test_pass')
    
    def test_save_credentials(self):
        """Test saving credentials."""
        config = Config(self.config_dir)
        
        # Save new credentials
        config.save_credentials('test_scraper', 'new_user', 'new_pass')
        
        # Verify they were saved
        saved_creds = config.get_credentials('test_scraper')
        self.assertEqual(saved_creds['username'], 'new_user')
        self.assertEqual(saved_creds['password'], 'new_pass')
        
        # Verify file was updated
        with open(os.path.join(self.config_dir, 'credentials.json'), 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['test_scraper']['username'], 'new_user')
        self.assertEqual(saved_data['test_scraper']['password'], 'new_pass')

if __name__ == '__main__':
    unittest.main()
