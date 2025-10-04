"""
Morizo AI v2 - Generic Logger

This module provides a simple, generic logger for all layers of the application.
Each layer is responsible for formatting their own log messages.
"""

import logging
import time
import os
from functools import wraps

from .logging import get_logger


class GenericLogger:
    """Simple generic logger for all application layers"""
    
    def __init__(self, layer: str, component: str = "", initialize_logging: bool = False):
        """
        Initialize generic logger
        
        Args:
            layer: Layer name (api, service, mcp, core)
            component: Component name (optional)
            initialize_logging: Whether to initialize logging system (default: False for MCP servers)
        """
        self.layer = layer
        self.component = component
        
        # Initialize logging system only if requested
        if initialize_logging:
            from .logging import setup_logging
            setup_logging(initialize=True)
        
        self.logger = get_logger(f'{layer}.{component}' if component else layer)
    
    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message"""
        self.logger.critical(message)


def log_execution_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger = get_logger('performance')
            logger.info(f"⏱️ [PERF] {func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger = get_logger('performance')
            logger.error(f"⏱️ [PERF] {func.__name__} failed after {duration:.3f}s: {e}")
            raise
    return wrapper


def log_execution_time_async(func):
    """Decorator to log async function execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger = get_logger('performance')
            logger.info(f"⏱️ [PERF] {func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger = get_logger('performance')
            logger.error(f"⏱️ [PERF] {func.__name__} failed after {duration:.3f}s: {e}")
            raise
    return wrapper


if __name__ == "__main__":
    # Quick verification
    print("✅ 汎用ロガーが利用可能です")