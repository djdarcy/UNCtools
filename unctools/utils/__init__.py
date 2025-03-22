"""
Utility functions and helpers for UNCtools.

This subpackage contains utility functions and helpers used across the UNCtools library,
including logging, cross-platform compatibility, and validation utilities.
"""

import os
import logging
import platform
import sys
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

# Set up module-level logger
logger = logging.getLogger(__name__)

# Import key functions for the package namespace
from .logger import configure_logging, get_logger
from .compat import is_windows, is_linux, is_macos, get_platform_info
from .validation import validate_path, validate_unc_path, validate_local_path

# For convenience, re-export platform detection in the utils namespace
is_windows = is_windows()
is_linux = is_linux()
is_macos = is_macos()

# Export key functions at the package level
__all__ = [
    'configure_logging',
    'get_logger',
    'is_windows',
    'is_linux',
    'is_macos',
    'get_platform_info',
    'validate_path',
    'validate_unc_path',
    'validate_local_path'
]
