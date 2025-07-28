"""Logging configuration for the Reverb bot."""

import logging
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Create a new log file for each session
LOG_FILE = LOGS_DIR / f"reverb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging
def setup_logger(debug_mode: bool = False):
    """Set up the logger with appropriate configuration.
    
    Args:
        debug_mode: If True, sets logging level to DEBUG, otherwise INFO
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure file handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Get root logger
    logger = logging.getLogger('reverb')
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log startup information
    logger.info("=" * 50)
    logger.info("Reverb Bot Starting")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info("=" * 50)

    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: The name of the logger (will be prefixed with 'reverb.')
    
    Returns:
        A Logger instance
    """
    if name:
        return logging.getLogger(f'reverb.{name}')
    return logging.getLogger('reverb')
