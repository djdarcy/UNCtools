"""
Windows network utilities for managing network drives and connections.

This module provides functions for working with Windows network drives,
including creating and removing network mappings, checking network connectivity,
and managing network shares.
"""

import os
import re
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

# Set up module-level logger
logger = logging.getLogger(__name__)

# Check if we're running on Windows
IS_WINDOWS = os.name == 'nt'

# Try to import Windows-specific modules
if IS_WINDOWS:
    try:
        import win32net
        import win32wnet
        import win32api
        import win32con
        import win32netcon
        from win32file import WNetAddConnection2, WNetCancelConnection2
        HAVE_WIN32NET = True
    except ImportError:
        HAVE_WIN32NET = False
        logger.debug("win32net module not available. Using command-line fallbacks for network operations.")
else:
    HAVE_WIN32NET = False

def create_network_mapping(unc_path: str, drive_letter: Optional[str] = None, 
                         username: Optional[str] = None, password: Optional[str] = None,
                         persistent: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Create a network drive mapping for a UNC path.
    
    Args:
        unc_path: The UNC path to map (e.g., \\\\server\\share).
        drive_letter: The drive letter to map to (e.g., "Z:").
                      If None, Windows will assign the next available drive.
        username: The username for authentication (optional).
        password: The password for authentication (optional).
        persistent: Whether the mapping should persist across reboots.
    
    Returns:
        A tuple of (success, drive_letter), where success is a boolean indicating
        whether the operation was successful, and drive_letter is the assigned
        drive letter (which may be different from the requested one if automatic
        assignment was used).
    """
    if not IS_WINDOWS:
        logger.warning("Network mappings are only available on Windows.")
        return (False, None)
    
    # Normalize UNC path
    unc_path = unc_path.replace('/', '\\')
    if not unc_path.startswith('\\\\'):
        unc_path = '\\\\' + unc_path.lstrip('\\')
    
    # Normalize drive letter if provided
    if drive_letter:
        drive_letter = drive_letter.upper()
        if not drive_letter.endswith(':'):
            drive_letter += ':'
    
    # Try to use the Windows API if available
    if HAVE_WIN32NET:
        try:
            # Create a network resource object
            netresource = {
                'Provider': None,
                'Flags': 0,
                'LocalName': drive_letter if drive_letter else None,
                'RemoteName': unc_path
            }
            
            # Attempt to add the connection
            try:
                WNetAddConnection2(netresource, password, username, win32con.CONNECT_UPDATE_PROFILE if persistent else 0)
                
                # If we didn't specify a drive letter, we need to find out what was assigned
                if not drive_letter:
                    # Enumerate network drives to find our newly created one
                    connections, _, _ = win32net.NetUseEnum(None, 2)
                    for conn in connections:
                        if conn.get('remote', '').lower() == unc_path.lower():
                            drive_letter = conn.get('local', '').upper()
                            break
                
                logger.info(f"Successfully mapped {unc_path} to {drive_letter}")
                return (True, drive_letter)
            except win32api.error as e:
                logger.error(f"Failed to map network drive using WNetAddConnection2: {e}")
                # Fall back to net use command
                pass
        except Exception as e:
            logger.error(f"Error using Windows API for network mapping: {e}")
            # Fall back to net use command
    
    # Fall back to using the net use command
    cmd = ['net', 'use']
    
    # Add drive letter if specified
    if drive_letter:
        cmd.append(drive_letter)
    
    # Add UNC path
    cmd.append(unc_path)
    
    # Add password if specified
    if password:
        cmd.append(password)
    
    # Add persistence flag
    if persistent:
        cmd.append('/PERSISTENT:YES')
    else:
        cmd.append('/PERSISTENT:NO')
    
    # Add username if specified
    if username:
        cmd.append(f'/USER:{username}')
    
    try:
        # Execute the command
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        
        if result.returncode == 0:
            # Command succeeded, parse output to find drive letter if not specified
            if not drive_letter:
                # Try to extract from output - "Drive Z: is now connected to \\server\share"
                match = re.search(r'Drive ([A-Z]:)', result.stdout)
                if match:
                    drive_letter = match.group(1)
            
            logger.info(f"Successfully mapped {unc_path} to {drive_letter}")
            return (True, drive_letter)
        else:
            logger.error(f"Failed to map network drive: {result.stderr}")
            return (False, None)
    except Exception as e:
        logger.error(f"Error executing net use command: {e}")
        return (False, None)

def remove_network_mapping(drive_letter: str, force: bool = False) -> bool:
    """
    Remove a network drive mapping.
    
    Args:
        drive_letter: The drive letter to remove (e.g., "Z:").
        force: Whether to force disconnection even if the drive is in use.
    
    Returns:
        True if the operation was successful, False otherwise.
    """
    if not IS_WINDOWS:
        logger.warning("Network mappings are only available on Windows.")
        return False
    
    # Normalize drive letter
    drive_letter = drive_letter.upper()
    if not drive_letter.endswith(':'):
        drive_letter += ':'
    
    # Try to use the Windows API if available
    if HAVE_WIN32NET:
        try:
            # Attempt to cancel the connection
            WNetCancelConnection2(drive_letter, win32con.CONNECT_UPDATE_PROFILE, force)
            logger.info(f"Successfully removed network mapping for {drive_letter}")
            return True
        except win32api.error as e:
            logger.warning(f"Failed to remove network mapping using WNetCancelConnection2: {e}")
            # Fall back to net use command
    
    # Fall back to using the net use command
    cmd = ['net', 'use', drive_letter, '/DELETE']
    
    if force:
        cmd.append('/Y')
    
    try:
        # Execute the command
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        
        if result.returncode == 0:
            logger.info(f"Successfully removed network mapping for {drive_letter}")
            return True
        else:
            logger.error(f"Failed to remove network mapping: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error executing net use command: {e}")
        return False

def get_all_network_mappings() -> Dict[str, str]:
    """
    Get all network drive mappings.
    
    Returns:
        A dictionary mapping drive letters to UNC paths.
    """
    if not IS_WINDOWS:
        logger.warning("Network mappings are only available on Windows.")
        return {}
    
    mappings = {}
    
    # Try to use the Windows API if available
    if HAVE_WIN32NET:
        try:
            # Enumerate network connections
            connections, _, _ = win32net.NetUseEnum(None, 2)
            
            for conn in connections:
                local = conn.get('local', '')
                remote = conn.get('remote', '')
                
                if local and remote:
                    mappings[local.upper()] = remote
            
            return mappings
        except Exception as e:
            logger.warning(f"Failed to enumerate network mappings using NetUseEnum: {e}")
            # Fall back to net use command
    
    # Fall back to using the net use command
    try:
        result = subprocess.run(['net', 'use'], text=True, capture_output=True, check=False)
        
        if result.returncode == 0:
            # Parse the output to extract mappings
            for line in result.stdout.splitlines():
                # Look for lines like "OK Z: \\server\share"
                match = re.search(r'(OK|Disconnected)\s+([A-Za-z]:)\s+(\\\\\S+)', line, re.IGNORECASE)
                if match:
                    drive_letter = match.group(2).upper()
                    unc_path = match.group(3)
                    mappings[drive_letter] = unc_path
            
            return mappings
        else:
            logger.error(f"Failed to enumerate network mappings: {result.stderr}")
            return {}
    except Exception as e:
        logger.error(f"Error executing net use command: {e}")
        return {}

def check_network_connection(server: str, timeout: int = 5) -> bool:
    """
    Check if a network server is reachable.
    
    Args:
        server: The server name or IP address to check.
        timeout: The timeout in seconds.
    
    Returns:
        True if the server is reachable, False otherwise.
    """
    if not IS_WINDOWS:
        # On non-Windows platforms, try ping
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', str(timeout), server], 
                                   text=True, capture_output=True, check=False)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error executing ping command: {e}")
            return False
    
    # On Windows, try ping with Windows-specific arguments
    try:
        result = subprocess.run(['ping', '-n', '1', '-w', str(timeout * 1000), server], 
                               text=True, capture_output=True, check=False)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error executing ping command: {e}")
        return False

def get_server_shares(server: str, username: Optional[str] = None, 
                     password: Optional[str] = None) -> List[str]:
    """
    Get a list of shares available on a server.
    
    Args:
        server: The server name.
        username: The username for authentication (optional).
        password: The password for authentication (optional).
    
    Returns:
        A list of share names.
    """
    if not IS_WINDOWS:
        logger.warning("Network share enumeration is only available on Windows.")
        return []
    
    shares = []
    
    # Try to use the Windows API if available
    if HAVE_WIN32NET:
        try:
            # Build server UNC path
            server_unc = '\\\\' + server.strip('\\')
            
            # Set up authentication if provided
            if username and password:
                try:
                    # Use NetUseAdd to create a temporary connection
                    use_info = {
                        'remote': server_unc,
                        'password': password,
                        'username': username
                    }
                    win32net.NetUseAdd(None, 2, use_info)
                    
                    # Clean up when we're done
                    temp_connection_added = True
                except Exception as e:
                    logger.warning(f"Failed to create temporary connection: {e}")
                    temp_connection_added = False
            else:
                temp_connection_added = False
            
            try:
                # Enumerate shares
                share_info, _, _ = win32net.NetShareEnum(server, 1)
                
                for share in share_info:
                    share_name = share.get('netname', '')
                    if share_name and not share_name.endswith('$'):  # Exclude hidden shares
                        shares.append(share_name)
            finally:
                # Clean up temporary connection if we created one
                if temp_connection_added:
                    try:
                        win32net.NetUseDel(None, server_unc)
                    except:
                        pass
            
            return shares
        except Exception as e:
            logger.warning(f"Failed to enumerate shares using NetShareEnum: {e}")
            # Fall back to net view command
    
    # Fall back to using the net view command
    cmd = ['net', 'view', '\\\\' + server.strip('\\')]
    
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        
        if result.returncode == 0:
            # Parse the output to extract share names
            for line in result.stdout.splitlines():
                # Look for lines with share names
                match = re.search(r'(\S+)\s+Disk\s+', line, re.IGNORECASE)
                if match:
                    share_name = match.group(1)
                    if not share_name.endswith('$'):  # Exclude hidden shares
                        shares.append(share_name)
            
            return shares
        else:
            logger.error(f"Failed to enumerate shares: {result.stderr}")
            return []
    except Exception as e:
        logger.error(f"Error executing net view command: {e}")
        return []

def create_share(path: str, share_name: str, description: str = "", 
                max_users: int = -1, full_access_users: List[str] = None) -> bool:
    """
    Create a network share on the local machine.
    
    Args:
        path: The local path to share.
        share_name: The name of the share.
        description: A description of the share.
        max_users: Maximum number of concurrent users (-1 for unlimited).
        full_access_users: List of users to grant full access to.
    
    Returns:
        True if the operation was successful, False otherwise.
    """
    if not IS_WINDOWS:
        logger.warning("Network share creation is only available on Windows.")
        return False
    
    # Check if path exists
    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return False
    
    # Try to use the Windows API if available
    if HAVE_WIN32NET:
        try:
            # Create the share
            share_info = {
                'netname': share_name,
                'path': os.path.abspath(path),
                'remark': description,
                'max_uses': max_users,
                'type': win32netcon.STYPE_DISKTREE,
                'permissions': 0
            }
            
            win32net.NetShareAdd(None, 2, share_info)
            
            # Set permissions if requested
            if full_access_users:
                for user in full_access_users:
                    # Add permission setting code here
                    # This requires more complex Windows API calls
                    pass
            
            logger.info(f"Successfully created share {share_name} for {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create share using NetShareAdd: {e}")
            # Fall back to net share command
    
    # Fall back to using the net share command
    cmd = ['net', 'share', share_name + '=' + os.path.abspath(path)]
    
    if description:
        cmd.extend(['/REMARK:', description])
    
    if max_users >= 0:
        cmd.extend(['/USERS:', str(max_users)])
    
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        
        if result.returncode == 0:
            logger.info(f"Successfully created share {share_name} for {path}")
            
            # Additional commands would be needed to set permissions
            
            return True
        else:
            logger.error(f"Failed to create share: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error executing net share command: {e}")
        return False

def remove_share(share_name: str) -> bool:
    """
    Remove a network share from the local machine.
    
    Args:
        share_name: The name of the share to remove.
    
    Returns:
        True if the operation was successful, False otherwise.
    """
    if not IS_WINDOWS:
        logger.warning("Network share removal is only available on Windows.")
        return False
    
    # Try to use the Windows API if available
    if HAVE_WIN32NET:
        try:
            win32net.NetShareDel(None, share_name)
            logger.info(f"Successfully removed share {share_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove share using NetShareDel: {e}")
            # Fall back to net share command
    
    # Fall back to using the net share command
    cmd = ['net', 'share', share_name, '/DELETE']
    
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        
        if result.returncode == 0:
            logger.info(f"Successfully removed share {share_name}")
            return True
        else:
            logger.error(f"Failed to remove share: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error executing net share command: {e}")
        return False