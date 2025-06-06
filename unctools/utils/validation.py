"""
Path validation utilities for UNCtools.

This module provides functions for validating and checking various path types,
ensuring they conform to expected formats and restrictions.
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union, Any

# Set up module-level logger
logger = logging.getLogger(__name__)

# Regular expressions for common path formats
UNC_PATH_REGEX = re.compile(r'^\\\\([^\\]+)\\([^\\]+)(?:\\(.*))?$')
DRIVE_PATH_REGEX = re.compile(r'^([A-Za-z]:)(?:\\(.*))?$')
POSIX_PATH_REGEX = re.compile(r'^(/[^/]*)+/?$')

# Maximum path length limitations
MAX_PATH_WINDOWS = 260
MAX_PATH_WINDOWS_EXTENDED = 32767
MAX_PATH_UNIX = 4096  # Common limit, can vary by filesystem

class ValidationError(Exception):
    """Exception raised for path validation errors."""
    pass

def validate_path(path: Union[str, Path], 
                exists: bool = False, 
                is_file: bool = False, 
                is_dir: bool = False,
                is_absolute: bool = False,
                max_length: Optional[int] = None) -> bool:
    """
    Validate a path against common requirements.
    
    Args:
        path: The path to validate.
        exists: Whether the path must exist.
        is_file: Whether the path must be a file.
        is_dir: Whether the path must be a directory.
        is_absolute: Whether the path must be absolute.
        max_length: Maximum allowed path length.
        
    Returns:
        True if the path meets all requirements.
        
    Raises:
        ValidationError: If the path does not meet the requirements.
    """
    path_obj = Path(path)
    path_str = str(path_obj)
    
    # Check if the path exists if required
    if exists and not os.path.exists(path_str):
        raise ValidationError(f"Path does not exist: {path_str}")
    
    # Check if the path is a file if required
    if is_file and not os.path.isfile(path_str):
        raise ValidationError(f"Path is not a file: {path_str}")
    
    # Check if the path is a directory if required
    if is_dir and not os.path.isdir(path_str):
        raise ValidationError(f"Path is not a directory: {path_str}")
    
    # Check if the path is absolute if required
    if is_absolute and not os.path.isabs(path_str):
        raise ValidationError(f"Path is not absolute: {path_str}")
    
    # Check the path length if a maximum is specified
    if max_length is not None:
        if len(path_str) > max_length:
            raise ValidationError(f"Path exceeds maximum length ({len(path_str)} > {max_length}): {path_str}")
    
    return True

def validate_unc_path(path: Union[str, Path]) -> bool:
    """
    Validate a UNC path (\\\\server\\share\\...).
    
    Args:
        path: The path to validate.
        
    Returns:
        True if the path is a valid UNC path.
        
    Raises:
        ValidationError: If the path is not a valid UNC path.
    """
    path_str = str(path).replace('/', '\\')
    
    # Check if the path matches the UNC pattern
    match = UNC_PATH_REGEX.match(path_str)
    if not match:
        raise ValidationError(f"Not a valid UNC path: {path_str}")
    
    # Extract server and share names
    server = match.group(1)
    share = match.group(2)
    
    # Validate server name
    if not server:
        raise ValidationError(f"Invalid UNC path: missing server name in {path_str}")
    
    # Validate share name
    if not share:
        raise ValidationError(f"Invalid UNC path: missing share name in {path_str}")
    
    return True

def validate_local_path(path: Union[str, Path], windows_only: bool = False) -> bool:
    """
    Validate a local path (drive letter on Windows, absolute path on Unix).
    
    Args:
        path: The path to validate.
        windows_only: Whether to only accept Windows drive paths.
        
    Returns:
        True if the path is a valid local path.
        
    Raises:
        ValidationError: If the path is not a valid local path.
    """
    path_str = str(path)
    
    # Check if the path is a Windows drive path
    if DRIVE_PATH_REGEX.match(path_str):
        # Valid Windows drive path
        return True
    
    # If windows_only is True, only accept Windows drive paths
    if windows_only:
        raise ValidationError(f"Not a valid Windows drive path: {path_str}")
    
    # Otherwise, check if the path is a valid POSIX absolute path
    if POSIX_PATH_REGEX.match(path_str):
        # Valid POSIX absolute path
        return True
    
    # Not a valid local path in either format
    raise ValidationError(f"Not a valid local path: {path_str}")

def check_path_length_limits(path: Union[str, Path], 
                            extended_prefix: bool = False) -> Dict[str, Any]:
    """
    Check if a path exceeds platform-specific length limits.
    
    Args:
        path: The path to check.
        extended_prefix: Whether to consider paths with the Windows extended path prefix.
        
    Returns:
        A dictionary with information about path length limits:
        {
            'length': int,             # Actual path length
            'exceeds_windows': bool,   # Whether it exceeds standard Windows limit
            'exceeds_windows_ext': bool,  # Whether it exceeds extended Windows limit
            'exceeds_unix': bool,      # Whether it exceeds common Unix limit
            'exceeds_current': bool,   # Whether it exceeds the current platform's limit
        }
    """
    path_str = str(path)
    length = len(path_str)
    
    # Check if the path has the extended path prefix
    has_extended_prefix = path_str.startswith('\\\\?\\')
    
    # Calculate effective length for Windows
    effective_length = length
    if has_extended_prefix:
        # Subtract the prefix length
        effective_length = length - 4
    
    # Check against various limits
    exceeds_windows = effective_length > MAX_PATH_WINDOWS
    exceeds_windows_ext = length > MAX_PATH_WINDOWS_EXTENDED
    exceeds_unix = length > MAX_PATH_UNIX
    
    # Determine the current platform's limit
    exceeds_current = False
    if os.name == 'nt':
        # On Windows, check against the appropriate limit
        if extended_prefix or has_extended_prefix:
            exceeds_current = exceeds_windows_ext
        else:
            exceeds_current = exceeds_windows
    else:
        # On Unix-like systems, check against the Unix limit
        exceeds_current = exceeds_unix
    
    return {
        'length': length,
        'effective_length': effective_length,
        'has_extended_prefix': has_extended_prefix,
        'exceeds_windows': exceeds_windows,
        'exceeds_windows_ext': exceeds_windows_ext,
        'exceeds_unix': exceeds_unix,
        'exceeds_current': exceeds_current
    }

def is_valid_server_name(server: str) -> bool:
    """
    Check if a server name is valid.
    
    Args:
        server: The server name to check.
        
    Returns:
        True if the server name is valid, False otherwise.
    """
    # Check for empty server name
    if not server:
        return False
    
    # Check for invalid characters
    invalid_chars = '<>:"/\\|?*'
    if any(c in server for c in invalid_chars):
        return False
    
    # Check for spaces in server name (generally not recommended)
    if ' ' in server:
        logger.warning(f"Server name contains spaces: '{server}'")
    
    return True

def is_valid_share_name(share: str) -> bool:
    """
    Check if a share name is valid.
    
    Args:
        share: The share name to check.
        
    Returns:
        True if the share name is valid, False otherwise.
    """
    # Check for empty share name
    if not share:
        return False
    
    # Check for invalid characters
    invalid_chars = '<>:"/\\|?*'
    if any(c in share for c in invalid_chars):
        return False
    
    # Check length (Windows limits share names to 80 characters)
    if len(share) > 80:
        return False
    
    return True

def is_valid_filename(filename: str) -> bool:
    """
    Check if a filename is valid.
    
    Args:
        filename: The filename to check.
        
    Returns:
        True if the filename is valid, False otherwise.
    """
    # Check for empty filename
    if not filename:
        return False
    
    # Check for invalid characters (Windows is most restrictive)
    invalid_chars = '<>:"/\\|?*'
    if any(c in filename for c in invalid_chars):
        return False
    
    # Check for reserved names on Windows
    if os.name == 'nt':
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        # Check if the filename (without extension) is a reserved name
        base_name = os.path.splitext(filename)[0].upper()
        if base_name in reserved_names:
            return False
    
    return True

def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """
    Sanitize a filename by replacing invalid characters.
    
    Args:
        filename: The filename to sanitize.
        replacement: The character to use as replacement.
        
    Returns:
        A sanitized filename.
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for c in invalid_chars:
        filename = filename.replace(c, replacement)
    
    # Replace reserved names on Windows
    if os.name == 'nt':
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        # Check if the filename (without extension) is a reserved name
        base_name, ext = os.path.splitext(filename)
        if base_name.upper() in reserved_names:
            base_name = f"{base_name}{replacement}"
            filename = f"{base_name}{ext}"
    
    # Ensure the filename is not empty
    if not filename:
        filename = "unnamed"
    
    return filename