"""
JobRight scraper implementation.
"""
import json
import logging
import os
import sys
import time
import pandas as pd
import undetected_chromedriver as uc

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import OperationSystemManager,ChromeType

# Setup path for importing project modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

# Paths and constants
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'jobright_logs.log')
OUTPUT_FILE = os.path.join(project_root, 'output', f'jobright_results_{datetime.now().strftime("%Y-%m-%d-%H-%M")}.xlsx')
CREDENTIALS_FILE = os.path.join(project_root, 'config', 'credentials.json')

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ] 
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_creds():
    """
    Get credentials from credentials file.
    
    Returns:
        dict: Dictionary with login credentials
    """
    try:
        # Try to load from config.json first (new structure)
        if os.path.exists(CREDENTIALS_FILE):
            try:
                import json
                with open(CREDENTIALS_FILE, 'r') as file:
                    config_data = json.load(file)
                    if 'jobright' in config_data:
                        return config_data['jobright']
            except Exception as e:
                logger.error(f'Cannot load credentials from {CREDENTIALS_FILE}: {e}')
        
        # Fallback to legacy credentials.txt in project root
        legacy_creds_file = os.path.join(project_root, 'credentials.txt')
        if os.path.exists(legacy_creds_file):
            credentials = {}
            with open(legacy_creds_file, 'r') as file:
                for line in file:
                    key, value = line.strip().split('=')
                    credentials[key] = value
            return credentials
            
        logger.error(f'Cannot find credentials file')
        sys.exit()
    except Exception as e:
        logger.error(f'Cannot get credentials, error: {e}')
        sys.exit()

def start_browser():
    """
    Start and configure Chrome browser.
    
    Returns:
        WebDriver: Configured Chrome browser instance
    """
    try:
        chrome_options = uc.ChromeOptions()
        #chrome_options.add_argument(f"--user-data-dir=/Users/max/wk/jobright/tst_profile")
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        capabilities = DesiredCapabilities.CHROME
        capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
        
        # Check if we're running in WSL or Linux
        is_wsl = 'WSL' in os.uname().release if hasattr(os, 'uname') else False
        is_linux = sys.platform.startswith('linux')
        
        # For cloud deployment, you might want to run in headless mode
        # Uncomment the line below for headless mode on cloud deployment
        # chrome_options.add_argument('--headless')
        
        if is_wsl or is_linux:
            logger.info('Running in WSL/Linux environment - setting up Chrome accordingly')
            # For Linux/WSL environments, we need to specify the Chrome binary location
            # Check if Chrome is installed and use the appropriate path
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
        logger.info('Browser sucessfully started')
        return driver
    except Exception as e:
        logger.error(f'Cannot start browser, error: {e}')
        sys.exit()

def stop_browser(driver):
    """
    Stop the browser.
    
    Args:
        driver: WebDriver instance to stop
    """
    try:
        driver.quit()
    except Exception as e:
        pass
    
def check_popups(driver):
    """
    Check for popups and close them.
    
    Args:
        driver: WebDriver instance
    """
    time.sleep(5)
    popup_close_buttons = driver.find_elements(By.XPATH, '//button[@aria-label="Close"]')
    if popup_close_buttons:
        logger.info('Popup was found, trying to cloae it...')
        try:
            popup_close_buttons[0].click()
        except:
            pass
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except:
            pass

def save_result(data):
    """
    Save data to Excel file.
    
    Args:
        data: Dictionary of job data to save
    """
    try:
        df = pd.DataFrame(data)
        if os.path.exists(OUTPUT_FILE):
            with pd.ExcelWriter(OUTPUT_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                df.to_excel(writer, index=False, header=False, sheet_name='Sheet1', startrow=writer.sheets['Sheet1'].max_row)
        else:
            df.to_excel(OUTPUT_FILE, index=False, sheet_name='Sheet1')
    except Exception as e:
        logger.error(f'Something went wrond during writing to file, error: {e}')

def capture_responses(driver):
    """
    Capture job data from network responses.
    
    Args:
        driver: WebDriver instance
    """
    for n in range(1,6):
        try:
            time.sleep(5)
            responses = {}
            for entry in driver.get_log('performance'):
                message = json.loads(entry['message'])['message']
                if message['method'] == 'Network.responseReceived':
                    request_id = message['params']['requestId']
                    url = message['params']['response']['url']
                    if '/list/jobs' in url:
                        logger.info(f'Collecting data from {url} ...')
                        responses[request_id] = {"url": url}

                        response_body = driver.execute_cdp_cmd(
                            "Network.getResponseBody", {"requestId": request_id}
                        )
                        responses[request_id]["body"] = response_body.get("body", "")
                        #print(len(json.loads(responses[request_id]['body'])['result']['jobList']))
                        #print(json.loads(responses[request_id]['body'])['result'].keys())

                        for ii in json.loads(responses[request_id]['body'])['result']['jobList']:
                            #print(ii)
                            #print(ii.keys())
                            
                            job_set = ii['jobResult']
                            
                            #print(job_set)
                            #print(job_set.keys())
                            try:
                                data = {
                                    'Apply now': [job_set.get('applyLink', '')],
                                    'Company name': [ii['companyResult'].get('companyName', '')],
                                    'Published time': [job_set.get('publishTimeDesc', '')],
                                    'Title': [job_set.get('jobTitle', '')],
                                    'Type': [job_set.get('employmentType', '')],
                                    'Remote': [job_set.get('workModel', '')],
                                    'Seniority': [job_set.get('jobSeniority', '')],
                                    'Salary': [job_set.get('salaryDesc', '')],
                                    'Description': [job_set.get('jobSummary', '')],
                                    'Inustry': [';'.join([x.get('displayName', '') for x in job_set['industryMatchingScores'][:2]])],
                                    'Tags': [';'.join(job_set.get('recommendationTags', ''))],
                                    'Responsibilities': [';'.join(job_set.get('coreResponsibilities', ''))],
                                    'Responsibilities': [';'.join(job_set.get('coreRessource venv/bin/activateponsibilities', ''))],
                                    'Connection name': [job_set['socialConnections'][0].get('fullName', '') if job_set['socialConnections'] else ''],
                                    'Connection company name': [job_set['socialConnections'][0].get('companyName', '') if job_set['socialConnections'] else ''],
                                    'Connection job title': [job_set['socialConnections'][0].get('jobTitle', '') if job_set['socialConnections'] else ''],
                                    'Connection linkedin url': [job_set['socialConnections'][0].get('linkedinUrl', '') if job_set['socialConnections'] else ''],
                                    }
                                save_result(data)
                            except Exception as e:
                                logger.error(f'Something went wrong during collecting job data: {e}')
            return True
        except Exception as e:
            logger.error(f'Something went wrong during capturing responses: {e}')
            return False
    
def collect_data():
    """
    Main function to execute the scraping process.
    """
    try:
        # Get credentials
        credentials = get_creds()
        
        # Start the browser
        driver = start_browser()
        
        try:
            # Attempt login
            driver.get('https://app.jobright.ai/user/login')
            
            # Wait for login form
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            
            # Enter credentials
            driver.find_element(By.ID, "email").send_keys(credentials.get('username', credentials.get('login', '')))
            driver.find_element(By.ID, "password").send_keys(credentials.get('password', credentials.get('pass', '')))
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            
            # Wait for successful login
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='dashboard-content']"))
            )
            
            logger.info('Login successful')
            
            # Check for popups
            check_popups(driver)
            
            # Navigate to jobs page
            driver.get('https://app.jobright.ai/jobs')
            time.sleep(5)
            
            # Capture job data
            capture_responses(driver)
            
            logger.info('Scraping completed successfully')
            return True
            
        except Exception as e:
            logger.error(f'Error during scraping: {e}')
            return False
            
        finally:
            # Close the browser
            stop_browser(driver)
            
    except Exception as e:
        logger.error(f'Error in collect_data: {e}')
        return False


def run_jobright_scraper(headless=False, output_file=None):
    """
    Run the JobRight scraper.
    
    Args:
        headless (bool): Run in headless mode (ignored in original implementation)
        output_file (str): Custom output file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    global OUTPUT_FILE
    
    if output_file:
        OUTPUT_FILE = output_file
        
    logger.info("Starting JobRight scraper...")
    
    # Run the scraper
    success = collect_data()
    
    if success:
        logger.info("JobRight scraper completed successfully")
    else:
        logger.error("JobRight scraper failed")
        
    return success


# Execute scraper when run directly
if __name__ == "__main__":
    collect_data()
