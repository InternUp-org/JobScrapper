#!/usr/bin/env python
"""
CLI interface for running job scrapers.
"""
import argparse
import os
import sys
import logging
from datetime import datetime

# Add the project root to the path so we can import our modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Set up logging directory
log_dir = os.path.join(project_root, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Set up logging
log_file = os.path.join(log_dir, f'scraper_{datetime.now().strftime("%Y-%m-%d")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ] 
)

logger = logging.getLogger(__name__)

# We'll import scrapers conditionally to avoid dependency issues

def setup_argparse():
    """Set up command line argument parsing."""
    parser = argparse.ArgumentParser(description='Run job scrapers')
    
    # Scraper selection arguments
    scraper_group = parser.add_argument_group('Scraper Selection')
    scraper_group.add_argument('--all', action='store_true', help='Run all scrapers')
    scraper_group.add_argument('--jobright', action='store_true', help='Run JobRight scraper')
    scraper_group.add_argument('--wellfound', action='store_true', help='Run Wellfound scraper')
    
    # Common options
    common_group = parser.add_argument_group('Common Options')
    common_group.add_argument('--headless', action='store_true', help='Run in headless mode')
    common_group.add_argument('--output-dir', type=str, help='Output directory for results')
    
    # Scraper-specific options
    wellfound_group = parser.add_argument_group('Wellfound Options')
    wellfound_group.add_argument('--no-proxy', action='store_true', help='Disable MITM proxy for Wellfound scraper')
    
    return parser

def main():
    """Main entry point for the CLI."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Determine which scrapers to run
    run_all = args.all
    run_jobright = args.jobright or run_all
    run_wellfound = args.wellfound or run_all
    
    if not (run_jobright or run_wellfound):
        parser.print_help()
        print("\nError: Please specify at least one scraper to run (--all, --jobright, or --wellfound)")
        return 1
        
    # Check for X11 dependencies if Wellfound is requested
    if run_wellfound:
        try:
            # Check for Xvfb
            if os.system("which Xvfb >/dev/null 2>&1") != 0:
                logger.warning("Xvfb not found. The Wellfound scraper may have issues in a headless environment.")
                
            # Check for .Xauthority
            xauth_path = os.path.expanduser("~/.Xauthority")
            if not os.path.exists(xauth_path):
                logger.warning(f"{xauth_path} not found. The Wellfound scraper may have issues with X11 authentication.")
        except Exception as e:
            logger.warning(f"Error checking X11 dependencies: {e}")
    
    # Set up output files
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    output_dir = args.output_dir
    
    if output_dir:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    else:
        output_dir = os.path.join(project_root, 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    logger.info(f"Output directory: {output_dir}")
    
    # Set up configuration directory
    config_dir = os.path.join(project_root, 'config')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    # Check for credentials
    if not os.path.exists(os.path.join(project_root, 'credentials.txt')) and \
       not os.path.exists(os.path.join(config_dir, 'credentials.json')):
        logger.warning("No credentials found! Please create credentials.txt in the project root or credentials.json in the config directory.")
    
    # Run scrapers
    results = []
    
    if run_jobright:
        logger.info("Running JobRight scraper...")
        try:
            # Import only when needed
            from src.scrapers.jobright.scraper import run_jobright_scraper
            
            output_file = os.path.join(output_dir, f'jobright_results_{timestamp}.xlsx')
            success = run_jobright_scraper(headless=args.headless, output_file=output_file)
            results.append(("JobRight", success, output_file if success else None))
        except Exception as e:
            logger.error(f"Error running JobRight scraper: {e}")
            results.append(("JobRight", False, None))
    
    if run_wellfound:
        logger.info("Running Wellfound scraper...")
        try:
            # Import only when needed
            from src.scrapers.wellfound.scraper import run_wellfound_scraper
            
            output_file = os.path.join(output_dir, f'wellfound_results_{timestamp}.xlsx')
            success = run_wellfound_scraper(
                headless=args.headless, 
                output_file=output_file,
                use_proxy=not args.no_proxy
            )
            results.append(("Wellfound", success, output_file if success else None))
        except Exception as e:
            logger.error(f"Error running Wellfound scraper: {e}")
            results.append(("Wellfound", False, None))
    
    # Print summary
    logger.info("\nScraper Summary:")
    for name, success, output_file in results:
        status = "✓ Success" if success else "✗ Failed"
        output_info = f"Results saved to: {output_file}" if output_file and os.path.exists(output_file) else "No results saved"
        logger.info(f"{name}: {status} - {output_info if success else ''}")
    
    # Return exit code based on success
    return 0 if all(success for _, success, _ in results) else 1

if __name__ == "__main__":
    sys.exit(main())
