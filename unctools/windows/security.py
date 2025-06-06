"""
Windows security utilities for UNC paths and network drives.

This module provides functions for handling Windows security aspects of UNC paths,
including access permissions, sharing options, and security token management.
"""

import os
import logging
import subprocess
from typing import Dict, List, Optional, Tuple, Union, Any

# Set up module-level logger
logger = logging.getLogger(__name__)

# Check if we're running on Windows
IS_WINDOWS = os.name == 'nt'

# Try to import Windows-specific modules
if IS_WINDOWS:
    try:
        import win32security
        import win32api
        import win32con
        import win32net
        import ntsecuritycon
        HAVE_WIN32SECURITY = True
    except ImportError:
        HAVE_WIN32SECURITY = False
        logger.warning("win32security module not available. Security operations will use limited functionality.")
else:
    HAVE_WIN32SECURITY = False

# Define or import constants for ACE types
if IS_WINDOWS and HAVE_WIN32SECURITY:
    # Use constants from win32security when available
    ACCESS_ALLOWED_ACE_TYPE = win32security.ACCESS_ALLOWED_ACE_TYPE
    ACCESS_DENIED_ACE_TYPE = win32security.ACCESS_DENIED_ACE_TYPE
    SYSTEM_AUDIT_ACE_TYPE = win32security.SYSTEM_AUDIT_ACE_TYPE
    
    # SYSTEM_ALARM_ACE_TYPE may not be available in all versions
    try:
        SYSTEM_ALARM_ACE_TYPE = win32security.SYSTEM_ALARM_ACE_TYPE
    except AttributeError:
        # Define fallback value based on Windows SDK
        SYSTEM_ALARM_ACE_TYPE = 3
        logger.debug("win32security.SYSTEM_ALARM_ACE_TYPE not available, using fallback value")
else:
    # Define fallback values for non-Windows or without win32security
    ACCESS_ALLOWED_ACE_TYPE = 0
    ACCESS_DENIED_ACE_TYPE = 1
    SYSTEM_AUDIT_ACE_TYPE = 2
    SYSTEM_ALARM_ACE_TYPE = 3

def get_file_security(path: str) -> Optional[Dict[str, Any]]:
    """
    Get security information for a file or directory.
    
    Args:
        path: The path to get security information for.
        
    Returns:
        A dictionary with security information, or None if not available.
    """
    if not IS_WINDOWS or not HAVE_WIN32SECURITY:
        logger.warning("Security information is only available on Windows with win32security.")
        return None
    
    try:
        # Get security descriptor
        sd = win32security.GetFileSecurity(
            path,
            win32security.OWNER_SECURITY_INFORMATION |
            win32security.GROUP_SECURITY_INFORMATION |
            win32security.DACL_SECURITY_INFORMATION
        )
        
        # Get owner, group, and DACL information
        owner_sid = sd.GetSecurityDescriptorOwner()
        group_sid = sd.GetSecurityDescriptorGroup()
        dacl = sd.GetSecurityDescriptorDacl()
        
        # Convert SIDs to names
        try:
            owner_name, domain, _ = win32security.LookupAccountSid(None, owner_sid)
            owner = f"{domain}\\{owner_name}"
        except:
            owner = str(owner_sid)
            
        try:
            group_name, domain, _ = win32security.LookupAccountSid(None, group_sid)
            group = f"{domain}\\{group_name}"
        except:
            group = str(group_sid)
        
        # Parse DACL
        acl_entries = []
        if dacl:
            for i in range(dacl.GetAceCount()):
                ace = dacl.GetAce(i)
                try:
                    trustee_sid = ace[2]
                    trustee_name, domain, _ = win32security.LookupAccountSid(None, trustee_sid)
                    trustee = f"{domain}\\{trustee_name}"
                except:
                    trustee = str(trustee_sid)
                    
                # Get access mask and type
                ace_type = ace[0][0]  # Type
                ace_flags = ace[0][1]  # Flags
                ace_mask = ace[1]  # Access mask
                
                acl_entries.append({
                    'trustee': trustee,
                    'type': _get_ace_type_name(ace_type),
                    'flags': _get_ace_flags(ace_flags),
                    'permissions': _get_permission_names(ace_mask)
                })
        
        return {
            'owner': owner,
            'group': group,
            'acl': acl_entries
        }
        
    except Exception as e:
        logger.error(f"Failed to get security information for {path}: {e}")
        return None

def _get_ace_type_name(ace_type: int) -> str:
    """
    Get a string representation of the ACE type.
    
    Args:
        ace_type: The ACE type value.
        
    Returns:
        A string describing the ACE type.
    """
    ace_types = {
        ACCESS_ALLOWED_ACE_TYPE: "Allow",
        ACCESS_DENIED_ACE_TYPE: "Deny",
        SYSTEM_AUDIT_ACE_TYPE: "Audit",
        SYSTEM_ALARM_ACE_TYPE: "Alarm"
    }
    return ace_types.get(ace_type, f"Unknown ({ace_type})")

def _get_ace_flags(ace_flags: int) -> List[str]:
    """
    Get a list of string representations of the ACE flags.
    
    Args:
        ace_flags: The ACE flags value.
        
    Returns:
        A list of strings describing the ACE flags.
    """
    flags = []
    if IS_WINDOWS and HAVE_WIN32SECURITY:
        if ace_flags & win32security.OBJECT_INHERIT_ACE:
            flags.append("Object Inherit")
        if ace_flags & win32security.CONTAINER_INHERIT_ACE:
            flags.append("Container Inherit")
        if ace_flags & win32security.NO_PROPAGATE_INHERIT_ACE:
            flags.append("No Propagate")
        if ace_flags & win32security.INHERIT_ONLY_ACE:
            flags.append("Inherit Only")
        if ace_flags & win32security.INHERITED_ACE:
            flags.append("Inherited")
    return flags

def _get_permission_names(access_mask: int) -> List[str]:
    """
    Get a list of string representations of the permissions.
    
    Args:
        access_mask: The access mask value.
        
    Returns:
        A list of strings describing the permissions.
    """
    permissions = []
    
    # Only try to decode permissions if we have the necessary module
    if IS_WINDOWS and HAVE_WIN32SECURITY:
        # File permissions
        if access_mask & ntsecuritycon.FILE_READ_DATA:
            permissions.append("Read")
        if access_mask & ntsecuritycon.FILE_WRITE_DATA:
            permissions.append("Write")
        if access_mask & ntsecuritycon.FILE_APPEND_DATA:
            permissions.append("Append")
        if access_mask & ntsecuritycon.FILE_EXECUTE:
            permissions.append("Execute")
        if access_mask & ntsecuritycon.DELETE:
            permissions.append("Delete")
        if access_mask & ntsecuritycon.READ_CONTROL:
            permissions.append("Read Permissions")
        if access_mask & ntsecuritycon.WRITE_DAC:
            permissions.append("Change Permissions")
        if access_mask & ntsecuritycon.WRITE_OWNER:
            permissions.append("Take Ownership")
        
        # Generic permissions
        if access_mask & ntsecuritycon.GENERIC_READ:
            permissions.append("Generic Read")
        if access_mask & ntsecuritycon.GENERIC_WRITE:
            permissions.append("Generic Write")
        if access_mask & ntsecuritycon.GENERIC_EXECUTE:
            permissions.append("Generic Execute")
        if access_mask & ntsecuritycon.GENERIC_ALL:
            permissions.append("Full Control")
    
    return permissions

def set_file_permissions(path: str, trustee: str, permissions: str, 
                        allow: bool = True) -> bool:
    """
    Set permissions on a file or directory.
    
    Args:
        path: The path to set permissions on.
        trustee: The user or group to set permissions for (e.g., "domain\\user").
        permissions: The permission to set ("read", "write", "execute", "full").
        allow: If True, grant the permissions; if False, deny them.
        
    Returns:
        True if successful, False otherwise.
    """
    if not IS_WINDOWS or not HAVE_WIN32SECURITY:
        logger.warning("Setting permissions is only available on Windows with win32security.")
        return False
    
    try:
        # Get security descriptor
        sd = win32security.GetFileSecurity(
            path, 
            win32security.DACL_SECURITY_INFORMATION
        )
        
        # Get existing DACL
        dacl = sd.GetSecurityDescriptorDacl()
        if dacl is None:
            dacl = win32security.ACL()
        
        # Determine access mask based on permissions
        access_mask = 0
        if permissions.lower() == "read":
            access_mask = ntsecuritycon.FILE_GENERIC_READ
        elif permissions.lower() == "write":
            access_mask = ntsecuritycon.FILE_GENERIC_WRITE
        elif permissions.lower() == "execute":
            access_mask = ntsecuritycon.FILE_GENERIC_EXECUTE
        elif permissions.lower() == "full":
            access_mask = ntsecuritycon.FILE_ALL_ACCESS
        else:
            logger.error(f"Unknown permission: {permissions}")
            return False
        
        # Convert trustee name to SID
        try:
            if "\\" in trustee:
                domain, user = trustee.split("\\", 1)
            else:
                domain, user = "", trustee
                
            trustee_sid, _, _ = win32security.LookupAccountName(None, trustee)
        except Exception as e:
            logger.error(f"Failed to look up SID for {trustee}: {e}")
            return False
        
        # Add ACE to DACL
        ace_type = ACCESS_ALLOWED_ACE_TYPE if allow else ACCESS_DENIED_ACE_TYPE
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, access_mask, trustee_sid)
        
        # Set new DACL
        sd.SetSecurityDescriptorDacl(1, dacl, 0)
        win32security.SetFileSecurity(
            path, 
            win32security.DACL_SECURITY_INFORMATION, 
            sd
        )
        
        logger.info(f"Set {permissions} permissions for {trustee} on {path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to set permissions on {path}: {e}")
        return False

def take_ownership(path: str) -> bool:
    """
    Take ownership of a file or directory.
    
    Args:
        path: The path to take ownership of.
        
    Returns:
        True if successful, False otherwise.
    """
    if not IS_WINDOWS:
        logger.warning("Taking ownership is only available on Windows.")
        return False
    
    # Try to use the Windows API if available
    if HAVE_WIN32SECURITY:
        try:
            # Get current process token
            token = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
            )
            
            # Enable SE_TAKE_OWNERSHIP_NAME privilege
            privilege_id = win32security.LookupPrivilegeValue(
                None, win32security.SE_TAKE_OWNERSHIP_NAME
            )
            win32security.AdjustTokenPrivileges(
                token, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
            )
            
            # Get current user SID
            user_sid = win32security.GetTokenInformation(
                token, win32security.TokenUser
            )[0]
            
            # Get security descriptor
            sd = win32security.GetFileSecurity(
                path, win32security.OWNER_SECURITY_INFORMATION
            )
            
            # Set new owner
            sd.SetSecurityDescriptorOwner(user_sid, 0)
            win32security.SetFileSecurity(
                path, win32security.OWNER_SECURITY_INFORMATION, sd
            )
            
            logger.info(f"Successfully took ownership of {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to take ownership using API: {e}")
            # Fall back to takeown command
    
    # Fall back to using the takeown command
    try:
        result = subprocess.run(
            ['takeown', '/f', path],
            text=True, capture_output=True, check=False
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully took ownership of {path} using takeown")
            return True
        else:
            logger.error(f"Failed to take ownership using takeown: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to take ownership: {e}")
        return False

def check_access_rights(path: str, desired_access: str = "read") -> bool:
    """
    Check if the current user has specific access rights to a path.
    
    Args:
        path: The path to check.
        desired_access: The type of access to check for ("read", "write", "execute", "full").
        
    Returns:
        True if the user has the requested access, False otherwise.
    """
    if not IS_WINDOWS:
        # On non-Windows platforms, use simpler checks
        if desired_access.lower() == "read":
            return os.access(path, os.R_OK)
        elif desired_access.lower() == "write":
            return os.access(path, os.W_OK)
        elif desired_access.lower() == "execute":
            return os.access(path, os.X_OK)
        elif desired_access.lower() == "full":
            return os.access(path, os.R_OK | os.W_OK | os.X_OK)
        else:
            logger.error(f"Unknown access type: {desired_access}")
            return False
    
    # Windows-specific checks
    if not HAVE_WIN32SECURITY:
        logger.warning("Detailed access checks require win32security.")
        # Fall back to simpler checks
        try:
            if desired_access.lower() == "read":
                # Try to open for reading
                with open(path, 'r'):
                    pass
                return True
            elif desired_access.lower() == "write":
                # Check if file exists and is writable, or if directory exists and we can create a temp file
                if os.path.isfile(path):
                    return os.access(path, os.W_OK)
                elif os.path.isdir(path):
                    try:
                        temp_file = os.path.join(path, "temp_access_check")
                        with open(temp_file, 'w'):
                            pass
                        os.remove(temp_file)
                        return True
                    except:
                        return False
                return False
            elif desired_access.lower() in ("execute", "full"):
                # These require more complex checks
                logger.warning("Detailed execute/full access check not available without win32security.")
                return False
            else:
                logger.error(f"Unknown access type: {desired_access}")
                return False
        except:
            return False
    
    # Use win32security for detailed checks
    try:
        # Map desired access to access mask
        if desired_access.lower() == "read":
            access_mask = ntsecuritycon.FILE_GENERIC_READ
        elif desired_access.lower() == "write":
            access_mask = ntsecuritycon.FILE_GENERIC_WRITE
        elif desired_access.lower() == "execute":
            access_mask = ntsecuritycon.FILE_GENERIC_EXECUTE
        elif desired_access.lower() == "full":
            access_mask = ntsecuritycon.FILE_ALL_ACCESS
        else:
            logger.error(f"Unknown access type: {desired_access}")
            return False
        
        # Check access
        if os.path.isdir(path):
            # For directories, we need to check directory-specific access
            handle = win32security.CreateFile(
                path,
                access_mask,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_FLAG_BACKUP_SEMANTICS,  # Required for directories
                0
            )
        else:
            # For files, use standard file access
            handle = win32security.CreateFile(
                path,
                access_mask,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                0,
                0
            )
        
        # If we got here, we have the requested access
        win32api.CloseHandle(handle)
        return True
        
    except win32api.error as e:
        # Access denied or other error
        logger.debug(f"Access check failed for {path} with {desired_access}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking access rights: {e}")
        return False

def get_unc_share_permissions(server: str, share: str) -> Optional[Dict[str, List[str]]]:
    """
    Get permissions for a network share.
    
    Args:
        server: The server name.
        share: The share name.
        
    Returns:
        A dictionary mapping users/groups to permission lists, or None if not available.
    """
    if not IS_WINDOWS or not HAVE_WIN32SECURITY:
        logger.warning("Share permissions are only available on Windows with win32security.")
        return None
    
    try:
        # Get share information
        server_unc = f"\\\\{server}"
        share_info, _, _ = win32net.NetShareGetInfo(server, share, 502)
        
        # Get share security descriptor
        sd = share_info['security_descriptor']
        if not sd:
            logger.warning(f"No security descriptor available for {server}\\{share}")
            return None
        
        # Parse permissions
        dacl = sd.GetSecurityDescriptorDacl()
        if not dacl:
            logger.warning(f"No DACL available for {server}\\{share}")
            return None
        
        permissions = {}
        for i in range(dacl.GetAceCount()):
            ace = dacl.GetAce(i)
            try:
                trustee_sid = ace[2]
                trustee_name, domain, _ = win32security.LookupAccountSid(None, trustee_sid)
                trustee = f"{domain}\\{trustee_name}"
            except:
                trustee = str(trustee_sid)
                
            # Get access type and mask
            ace_type = ace[0][0]  # Type
            ace_mask = ace[1]  # Access mask
            
            # Determine share permissions
            perm_list = []
            if ace_mask & win32netcon.ACCESS_READ:
                perm_list.append("Read")
            if ace_mask & win32netcon.ACCESS_WRITE:
                perm_list.append("Write")
            if ace_mask & win32netcon.ACCESS_CREATE:
                perm_list.append("Create")
            if ace_mask & win32netcon.ACCESS_EXEC:
                perm_list.append("Execute")
            if ace_mask & win32netcon.ACCESS_DELETE:
                perm_list.append("Delete")
            if ace_mask & win32netcon.ACCESS_ATRIB:
                perm_list.append("Change Attributes")
            if ace_mask & win32netcon.ACCESS_PERM:
                perm_list.append("Change Permissions")
            if ace_mask & win32netcon.ACCESS_ALL:
                perm_list = ["Full Control"]
            
            # Only include ALLOW aces (ignore DENY for now)
            if ace_type == ACCESS_ALLOWED_ACE_TYPE:
                permissions[trustee] = perm_list
        
        return permissions
        
    except Exception as e:
        logger.error(f"Failed to get share permissions for {server}\\{share}: {e}")
        return None

def bypass_security_dialog(enabled: bool = True) -> bool:
    """
    Enable or disable the security warning dialog for UNC paths.
    
    This modifies the registry to suppress security warnings when accessing UNC paths.
    
    Args:
        enabled: True to suppress warnings, False to restore default behavior.
        
    Returns:
        True if successful, False otherwise.
    """
    if not IS_WINDOWS:
        logger.warning("Registry modifications are only available on Windows.")
        return False
    
    try:
        import winreg
        
        # Registry key for UNC security
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Network"
        value_name = "ClassicSharing"
        
        # Open or create the key
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        except:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        
        # Set the value
        winreg.SetValueEx(key, value_name, 0, winreg.REG_DWORD, 1 if enabled else 0)
        winreg.CloseKey(key)
        
        logger.info(f"{'Enabled' if enabled else 'Disabled'} UNC security bypass")
        return True
        
    except Exception as e:
        logger.error(f"Failed to modify registry for UNC security bypass: {e}")
        return False
