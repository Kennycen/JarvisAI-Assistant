"""Structured logging for tools"""
import logging
import sys
from typing import Optional

def setup_tool_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create a standardized logger for tools.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"jarvis.tools.{name}")
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger