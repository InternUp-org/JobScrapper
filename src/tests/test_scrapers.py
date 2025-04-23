"""
Tests for the scraper modules.
"""
import os
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the path so we can import our modules
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.scrapers.jobright.scraper import JobRightScraper
from src.scrapers.wellfound.scraper import WellfoundScraper

class TestJobRightScraper(unittest.TestCase):
    """Test cases for the JobRight scraper."""
    
    @patch('src.scrapers.jobright.scraper.start_browser')
    def test_start(self, mock_start_browser):
        """Test browser initialization."""
        # Setup mock
        mock_driver = MagicMock()
        mock_start_browser.return_value = mock_driver
        
        # Test scraper start
        scraper = JobRightScraper(headless=True)
        result = scraper.start()
        
        # Verify results
        self.assertTrue(result)
        mock_start_browser.assert_called_once_with(headless=True, enable_performance_logging=True)
        self.assertEqual(scraper.driver, mock_driver)
    
    @patch('src.scrapers.jobright.scraper.stop_browser')
    def test_stop(self, mock_stop_browser):
        """Test browser cleanup."""
        # Setup mock and scraper
        scraper = JobRightScraper()
        scraper.driver = MagicMock()
        
        # Test stop
        scraper.stop()
        
        # Verify results
        mock_stop_browser.assert_called_once_with(scraper.driver)
        self.assertIsNone(scraper.driver)
    
    @patch('src.scrapers.jobright.scraper.config')
    @patch('src.scrapers.jobright.scraper.start_browser')
    @patch('src.scrapers.jobright.scraper.WebDriverWait')
    def test_login(self, mock_wait, mock_start_browser, mock_config):
        """Test login functionality."""
        # Mock configuration
        mock_config.get_credentials.return_value = {'username': 'test_user', 'password': 'test_pass'}
        mock_config.get_setting.return_value = 'https://app.jobright.ai/login'
        
        # Mock driver and elements
        mock_driver = MagicMock()
        mock_start_browser.return_value = mock_driver
        
        # Create scraper and mock start
        scraper = JobRightScraper()
        scraper.driver = mock_driver
        
        # Test login
        result = scraper.login()
        
        # Verify driver calls
        mock_driver.get.assert_called_once()
        mock_driver.find_element.assert_called()
        
        # This test is rudimentary since we can't fully mock browser interactions
        # In a more advanced test, we would mock more of the selenium interactions


class TestWellfoundScraper(unittest.TestCase):
    """Test cases for the Wellfound scraper."""
    
    @patch('src.scrapers.wellfound.scraper.start_browser')
    @patch('src.scrapers.wellfound.scraper.subprocess.Popen')
    def test_start_with_proxy(self, mock_popen, mock_start_browser):
        """Test starting the scraper with proxy."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_start_browser.return_value = mock_driver
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        # Create scraper with proxy enabled
        scraper = WellfoundScraper(headless=True, use_proxy=True)
        
        # Override monitor_thread to prevent threading issues in tests
        scraper.monitor_thread = MagicMock()
        
        # Test start
        result = scraper.start()
        
        # Verify results
        self.assertTrue(result)
        mock_popen.assert_called_once()
        mock_start_browser.assert_called_once_with(headless=True, proxy='localhost:8080')
        self.assertEqual(scraper.driver, mock_driver)
        self.assertEqual(scraper.proxy_process, mock_process)
    
    @patch('src.scrapers.wellfound.scraper.start_browser')
    def test_start_without_proxy(self, mock_start_browser):
        """Test starting the scraper without proxy."""
        # Setup mock
        mock_driver = MagicMock()
        mock_start_browser.return_value = mock_driver
        
        # Create scraper with proxy disabled
        scraper = WellfoundScraper(headless=True, use_proxy=False)
        
        # Test start
        result = scraper.start()
        
        # Verify results
        self.assertTrue(result)
        mock_start_browser.assert_called_once_with(headless=True, proxy=None)
        self.assertEqual(scraper.driver, mock_driver)
        self.assertIsNone(scraper.proxy_process)
    
    @patch('src.scrapers.wellfound.scraper.stop_browser')
    def test_stop(self, mock_stop_browser):
        """Test stopping the scraper."""
        # Setup scraper with mocked components
        scraper = WellfoundScraper()
        scraper.driver = MagicMock()
        scraper.proxy_process = MagicMock()
        scraper.stop_event = MagicMock()
        scraper.monitor_thread = MagicMock()
        
        # Test stop
        scraper.stop()
        
        # Verify results
        mock_stop_browser.assert_called_once_with(scraper.driver)
        scraper.stop_event.set.assert_called_once()
        scraper.proxy_process.send_signal.assert_called_once()
        scraper.monitor_thread.join.assert_called_once()

    def test_get_results(self):
        """Test processing of startup results."""
        # Create test data
        mock_data = [
            {
                'node': {
                    '__typename': 'PromotedResult',
                    'promotedStartup': {
                        'startupId': '123',
                        'name': 'Test Startup 1'
                    }
                }
            },
            {
                'node': {
                    '__typename': 'StartupResult',
                    'startupId': '456',
                    'name': 'Test Startup 2'
                }
            }
        ]
        
        # Create scraper and test function
        scraper = WellfoundScraper()
        scraper.get_results(mock_data)
        
        # Verify results
        self.assertEqual(len(scraper.all_startups), 2)
        self.assertIn('123', scraper.all_startups)
        self.assertIn('456', scraper.all_startups)
        self.assertEqual(scraper.all_startups['123']['name'], 'Test Startup 1')


if __name__ == '__main__':
    unittest.main()
