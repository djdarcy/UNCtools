"""
Logging utilities for UNCtools.

This module provides functions for configuring and using logging throughout
the UNCtools library.
"""

import os
import sys
import logging
import datetime
from typing import Optional, Union, Dict, Any, List, TextIO

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default date format for log timestamps
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO

# Package logger
logger = logging.getLogger("unctools")

class UNCLogFormatter(logging.Formatter):
    """
    Custom log formatter for UNCtools.
    
    This formatter adds additional context information to log entries
    including thread/process information for concurrent operations.
    """
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        """
        Initialize the formatter.
        
        Args:
            fmt: Log format string.
            datefmt: Date format string.
        """
        if fmt is None:
            fmt = DEFAULT_LOG_FORMAT
        if datefmt is None:
            datefmt = DEFAULT_DATE_FORMAT
        super().__init__(fmt=fmt, datefmt=datefmt)
    
    def formatException(self, ei) -> str:
        """
        Format an exception with enhanced details.
        
        Args:
            ei: Exception information tuple.
            
        Returns:
            Formatted exception string.
        """
        # Get the standard exception text
        result = super().formatException(ei)
        # Add custom context information
        return f"{result}\nLogger: {logger.name}"

def configure_logging(
    level: int = DEFAULT_LOG_LEVEL,
    format_str: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    log_file: Optional[str] = None,
    log_to_console: bool = True,
    log_to_file: bool = False,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    propagate: bool = True
) -> None:
    """
    Configure logging for UNCtools.
    
    Args:
        level: Logging level (default: logging.INFO).
        format_str: Log format string.
        date_format: Date format for log timestamps.
        log_file: Path to log file (if log_to_file is True).
        log_to_console: Whether to log to console.
        log_to_file: Whether to log to a file.
        max_bytes: Maximum log file size before rotation.
        backup_count: Number of backup log files to keep.
        propagate: Whether to propagate logs to the root logger.
    """
    # Get the package logger
    unc_logger = logging.getLogger("unctools")
    
    # Reset handlers
    for handler in unc_logger.handlers[:]:
        unc_logger.removeHandler(handler)
    
    # Set log level
    unc_logger.setLevel(level)
    
    # Create formatter
    formatter = UNCLogFormatter(format_str, date_format)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        unc_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        if log_file is None:
            # Default log file in user's home directory
            log_dir = os.path.join(os.path.expanduser("~"), ".unctools", "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            # Use date in filename
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(log_dir, f"unctools_{date_str}.log")
        
        # Create directory if needed
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        try:
            # Use rotating file handler for log rotation
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            unc_logger.addHandler(file_handler)
            
            logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            logger.warning(f"Failed to set up file logging: {e}")
    
    # Set propagation
    unc_logger.propagate = propagate
    
    logger.debug("Logging configured successfully")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: The name of the module.
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(f"unctools.{name}")

def enable_debug_logging() -> None:
    """
    Enable debug-level logging for UNCtools.
    
    This is a convenience function for quickly enabling detailed logging.
    """
    configure_logging(level=logging.DEBUG)
    logger.debug("Debug logging enabled")

def disable_logging() -> None:
    """
    Disable all logging for UNCtools.
    
    This is useful for applications that want to handle all output themselves.
    """
    unc_logger = logging.getLogger("unctools")
    
    # Remove all handlers
    for handler in unc_logger.handlers[:]:
        unc_logger.removeHandler(handler)
    
    # Set level to higher than CRITICAL to effectively disable
    unc_logger.setLevel(logging.CRITICAL + 10)

def log_exception(exc: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exception with additional context information.
    
    Args:
        exc: The exception to log.
        context: Additional context information (optional).
    """
    context_str = ", ".join(f"{k}={v}" for k, v in (context or {}).items())
    
    if context_str:
        logger.exception(f"Exception occurred ({context_str}): {exc}")
    else:
        logger.exception(f"Exception occurred: {exc}")

class LogContext:
    """
    Context manager for temporarily changing log levels.
    
    This allows for increasing or decreasing verbosity for a specific block of code.
    """
    
    def __init__(self, level: int = logging.DEBUG, module: Optional[str] = None):
        """
        Initialize the context manager.
        
        Args:
            level: The logging level to use within the context.
            module: The specific module to change (if None, changes the entire package).
        """
        self.level = level
        self.module = module
        self.previous_level = None
        self.logger = None
    
    def __enter__(self) -> 'LogContext':
        # Get the appropriate logger
        if self.module:
            self.logger = logging.getLogger(f"unctools.{self.module}")
        else:
            self.logger = logging.getLogger("unctools")
        
        # Store previous level and set new level
        self.previous_level = self.logger.level
        self.logger.setLevel(self.level)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Restore previous level
        if self.logger and self.previous_level is not None:
            self.logger.setLevel(self.previous_level)