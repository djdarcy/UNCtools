"""
Windows registry utilities for managing security zones and network settings.

This module provides functions for working with the Windows registry,
particularly for managing security zones for UNC paths, which can help
resolve access issues with network shares.
"""

import os
import re
import logging
from typing import Optional, Dict, List, Tuple, Any, Union

# Set up module-level logger
logger = logging.getLogger(__name__)

# Check if we're running on Windows
IS_WINDOWS = os.name == 'nt'

# Try to import Windows-specific modules
if IS_WINDOWS:
    try:
        import winreg
        HAVE_WINREG = True
    except ImportError:
        HAVE_WINREG = False
        logger.warning("winreg module not available. Registry operations will not work.")
else:
    HAVE_WINREG = False

# Constants for Windows security zones
ZONE_LOCAL_INTRANET = 1
ZONE_TRUSTED_SITES = 2
ZONE_INTERNET = 3
ZONE_RESTRICTED_SITES = 4

# Registry paths
ZONEMAP_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings\ZoneMap"
DOMAINS_KEY_PATH = ZONEMAP_KEY_PATH + r"\Domains"
RANGES_KEY_PATH = ZONEMAP_KEY_PATH + r"\Ranges"

def _ensure_admin_access() -> bool:
    """
    Check if the script has administrative access to the Windows registry.
    
    Returns:
        True if the script has administrative access, False otherwise.
    """
    if not IS_WINDOWS:
        return False
        
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        # If we can't check, assume we don't have admin access
        return False

def add_to_intranet_zone(server_name: str, for_all_users: bool = False) -> bool:
    """
    Add a server to the Local Intranet security zone.
    
    This can help resolve access issues with UNC paths by lowering the security
    restrictions for the specified server.
    
    Args:
        server_name: The name of the server to add to the zone.
        for_all_users: If True, attempt to add the server to the zone for all users.
                      This requires administrative privileges.
    
    Returns:
        True if the server was successfully added to the zone, False otherwise.
    """
    if not IS_WINDOWS or not HAVE_WINREG:
        logger.warning("Registry operations are only available on Windows.")
        return False
    
    # Validate server name
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*$', server_name):
        logger.error(f"Invalid server name: {server_name}")
        return False
    
    # Check if for_all_users requires admin access
    if for_all_users and not _ensure_admin_access():
        logger.warning("Administrative access required to add zone for all users.")
        for_all_users = False
    
    # Determine which registry hive to use
    if for_all_users:
        root_key = winreg.HKEY_LOCAL_MACHINE
        logger.info(f"Adding {server_name} to Local Intranet zone for all users")
    else:
        root_key = winreg.HKEY_CURRENT_USER
        logger.info(f"Adding {server_name} to Local Intranet zone for current user")
    
    try:
        # Create or open the domain key
        domain_path = DOMAINS_KEY_PATH + "\\" + server_name
        
        try:
            # Try to create the key
            domain_key = winreg.CreateKeyEx(root_key, domain_path, 0, winreg.KEY_WRITE)
        except PermissionError:
            logger.error(f"Permission denied accessing registry key: {domain_path}")
            return False
        
        try:
            # Set the "*" value to Local Intranet zone (1)
            winreg.SetValueEx(domain_key, "*", 0, winreg.REG_DWORD, ZONE_LOCAL_INTRANET)
            logger.info(f"Added {server_name} to Local Intranet zone successfully.")
            success = True
        except Exception as e:
            logger.error(f"Failed to add {server_name} to zone: {e}")
            success = False
            
        # Close the key
        winreg.CloseKey(domain_key)
        
        return success
    except Exception as e:
        logger.error(f"Failed to add {server_name} to Local Intranet zone: {e}")
        return False

def remove_from_zone(server_name: str, for_all_users: bool = False) -> bool:
    """
    Remove a server from any security zone.
    
    Args:
        server_name: The name of the server to remove from zones.
        for_all_users: If True, attempt to remove the server from zones for all users.
                      This requires administrative privileges.
    
    Returns:
        True if the server was successfully removed, False otherwise.
    """
    if not IS_WINDOWS or not HAVE_WINREG:
        logger.warning("Registry operations are only available on Windows.")
        return False
    
    # Check if for_all_users requires admin access
    if for_all_users and not _ensure_admin_access():
        logger.warning("Administrative access required to remove zone for all users.")
        for_all_users = False
    
    # Determine which registry hive to use
    if for_all_users:
        root_key = winreg.HKEY_LOCAL_MACHINE
        logger.info(f"Removing {server_name} from security zones for all users")
    else:
        root_key = winreg.HKEY_CURRENT_USER
        logger.info(f"Removing {server_name} from security zones for current user")
    
    try:
        # Check if the key exists
        domain_path = DOMAINS_KEY_PATH + "\\" + server_name
        
        try:
            # Try to open the key
            try:
                domain_key = winreg.OpenKey(root_key, domain_path, 0, winreg.KEY_READ)
                # Close right away, we just want to see if it exists
                winreg.CloseKey(domain_key)
            except FileNotFoundError:
                logger.info(f"Server {server_name} not found in any zone.")
                return True  # Already not in a zone
                
            # Delete the key
            try:
                winreg.DeleteKey(root_key, domain_path)
                logger.info(f"Removed {server_name} from security zones successfully.")
                return True
            except Exception as e:
                logger.error(f"Failed to remove {server_name} from zones: {e}")
                return False
        except PermissionError:
            logger.error(f"Permission denied accessing registry key: {domain_path}")
            return False
    except Exception as e:
        logger.error(f"Failed to remove {server_name} from zones: {e}")
        return False

def check_zone(server_name: str) -> Optional[int]:
    """
    Check which security zone a server is in.
    
    Args:
        server_name: The name of the server to check.
    
    Returns:
        The zone number if found, or None if the server is not in any zone.
        Zone numbers:
            1: Local Intranet
            2: Trusted Sites
            3: Internet
            4: Restricted Sites
    """
    if not IS_WINDOWS or not HAVE_WINREG:
        logger.warning("Registry operations are only available on Windows.")
        return None
    
    try:
        # Check current user settings first
        domain_path = DOMAINS_KEY_PATH + "\\" + server_name
        
        try:
            # Try to open the key
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, domain_path, 0, winreg.KEY_READ) as domain_key:
                try:
                    value, _ = winreg.QueryValueEx(domain_key, "*")
                    return value
                except FileNotFoundError:
                    # Check if there are any other entries
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(domain_key, i)
                            if name and value is not None:
                                return value
                            i += 1
                        except OSError:
                            break
        except FileNotFoundError:
            pass
        
        # If not found in current user, check all users (HKLM)
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, domain_path, 0, winreg.KEY_READ) as domain_key:
                try:
                    value, _ = winreg.QueryValueEx(domain_key, "*")
                    return value
                except FileNotFoundError:
                    # Check if there are any other entries
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(domain_key, i)
                            if name and value is not None:
                                return value
                            i += 1
                        except OSError:
                            break
        except (FileNotFoundError, PermissionError):
            pass
        
        # Not found in any zone
        return None
    except Exception as e:
        logger.error(f"Failed to check zone for {server_name}: {e}")
        return None

def fix_security_zone(server_name: str) -> bool:
    """
    Fix security zone issues for a server.
    
    This function adds the server to the Local Intranet zone, which can help
    resolve access issues with UNC paths.
    
    Args:
        server_name: The name of the server to fix.
        
    Returns:
        True if the fix was applied successfully, False otherwise.
    """
    # Check if the server is already in a zone
    current_zone = check_zone(server_name)
    
    if current_zone == ZONE_LOCAL_INTRANET:
        logger.info(f"Server {server_name} is already in the Local Intranet zone.")
        return True
    
    # Try to add to current user's zones first
    if add_to_intranet_zone(server_name, for_all_users=False):
        return True
    
    # If that fails and we have admin access, try for all users
    if _ensure_admin_access():
        return add_to_intranet_zone(server_name, for_all_users=True)
    
    return False

def get_all_zone_servers() -> Dict[str, int]:
    """
    Get all servers that are in security zones.
    
    Returns:
        A dictionary mapping server names to zone numbers.
    """
    if not IS_WINDOWS or not HAVE_WINREG:
        logger.warning("Registry operations are only available on Windows.")
        return {}
    
    servers = {}
    
    try:
        # Check HKCU first
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DOMAINS_KEY_PATH, 0, winreg.KEY_READ) as domains_key:
                i = 0
                while True:
                    try:
                        server = winreg.EnumKey(domains_key, i)
                        servers[server] = check_zone(server)
                        i += 1
                    except OSError:
                        break
        except (FileNotFoundError, PermissionError):
            pass
        
        # Then check HKLM if we have access
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, DOMAINS_KEY_PATH, 0, winreg.KEY_READ) as domains_key:
                i = 0
                while True:
                    try:
                        server = winreg.EnumKey(domains_key, i)
                        if server not in servers:  # Only add if not already found in HKCU
                            servers[server] = check_zone(server)
                        i += 1
                    except OSError:
                        break
        except (FileNotFoundError, PermissionError):
            pass
        
        return servers
    except Exception as e:
        logger.error(f"Failed to get all zone servers: {e}")
        return {}

def backup_zone_settings(backup_file: str) -> bool:
    """
    Backup all security zone settings to a file.
    
    Args:
        backup_file: The path to save the backup to.
        
    Returns:
        True if the backup was successful, False otherwise.
    """
    import json
    
    servers = get_all_zone_servers()
    
    if not servers:
        logger.warning("No zone settings found to backup.")
        return False
    
    try:
        with open(backup_file, 'w') as f:
            json.dump(servers, f, indent=2)
        logger.info(f"Backed up zone settings for {len(servers)} servers to {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to backup zone settings: {e}")
        return False

def restore_zone_settings(backup_file: str, for_all_users: bool = False) -> Tuple[int, int]:
    """
    Restore security zone settings from a backup file.
    
    Args:
        backup_file: The path to the backup file.
        for_all_users: If True, attempt to restore settings for all users.
                      This requires administrative privileges.
    
    Returns:
        A tuple of (success_count, failure_count) indicating how many servers
        were successfully restored and how many failed.
    """
    import json
    
    try:
        with open(backup_file, 'r') as f:
            servers = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read backup file {backup_file}: {e}")
        return (0, 0)
    
    success_count = 0
    failure_count = 0
    
    for server, zone in servers.items():
        try:
            # Remove from all zones first
            remove_from_zone(server)
            
            if zone == ZONE_LOCAL_INTRANET:
                if add_to_intranet_zone(server, for_all_users=for_all_users):
                    success_count += 1
                else:
                    failure_count += 1
            elif zone == ZONE_TRUSTED_SITES:
                # Add code to restore to trusted sites
                # Currently not implemented
                failure_count += 1
            elif zone == ZONE_INTERNET:
                # Add code to restore to internet zone
                # Currently not implemented
                failure_count += 1
            elif zone == ZONE_RESTRICTED_SITES:
                # Add code to restore to restricted sites
                # Currently not implemented
                failure_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logger.error(f"Failed to restore zone for {server}: {e}")
            failure_count += 1
    
    logger.info(f"Restored zone settings: {success_count} succeeded, {failure_count} failed")
    return (success_count, failure_count)
