"""
Logging utility for scrapers.
Provides consistent logging configuration across all scrapers.
"""
import os
import logging
from datetime import datetime

def get_logger(name, log_dir=None, console_level=logging.INFO, file_level=logging.WARNING):
    """
    Get a configured logger instance.
    
    Args:
        name (str): Logger name
        log_dir (str): Directory to store log files (default: None, uses CWD)
        console_level: Logging level for console output
        file_level: Logging level for file output
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Return if handler already exists to prevent duplicate handlers
    if logger.handlers:
        return logger
        
    # Set the root logger level
    logger.setLevel(logging.DEBUG)
    
    # Set log directory
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler and set level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create log filename based on module name
    module_name = name.split('.')[-1]
    log_file = os.path.join(log_dir, f'{module_name}_{datetime.now().strftime("%Y-%m-%d")}.log')
    
    # Create file handler and set level
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
