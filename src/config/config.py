"""
Configuration management for the job scrapers.
Loads and provides access to configuration settings.
"""
import os
import json
import configparser
from pathlib import Path

class Config:
    """Configuration manager for job scrapers."""
    
    def __init__(self, config_dir=None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir (str): Path to configuration directory
        """
        # Set config directory
        if config_dir is None:
            # Default to config directory in project root
            self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
        else:
            self.config_dir = config_dir
            
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # Default paths for configuration files
        self.config_file = os.path.join(self.config_dir, 'config.ini')
        self.credentials_file = os.path.join(self.config_dir, 'credentials.json')
        
        # Initialize configuration containers
        self.settings = {}
        self.credentials = {}
        
        # Load configurations
        self._load_settings()
        self._load_credentials()
    
    def _load_settings(self):
        """Load settings from config.ini file."""
        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            # Convert config to dictionary
            for section in config.sections():
                self.settings[section] = {}
                for key, value in config[section].items():
                    self.settings[section][key] = value
        else:
            # Create default configuration
            self._create_default_settings()
    
    def _create_default_settings(self):
        """Create default settings file."""
        config = configparser.ConfigParser()
        
        # General settings
        config['general'] = {
            'headless': 'false',
            'output_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output'),
            'log_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        }
        
        # JobRight settings
        config['jobright'] = {
            'enable': 'true',
            'login_url': 'https://app.jobright.ai/user/login'
        }
        
        # Wellfound settings
        config['wellfound'] = {
            'enable': 'true',
            'login_url': 'https://wellfound.com/login',
            'proxy': 'localhost:8080'
        }
        
        # Write configuration to file
        with open(self.config_file, 'w') as f:
            config.write(f)
            
        # Load the created settings
        self._load_settings()
    
    def _load_credentials(self):
        """Load credentials from credentials.json file."""
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'r') as f:
                self.credentials = json.load(f)
        else:
            # Create default credentials file
            self._create_default_credentials()
    
    def _create_default_credentials(self):
        """Create default credentials file."""
        # Check if legacy credentials files exist
        legacy_jobright_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'credentials.txt')
        legacy_wellfound_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'wellfound_files', 'wellfound_credentials.txt')
        
        credentials = {
            'jobright': {
                'username': 'dizzlay@gmail.com',
                'password': 'Miqry1-zepwac-gekgar'
            },
            'wellfound': {
                'username': 'dizzlay@gmail.com',
                'password': 'Miqry1-zepwac-gekgar'
            }
        }
        
        # Try to import from legacy credentials files
        if os.path.exists(legacy_jobright_file):
            try:
                with open(legacy_jobright_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            if key in ['username', 'login']:
                                credentials['jobright']['username'] = value
                            elif key in ['password', 'pass']:
                                credentials['jobright']['password'] = value
            except Exception as e:
                print(f"Error loading legacy JobRight credentials: {e}")
        
        if os.path.exists(legacy_wellfound_file):
            try:
                with open(legacy_wellfound_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            if key in ['username', 'login']:
                                credentials['wellfound']['username'] = value
                            elif key in ['password', 'pass']:
                                credentials['wellfound']['password'] = value
            except Exception as e:
                print(f"Error loading legacy Wellfound credentials: {e}")
        
        # Write credentials to file
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)
            
        # Load the created credentials
        self._load_credentials()
    
    def get_setting(self, section, key, default=None):
        """
        Get a setting value.
        
        Args:
            section (str): Configuration section
            key (str): Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        if section in self.settings and key in self.settings[section]:
            return self.settings[section][key]
        return default
    
    def get_credentials(self, scraper):
        """
        Get credentials for a specific scraper.
        
        Args:
            scraper (str): Scraper name (e.g., 'jobright', 'wellfound')
            
        Returns:
            dict: Dictionary containing username and password
        """
        if scraper in self.credentials:
            return self.credentials[scraper]
        return {'username': '', 'password': ''}
    
    def save_credentials(self, scraper, username, password):
        """
        Save credentials for a specific scraper.
        
        Args:
            scraper (str): Scraper name
            username (str): Username or email
            password (str): Password
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if scraper not in self.credentials:
                self.credentials[scraper] = {}
                
            self.credentials[scraper]['username'] = username
            self.credentials[scraper]['password'] = password
            
            # Save to file
            with open(self.credentials_file, 'w') as f:
                json.dump(self.credentials, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False

# Create a singleton instance
config = Config()
