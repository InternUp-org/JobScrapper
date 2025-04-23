"""
Wellfound scraper implementation.
"""
import json
import logging
import os
import sys
import time
import pandas as pd
import undetected_chromedriver as uc
import subprocess
import threading
import random
import signal
from datetime import datetime
from botasaurus.browser import browser, Driver
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import OperationSystemManager,ChromeType

# Setup path for importing project modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

# Configure Django settings if available
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobs_scraper.settings')
    import django
    django.setup()
    from jobs.models import WellfoundCredential
    credentials = WellfoundCredential.objects.last()
    if credentials:
        username = credentials.username
        password = credentials.password
except:
    # Fall back to config if Django not available
    from src.config.config import config
    credentials = config.get_credentials('wellfound')
    username = credentials.get('username', '')
    password = credentials.get('password', '')

# Try to initialize display for headless environments
try:
    display = Display(visible=0, size=(1920, 1080), use_xauth=True)
    display.start()
    import pyautogui
except:
    pass

# Paths and constants
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data.json')
PROXY = "localhost:8080"
ADDON_SCRIPT = os.path.join(BASE_DIR, "mitmproxy_addon.py")
LOG_FILE = os.path.join(BASE_DIR, 'wellfound_logs.log')

# Default to output in project root if custom path not available
try:
    OUTPUT_FILE = os.path.join('/home/jobs_scraper/jobs/jobs_scraper_results', 
                              f'wellfound_results_{username.split("@")[0]}_{datetime.now().strftime("%Y-%m-%d-%H-%M")}.xlsx')
except:
    OUTPUT_FILE = os.path.join(project_root, 'output', 
                              f'wellfound_results_test_{datetime.now().strftime("%Y-%m-%d-%H-%M")}.xlsx')

CREDENTIALS_FILE = os.path.join(BASE_DIR, 'wellfound_credentials.txt')

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

# Global data containers
all_statups = {}
all_statups_pages = {}
all_extended_statups_pages = {}

def delay_range():
    """Return a random delay in seconds."""
    return random.randint(5, 7)

def random_click(image_path, confidence=0.8):
    """Perform a random click near the center of an image match."""
    try:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location:
            offset = int(location.width * 0.1)
            center_x, center_y = pyautogui.center(location)
            random_x = center_x + random.randint(-offset, offset)
            random_y = center_y + random.randint(-offset, offset)
            pyautogui.moveTo(random_x, random_y, duration=random.uniform(0.1, 1.0))
            pyautogui.click()
        else:
            logger.info("Image not found.")
    except Exception as e:
        logger.info(f"Error during random click: {e}")
    
@browser(proxy=f"http://{PROXY}", add_arguments=['--no-sandbox', '--ignore-certificate-errors'])
def scrape_heading_task(driver: Driver, data):
    """
    Main scraping function using botasaurus browser.
    """
    try:        
        driver.get("https://wellfound.com/login")
        time.sleep(10)
        try:
            driver.save_screenshot('check_1111.png')
        except:
            driver.save_screenshot()
            pass
        
        image_path = "11zon_cropped.png"
        try:
            random_click(image_path, confidence=0.8)
        except Exception as e:
            logger.info(e)
        time.sleep(15)
        
        # Login sequence
        driver.type("input[id='user_email']", username)
        time.sleep(delay_range())
        driver.type("input[id='user_password']", password)
        time.sleep(delay_range())
        driver.click("input[type='submit']")
        time.sleep(delay_range())
        
        # Scroll and collect data
        counter = 0
        for _ in range(105):
            driver.scroll_to_bottom()
            time.sleep(10)
            if len(all_statups) == counter:
                break
            counter = len(all_statups)
            
        # Click on detail arrows
        details_arrows = driver.select_all('div[class="flex w-full"]')
        time.sleep(delay_range())
        for arrow in details_arrows:
            arrow.click()
            time.sleep(delay_range())
            driver.click("button[data-test='closeButton']")
            time.sleep(delay_range())

        # Process collected data
        for k, v in all_statups.items():
            try:
                for entry in all_statups[k]["highlightedJobListings"]:
                    try:
                        data = {
                            'Company name': [all_statups[k]["name"]],
                            'Actively hiring': [''.join([x["label"] for x in all_extended_statups_pages[k]["badges"] if x.get("name", '') == 'ACTIVELY_HIRING_BADGE'])],
                            'Description': [all_statups[k]["highConcept"]],
                            'Company size': [all_statups[k]["companySize"].split('SIZE_')[-1].replace('_', '-')],
                            'Badges': [','.join([x["label"] for x in all_extended_statups_pages[k]["badges"]])],
                            'Title': [entry['title']],
                            'Location': [','.join(entry['locationNames'])],
                            'Remote options': entry['remoteConfig']['kind'].lower(),
                            'Remote': ['Yes' if entry['remote'] == True else ''],
                            'Salary': [entry['compensation']],
                            'Published time': [datetime.utcfromtimestamp(int(entry['liveStartAt'])).strftime('%Y-%m-%d %H:%M:%S')],
                            'Website': [all_extended_statups_pages[k]['companyUrl']],
                            'Linkedin': [all_extended_statups_pages[k]['linkedInUrl']],
                            'Company type': [','.join(x['displayName'] for x in all_extended_statups_pages[k]['companyTypeTaggings'])],
                            'Company markets': [','.join(x['displayName'] for x in all_extended_statups_pages[k]['marketTaggings'])],
                        }
                        save_result(data)
                    except Exception as e:
                        logger.error(f'Something went wrong during collecting of data, error: {e}')
            except Exception as e:
                print(e)
        return True
    except Exception as e:
        logger.info(f"Error during scraping: {e}")
        return None

def start_mitmproxy():
    """Start Mitmproxy with the specified addon script."""
    try:
        process = subprocess.Popen(
            ["mitmdump", "-s", ADDON_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return process
    except Exception as e:
        logger.info(f"Error starting Mitmproxy: {e}")
        sys.exit(1)

def stop_mitmproxy(process):
    """Gracefully stop the Mitmproxy process."""
    try:
        if process:
            process.send_signal(signal.SIGINT)
            process.wait()
            logger.info("Mitmproxy stopped.")
    except Exception as e:
        logger.info(f"Error stopping Mitmproxy: {e}")
    
def get_results(data):
    """Process startup data from GraphQL response."""
    for entry in data:
        logger.info('='*80)
        if entry['node']['__typename'] == 'PromotedResult':
            logger.info(entry['node']['promotedStartup']['startupId'])
            all_statups[entry['node']['promotedStartup']['startupId']] = entry['node']['promotedStartup']
        else:
            logger.info(entry['node']['startupId'])
            all_statups[entry['node']['startupId']] = entry['node']

def save_result(data):
    """Save data to Excel file."""
    try:
        df = pd.DataFrame(data)
        if os.path.exists(OUTPUT_FILE):
            with pd.ExcelWriter(OUTPUT_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                df.to_excel(writer, index=False, header=False, sheet_name='Sheet1', startrow=writer.sheets['Sheet1'].max_row)
        else:
            df.to_excel(OUTPUT_FILE, index=False, sheet_name='Sheet1')
    except Exception as e:
        logger.error(f'Something went wrong during writing to file, error: {e}')

def get_page_results(data):
    """Process startup page data from GraphQL response."""
    if "startupResult" in data:
        startup_id = data["startupResult"]["startupId"]
        all_statups_pages[startup_id] = data["startupResult"]

def get_extended_page_results(data):
    """Process extended startup page data from GraphQL response."""
    if "startupResult" in data:
        startup_id = data["startupResult"]["startupId"]
        all_extended_statups_pages[startup_id] = data["startupResult"]
    
def monitor_mitmproxy(process, stop_event):
    """Monitor Mitmproxy process and process captured data."""
    try:
        last_modified = 0
        while not stop_event.is_set():
            try:
                # Check if file exists and has been modified
                if os.path.exists(DATA_FILE):
                    current_modified = os.path.getmtime(DATA_FILE)
                    
                    if current_modified > last_modified:
                        last_modified = current_modified
                        # Process the file
                        try:
                            with open(DATA_FILE) as f:
                                d = json.load(f)
                            dt = json.loads(d).get('data', {})
                            
                            # Process based on type of response
                            if 'talent' in dt and 'searchStartups' in dt['talent'] and 'edges' in dt['talent']['searchStartups']:
                                get_results(dt['talent']['searchStartups']['edges'])
                            elif 'startup' in dt and 'startupResult' in dt['startup']:
                                get_page_results(dt['startup'])
                            elif 'startupOverview' in dt and 'startupResult' in dt['startupOverview']:
                                get_extended_page_results(dt['startupOverview'])
                                
                        except Exception as e:
                            pass
                        try:
                            os.remove(DATA_FILE)
                        except Exception as e:
                            pass
            except Exception as e:
                logger.error(f"Error processing data file: {e}")
                
            # Sleep before checking again
            time.sleep(1)
    except Exception as e:
        logger.info(f"Error monitoring Mitmproxy: {e}")
    finally:
        stop_mitmproxy(process)
    
    def login(self):
        """
        Login to Wellfound.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        if not self.driver:
            logger.error("Browser not started. Call start() first.")
            return False
            
        try:
            username = self.credentials.get('username', '')
            password = self.credentials.get('password', '')
            
            if not username or not password:
                logger.error("Missing credentials. Please set username and password in config.")
                return False
                
            logger.info(f"Logging in to {self.login_url}...")
            self.driver.get(self.login_url)
            
            # Wait for login form to load
            time.sleep(10)  # Initial wait to ensure page is loaded
            
            # Enter credentials
            self.driver.find_element(By.CSS_SELECTOR, "input[id='user_email']").send_keys(username)
            time.sleep(self.delay_range())
            self.driver.find_element(By.CSS_SELECTOR, "input[id='user_password']").send_keys(password)
            time.sleep(self.delay_range())
            
            # Click login button
            self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
            time.sleep(10)  # Wait for login to complete
            
            # Check if login was successful by looking for a known element on the dashboard
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "nav[aria-label='Main']"))
                )
                logger.info("Login successful")
                return True
            except Exception as e:
                logger.error(f"Login verification failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def scrape_jobs(self):
        """
        Scrape job listings.
        
        Returns:
            int: Number of jobs processed
        """
        try:
            # Navigate to job listings page
            self.driver.get("https://wellfound.com/jobs")
            time.sleep(10)
            
            # Scroll down to load more results
            job_count = 0
            counter = 0
            for _ in range(105):  # Maximum number of scrolls
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(10)
                
                # Check if we're still getting new results
                if len(self.all_startups) == counter:
                    logger.info(f"No new startups found after {_+1} scrolls. Stopping.")
                    break
                    
                counter = len(self.all_startups)
                logger.info(f"Found {counter} startups so far")
            
            # Click on job cards to load details
            try:
                details_arrows = self.driver.find_elements(By.CSS_SELECTOR, 'div[class="flex w-full"]')
                logger.info(f"Found {len(details_arrows)} detail arrows to click")
                
                for arrow in details_arrows:
                    arrow.click()
                    time.sleep(self.delay_range())
                    
                    # Close the detail panel
                    close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[data-test='closeButton']")
                    if close_buttons:
                        close_buttons[0].click()
                    
                    time.sleep(self.delay_range())
            except Exception as e:
                logger.error(f"Error clicking on job details: {e}")
            
            # Process collected data
            for startup_id, startup_data in self.all_startups.items():
                try:
                    # Skip if no extended data available
                    if startup_id not in self.all_extended_startups_pages:
                        continue
                        
                    # Process job listings for this startup
                    if "highlightedJobListings" in startup_data:
                        for job in startup_data["highlightedJobListings"]:
                            try:
                                data = {
                                    'Company name': [startup_data.get("name", "")],
                                    'Actively hiring': [''.join([x["label"] for x in self.all_extended_startups_pages[startup_id]["badges"] if x.get("name", '') == 'ACTIVELY_HIRING_BADGE'])],
                                    'Description': [startup_data.get("highConcept", "")],
                                    'Company size': [startup_data.get("companySize", "").split('SIZE_')[-1].replace('_', '-')],
                                    'Badges': [','.join([x["label"] for x in self.all_extended_startups_pages[startup_id]["badges"]])],
                                    'Title': [job.get('title', '')],
                                    'Location': [','.join(job.get('locationNames', []))],
                                    'Remote options': [job.get('remoteConfig', {}).get('kind', '').lower()],
                                    'Remote': ['Yes' if job.get('remote', False) is True else ''],
                                    'Salary': [job.get('compensation', '')],
                                    'Published time': [datetime.utcfromtimestamp(int(job.get('liveStartAt', 0))).strftime('%Y-%m-%d %H:%M:%S')],
                                    'Website': [self.all_extended_startups_pages[startup_id].get('companyUrl', '')],
                                    'Linkedin': [self.all_extended_startups_pages[startup_id].get('linkedInUrl', '')],
                                    'Company type': [','.join(x.get('displayName', '') for x in self.all_extended_startups_pages[startup_id].get('companyTypeTaggings', []))],
                                    'Company markets': [','.join(x.get('displayName', '') for x in self.all_extended_startups_pages[startup_id].get('marketTaggings', []))],
                                }
                                
                                # Save the data
                                save_to_excel(
                                    data,
                                    output_file=self.custom_output_file, 
                                    prefix='wellfound_results'
                                )
                                
                                job_count += 1
                            except Exception as e:
                                logger.error(f"Error processing job data: {e}")
                except Exception as e:
                    logger.error(f"Error processing startup {startup_id}: {e}")
            
            return job_count
            
        except Exception as e:
            logger.error(f"Error scraping jobs: {e}")
            return 0
    
    def run(self):
        """
        Run the full scraping process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Start browser and proxy
            if not self.start():
                return False
                
            # Login
            if not self.login():
                self.stop()
                return False
            
            # Scrape jobs
            job_count = self.scrape_jobs()
            
            # Clean up
            self.stop()
            
            if job_count > 0:
                logger.info(f"Successfully scraped {job_count} jobs")
                return True
            else:
                logger.warning("No jobs found")
                return False
                
        except Exception as e:
            logger.error(f"Error running Wellfound scraper: {e}")
            self.cleanup()
            return False


def run_wellfound_scraper(headless=False, output_file=None, use_proxy=True):
    """
    Run the Wellfound scraper.
    
    Args:
        headless (bool): Run in headless mode
        output_file (str): Custom output file path
        use_proxy (bool): Whether to use MITM proxy
        
    Returns:
        bool: True if successful, False otherwise
    """
    global OUTPUT_FILE
    
    if output_file:
        OUTPUT_FILE = output_file
    
    logger.info("Starting Wellfound scraper...")
    
    stop_event = threading.Event()  # Event to stop Mitmproxy monitoring
    
    try:
        # Start mitmproxy
        if use_proxy:
            logger.info("Starting Mitmproxy...")
            mitm_process = start_mitmproxy()
            
            # Start Mitmproxy monitoring in a separate thread
            monitor_thread = threading.Thread(target=monitor_mitmproxy, args=(mitm_process, stop_event))
            monitor_thread.daemon = True
            monitor_thread.start()
        
        # Start the scraping task
        logger.info("Starting scraping task...")
        result = scrape_heading_task()
        logger.info(f"Scraping result: {result}")
        
        success = result is True
        
    except Exception as e:
        logger.error(f"Error during Wellfound scraping: {e}")
        success = False
        
    finally:
        # Stop Mitmproxy if it was started
        if use_proxy:
            stop_event.set()
            if 'monitor_thread' in locals():
                monitor_thread.join(timeout=5)
        
        # Clean up display if it was started
        try:
            if 'display' in globals():
                display.stop()
        except:
            pass
            
        logger.info("Wellfound scraper finished.")
        
    return success
