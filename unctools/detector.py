"""
Path detection utilities for UNC paths, network drives, and substituted drives.

This module provides functions to detect and identify different types of paths,
including UNC paths, network drives, and substituted (subst) drives.
"""

import os
import re
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

# Import from our own modules
from .converter import get_mappings

# Set up module-level logger
logger = logging.getLogger(__name__)

# Constants
PATH_TYPE_UNKNOWN = "unknown"
PATH_TYPE_LOCAL = "local"
PATH_TYPE_UNC = "unc"
PATH_TYPE_NETWORK = "network"
PATH_TYPE_SUBST = "subst"
PATH_TYPE_REMOVABLE = "removable"
PATH_TYPE_CDROM = "cdrom"
PATH_TYPE_RAMDISK = "ramdisk"

# Try to import Windows-specific modules
IS_WINDOWS = os.name == 'nt'

if IS_WINDOWS:
    try:
        import ctypes
        import win32api
        import win32file
        HAVE_WIN32API = True
    except ImportError:
        HAVE_WIN32API = False
        logger.debug("win32api and/or ctypes modules not available. Some Windows-specific features will use fallbacks.")
else:
    HAVE_WIN32API = False

# Cache for path type detection to avoid repeated expensive operations
_path_type_cache = {}

def _clear_path_type_cache() -> None:
    """Clear the internal path type detection cache."""
    global _path_type_cache
    _path_type_cache.clear()

def is_unc_path(path: Union[str, Path]) -> bool:
    """
    Determine if a path is a UNC path (starts with \\server\share).
    
    Args:
        path: The path to check.
        
    Returns:
        True if the path is a UNC path, False otherwise.
    """
    path_str = str(path).replace('/', '\\')
    return path_str.startswith('\\\\')

def _get_drive_type_windows(drive_letter: str) -> int:
    """
    Get the drive type using Windows API.
    
    Args:
        drive_letter: The drive letter to check (e.g., 'C:').
        
    Returns:
        The drive type code from GetDriveTypeW.
    """
    if not IS_WINDOWS:
        return 0
        
    if not drive_letter.endswith('\\'):
        drive_letter += '\\'
        
    try:
        if HAVE_WIN32API:
            # Use win32api if available
            return win32file.GetDriveType(drive_letter)
        else:
            # Fall back to direct ctypes call
            return ctypes.windll.kernel32.GetDriveTypeW(drive_letter)
    except Exception as e:
        logger.warning(f"Failed to get drive type for {drive_letter}: {e}")
        return 0

def get_drive_type(drive: Union[str, Path]) -> str:
    """
    Get the type of a drive.
    
    Args:
        drive: The drive letter or path to check.
        
    Returns:
        A string indicating the drive type:
        - 'local': Local fixed drive
        - 'network': Network drive
        - 'subst': Substituted drive (not a physical device)
        - 'removable': Removable drive (e.g., USB)
        - 'cdrom': CD-ROM drive
        - 'ramdisk': RAM disk
        - 'unknown': Unknown or could not determine
    """
    # Normalize the drive input
    drive_str = str(drive)
    
    # Extract drive letter if a full path was provided
    match = re.match(r'^([A-Za-z]:)', drive_str)
    if match:
        drive_letter = match.group(1)
    else:
        drive_letter = drive_str
    
    # Only applicable to Windows
    if not IS_WINDOWS:
        return PATH_TYPE_UNKNOWN
    
    # Check cache
    cache_key = drive_letter.upper()
    if cache_key in _path_type_cache:
        return _path_type_cache[cache_key]
    
    # Windows drive type constants
    DRIVE_UNKNOWN = 0
    DRIVE_NO_ROOT_DIR = 1
    DRIVE_REMOVABLE = 2
    DRIVE_FIXED = 3
    DRIVE_REMOTE = 4
    DRIVE_CDROM = 5
    DRIVE_RAMDISK = 6
    
    # Get drive type
    drive_type = _get_drive_type_windows(drive_letter)
    
    # Map drive type to string
    if drive_type == DRIVE_FIXED:
        # For fixed drives, check if it's a subst drive
        if is_subst_drive(drive_letter):
            result = PATH_TYPE_SUBST
        else:
            result = PATH_TYPE_LOCAL
    elif drive_type == DRIVE_REMOTE:
        result = PATH_TYPE_NETWORK
    elif drive_type == DRIVE_REMOVABLE:
        result = PATH_TYPE_REMOVABLE
    elif drive_type == DRIVE_CDROM:
        result = PATH_TYPE_CDROM
    elif drive_type == DRIVE_RAMDISK:
        result = PATH_TYPE_RAMDISK
    elif drive_type in (DRIVE_UNKNOWN, DRIVE_NO_ROOT_DIR):
        # Could be a subst that points to a non-existent location
        if is_subst_drive(drive_letter):
            result = PATH_TYPE_SUBST
        else:
            result = PATH_TYPE_UNKNOWN
    else:
        result = PATH_TYPE_UNKNOWN
    
    # Cache the result
    _path_type_cache[cache_key] = result
    
    return result

def is_network_drive(drive: Union[str, Path, None]) -> bool:
    """
    Determine if a drive is a network drive.
    
    Args:
        drive: The drive letter or path to check.
        
    Returns:
        True if the drive is a network drive, False otherwise.
    """
    # Handle None input
    if drive is None:
        return False
        
    return get_drive_type(drive) == PATH_TYPE_NETWORK

def is_subst_drive(drive: Union[str, Path, None]) -> bool:
    """
    Determine if a drive is a substituted (subst) drive.
    
    Args:
        drive: The drive letter or path to check.
        
    Returns:
        True if the drive is a substituted drive, False otherwise.
    """
    # Handle None input
    if drive is None:
        return False
        
    # Extract drive letter if a full path was provided
    drive_str = str(drive)
    match = re.match(r'^([A-Za-z]:)', drive_str)
    if match:
        drive_letter = match.group(1)
    else:
        drive_letter = drive_str
    
    # Only applicable to Windows
    if not IS_WINDOWS:
        return False
    
    # Check cache
    cache_key = f"subst_{drive_letter.upper()}"
    if cache_key in _path_type_cache:
        return _path_type_cache[cache_key]
    
    # Check if the drive is a subst drive
    try:
        # Try to get subst drives using the 'subst' command
        output = subprocess.check_output(['subst'], text=True, stderr=subprocess.STDOUT)
        
        # Look for the drive letter in the output
        drive_pattern = re.escape(drive_letter.upper().rstrip('\\')) + r'\\: => (.*)'
        match = re.search(drive_pattern, output)
        
        result = match is not None
        
        # Cache the result
        _path_type_cache[cache_key] = result
        
        return result
    except Exception as e:
        logger.warning(f"Failed to check if {drive_letter} is a subst drive: {e}")
        return False

def get_subst_target(drive: Union[str, Path]) -> Optional[str]:
    """
    Get the target path of a substituted (subst) drive.
    
    Args:
        drive: The drive letter or path to check.
        
    Returns:
        The target path of the subst drive, or None if the drive is not a subst drive.
    """
    # Extract drive letter if a full path was provided
    drive_str = str(drive)
    match = re.match(r'^([A-Za-z]:)', drive_str)
    if match:
        drive_letter = match.group(1)
    else:
        drive_letter = drive_str
    
    # Only applicable to Windows
    if not IS_WINDOWS:
        return None
    
    # Check if it's a subst drive first
    if not is_subst_drive(drive_letter):
        return None
    
    try:
        # Get subst drives using the 'subst' command
        output = subprocess.check_output(['subst'], text=True, stderr=subprocess.STDOUT)
        
        # Look for the drive letter in the output
        drive_pattern = re.escape(drive_letter.upper().rstrip('\\')) + r'\\: => (.*)'
        match = re.search(drive_pattern, output)
        
        if match:
            return match.group(1)
        
        return None
    except Exception as e:
        logger.warning(f"Failed to get subst target for {drive_letter}: {e}")
        return None

def get_network_target(drive: Union[str, Path, None]) -> Optional[str]:
    """
    Get the UNC path target of a network drive.
    
    Args:
        drive: The drive letter or path to check.
        
    Returns:
        The UNC path target of the network drive, or None if the drive is not a network drive
        or if the target cannot be determined.
    """
    # Handle None input
    if drive is None:
        return None
        
    # Extract drive letter if a full path was provided
    drive_str = str(drive)
    match = re.match(r'^([A-Za-z]:)', drive_str)
    if match:
        drive_letter = match.group(1)
    else:
        drive_letter = drive_str
    
    # Only applicable to Windows
    if not IS_WINDOWS:
        return None
    
    # Check if it's a network drive first
    if not is_network_drive(drive_letter):
        return None
    
    # Get the mappings
    mappings = get_mappings()
    reverse_mappings = {}
    
    # Build reverse mappings (drive letter -> UNC path)
    for unc_path, mapped_drive in mappings.items():
        drive_key = mapped_drive.rstrip('\\')
        reverse_mappings[drive_key.upper()] = unc_path
    
    # Look up the drive letter
    drive_key = drive_letter.upper().rstrip('\\')
    if drive_key in reverse_mappings:
        return reverse_mappings[drive_key]
    
    # If not found in our mappings, try using net use as fallback
    try:
        output = subprocess.check_output(['net', 'use', drive_letter], text=True, stderr=subprocess.STDOUT)
        
        # Look for the remote name in the output
        # Using raw string for regex pattern to fix escape sequences
        match = re.search(r'Remote name\s+(\\\\[^\s]+)', output, re.IGNORECASE)
        if match:
            return match.group(1)
    except Exception as e:
        logger.debug(f"Failed to get network target with 'net use' for {drive_letter}: {e}")
    
    # If all else fails, return None
    return None

def get_path_type(path: Union[str, Path]) -> str:
    """
    Determine the type of a path.
    
    Args:
        path: The path to check.
        
    Returns:
        A string indicating the path type:
        - 'unc': UNC path (\\server\share)
        - 'network': Path on a network drive
        - 'subst': Path on a substituted drive
        - 'local': Path on a local fixed drive
        - 'removable': Path on a removable drive
        - 'cdrom': Path on a CD-ROM drive
        - 'ramdisk': Path on a RAM disk
        - 'unknown': Unknown or could not determine
    """
    path_str = str(path).replace('/', '\\')
    
    # Check cache
    cache_key = f"type_{path_str}"
    if cache_key in _path_type_cache:
        return _path_type_cache[cache_key]
    
    # Check if it's a UNC path
    if is_unc_path(path_str):
        result = PATH_TYPE_UNC
    else:
        # Extract drive letter
        match = re.match(r'^([A-Za-z]:)', path_str)
        if not match:
            result = PATH_TYPE_UNKNOWN
        else:
            drive_letter = match.group(1)
            result = get_drive_type(drive_letter)
    
    # Cache the result
    _path_type_cache[cache_key] = result
    
    return result

def detect_path_issues(path: Union[str, Path]) -> List[str]:
    """
    Detect potential issues with a path.
    
    Args:
        path: The path to check.
        
    Returns:
        A list of potential issues with the path, or an empty list if no issues were found.
    """
    issues = []
    path_str = str(path)
    path_type = get_path_type(path_str)
    
    # Check if the path is too long for Windows
    if IS_WINDOWS and len(path_str) > 260 and not path_str.startswith('\\\\?\\'):
        issues.append("Path exceeds Windows MAX_PATH limit (260 characters)")
    
    # Check UNC paths
    if path_type == PATH_TYPE_UNC:
        # Check for no server or share name
        if not re.match(r'\\\\[^\\]+\\[^\\]+', path_str):
            issues.append("Invalid UNC path: missing server or share name")
        
        # Check for potential security zone issues on Windows
        if IS_WINDOWS:
            match = re.match(r'\\\\([^\\]+)', path_str)
            if match:
                server = match.group(1)
                if not is_server_in_intranet_zone(server):
                    issues.append(f"UNC server '{server}' is not in the Intranet security zone")
    
    # Check network drive paths
    elif path_type == PATH_TYPE_NETWORK:
        drive_match = re.match(r'^([A-Za-z]:)', path_str)
        if drive_match:
            drive = drive_match.group(1)
            if get_network_target(drive) is None:
                issues.append(f"Network drive {drive} has no detectable UNC target")
    
    # Check subst drive paths
    elif path_type == PATH_TYPE_SUBST:
        drive_match = re.match(r'^([A-Za-z]:)', path_str)
        if drive_match:
            drive = drive_match.group(1)
            target = get_subst_target(drive)
            if target is None:
                issues.append(f"Substituted drive {drive} has no detectable target")
            elif not os.path.exists(target):
                issues.append(f"Substituted drive {drive} points to non-existent target: {target}")
    
    return issues

def get_network_mappings() -> Dict[str, str]:
    """
    Get all network drive mappings.
    
    Returns:
        A dictionary mapping drive letters to UNC paths.
    """
    if not IS_WINDOWS:
        return {}
    
    try:
        mappings = {}
        reverse_mappings = get_mappings()
        
        # Invert the mapping (UNC -> drive becomes drive -> UNC)
        for unc_path, drive in reverse_mappings.items():
            drive_key = drive.rstrip('\\')
            mappings[drive_key] = unc_path
        
        return mappings
    except Exception as e:
        logger.warning(f"Failed to get network mappings: {e}")
        return {}

def is_server_in_intranet_zone(server: str) -> bool:
    """
    Check if a server is in the local intranet security zone.
    
    Args:
        server: The server name to check.
        
    Returns:
        True if the server is in the intranet zone, False otherwise.
    """
    # Only applicable to Windows
    if not IS_WINDOWS:
        return False
    
    try:
        import winreg
        
        # Check the registry key for the server in the intranet zone
        zone_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings\ZoneMap\Domains"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, zone_path + "\\" + server) as key:
                # Check if any entry exists for this server
                try:
                    value, _ = winreg.QueryValueEx(key, "*")
                    # Value 1 is Local Intranet zone
                    return value == 1
                except FileNotFoundError:
                    pass
                
                # Check numbered subdomains
                i = 0
                while True:
                    try:
                        value, _ = winreg.QueryValueEx(key, str(i))
                        if value == 1:
                            return True
                        i += 1
                    except FileNotFoundError:
                        break
        except FileNotFoundError:
            pass
        
        # Check Ranges key
        ranges_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings\ZoneMap\Ranges"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ranges_path) as ranges_key:
                # Iterate through the range entries
                i = 0
                while True:
                    try:
                        range_name = winreg.EnumKey(ranges_key, i)
                        with winreg.OpenKey(ranges_key, range_name) as range_key:
                            try:
                                value, _ = winreg.QueryValueEx(range_key, ":Range")
                                if value == 1:  # Local Intranet zone
                                    # Check if server is in this range
                                    try:
                                        server_value, _ = winreg.QueryValueEx(range_key, "http")
                                        if server.lower() in server_value.lower():
                                            return True
                                    except FileNotFoundError:
                                        pass
                            except FileNotFoundError:
                                pass
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            pass
        
        return False
    except Exception as e:
        logger.warning(f"Failed to check if server {server} is in intranet zone: {e}")
        return False