from mitmproxy import http
import json
import logging
import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data.json')
LOG_FILE = os.path.join(BASE_DIR, 'network.log')

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ] 
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Keyword to filter URLs
KEYWORD = "graph"

def response(flow: http.HTTPFlow):
    """
    This function is triggered whenever Mitmproxy captures a response.
    """
    # Check if the request URL contains the keyword
    if KEYWORD in flow.request.url:
        # Log the response body (ensure it's decoded)
        if flow.response.content:
            
            response_body = flow.response.text
            if 'talent' in response_body or 'startupOverview' in response_body or 'StartupPageMeta' in response_body:
                try:
                    with open(DATA_FILE, 'w') as f:
                        json.dump(response_body, f)
                except:
                    pass
