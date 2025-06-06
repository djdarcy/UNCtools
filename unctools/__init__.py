r"""
UNCtools - A comprehensive toolkit for handling UNC paths, network drives, and substituted drives.

This package provides utilities for working with UNC paths (\\server\share) and network/substituted 
drives across different operating systems, with special support for Windows environments.

Basic Usage:
    from unctools import convert_to_local, convert_to_unc
    
    # Convert UNC path to local drive path
    local_path = convert_to_local("\\\\server\\share\\folder\\file.txt")
    
    # Convert local drive path back to UNC
    unc_path = convert_to_unc("Z:\\folder\\file.txt")
    
    # Detect path types
    from unctools import is_unc_path, is_network_drive
    
    if is_unc_path(path):
        print("This is a UNC path")
    
    if is_network_drive("Z:"):
        print("Z: is a network drive")
        
Advanced Windows functionality:
    from unctools.windows import fix_security_zone, get_network_mappings
    
    # Fix Windows security zone for a server
    fix_security_zone("server")
    
    # Get all network drive mappings
    mappings = get_network_mappings()
"""

__version__ = "0.1.0"

import os
import sys
import logging
from pathlib import Path

# Set up package-level logger
logger = logging.getLogger(__name__)

# Import core functionality into the main namespace
from .converter import convert_to_local, convert_to_unc, normalize_path
from .detector import (
    is_unc_path, is_network_drive, is_subst_drive, 
    get_path_type, get_network_mappings, detect_path_issues
)
from .operations import (
    safe_open, safe_copy, batch_convert, batch_copy, 
    process_files, file_exists, replace_in_file, batch_replace_in_files,
    get_unc_path_elements, build_unc_path, is_path_accessible, find_accessible_path
)

# Determine if we're running on Windows
IS_WINDOWS = os.name == 'nt'

# Import Windows-specific modules if on Windows
if IS_WINDOWS:
    try:
        from .windows import fix_security_zone, add_to_intranet_zone
    except ImportError as e:
        logger.warning(f"Windows-specific modules could not be imported: {e}")
else:
    # Define stub functions for non-Windows platforms
    def fix_security_zone(server_name):
        """Stub function for non-Windows platforms."""
        logger.warning("fix_security_zone is only available on Windows")
        return False
        
    def add_to_intranet_zone(server_name):
        """Stub function for non-Windows platforms."""
        logger.warning("add_to_intranet_zone is only available on Windows")
        return False

# Configure default logging
def configure_logging(level=logging.INFO, handler=None):
    """
    Configure the package's logging settings.
    
    Args:
        level: The logging level (default: logging.INFO)
        handler: A logging handler to use (default: StreamHandler)
    """
    if handler is None:
        handler = logging.StreamHandler()
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    logger.addHandler(handler)
    
# Version information
def get_version():
    """Return the package version."""
    return __version__
