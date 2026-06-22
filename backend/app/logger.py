"""
Centralized logging configuration.
"""

import logging
import sys
from app.config import settings


def setup_logger() -> logging.Logger:
    """
    Configure and return application logger.
    
    Returns:
        Logger instance configured with appropriate level and format
    """
    # Create logger
    logger = logging.getLogger("typeahead")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Single logger instance - import this everywhere
logger = setup_logger()
