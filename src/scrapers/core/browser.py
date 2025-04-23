"""
Browser management utility for scapers.
Provides functions to start and stop browsers with proper configuration.
"""
import os
import sys
import logging
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import OperationSystemManager, ChromeType

from src.scrapers.core.logger import get_logger

logger = get_logger(__name__)

def start_browser(headless=False, proxy=None, user_data_dir=None, enable_performance_logging=True):
    """
    Start and configure a browser instance with appropriate options.
    
    Args:
        headless (bool): Run in headless mode
        proxy (str): Proxy server to use (format: "host:port")
        user_data_dir (str): Path to Chrome user data directory
        enable_performance_logging (bool): Enable performance logging
        
    Returns:
        WebDriver: Configured browser instance
    """
    try:
        chrome_options = uc.ChromeOptions()
        
        if user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
            
        if headless:
            chrome_options.add_argument('--headless')
            
        if enable_performance_logging:
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
        capabilities = DesiredCapabilities.CHROME
        if enable_performance_logging:
            capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
        
        # Check if we're running in WSL or Linux
        is_wsl = 'WSL' in os.uname().release if hasattr(os, 'uname') else False
        is_linux = sys.platform.startswith('linux')
        
        if is_wsl or is_linux:
            logger.info('Running in WSL/Linux environment - setting up Chrome accordingly')
            # For Linux/WSL environments, we need to specify the Chrome binary location
            chrome_paths = [
                '/usr/bin/google-chrome-stable',  # Ubuntu/Debian
                '/usr/bin/google-chrome',        # Alternative
                '/usr/bin/chromium-browser',     # Chromium alternative
            ]
            
            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    break
                    
            if chrome_binary:
                logger.info(f'Found Chrome binary at: {chrome_binary}')
                chrome_options.binary_location = chrome_binary
            else:
                logger.warning('Chrome binary not found in common locations. You may need to install Chrome.')
                
            try:
                # Try with undetected_chromedriver
                driver = uc.Chrome(options=chrome_options, desired_capabilities=capabilities)
            except Exception as inner_e:
                logger.warning(f'Failed to initialize undetected_chromedriver: {inner_e}')
                logger.info('Trying alternative approach with regular selenium...')
                
                # Alternative approach with regular selenium
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Windows environment - proceed with version detection
            browser_version = OperationSystemManager().get_browser_version_from_os(ChromeType.GOOGLE)
            if browser_version is None:
                # If browser version can't be detected, use a default version or None
                logger.warning('Unable to detect Chrome browser version. Using default settings.')
                driver = uc.Chrome(options=chrome_options, desired_capabilities=capabilities)
            else:
                version_main = int(browser_version.split('.')[0])
                driver = uc.Chrome(options=chrome_options, desired_capabilities=capabilities, version_main=version_main)
        
        logger.info('Browser successfully started')
        return driver
        
    except Exception as e:
        logger.error(f'Cannot start browser, error: {e}')
        raise

def stop_browser(driver):
    """
    Safely close the browser.
    
    Args:
        driver (WebDriver): Browser instance to close
    """
    try:
        if driver:
            driver.quit()
            logger.info("Browser closed successfully")
    except Exception as e:
        logger.warning(f"Error closing browser: {e}")
