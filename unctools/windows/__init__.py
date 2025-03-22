"""
Windows-specific utilities for UNC paths, network drives, and security zones.

This subpackage contains Windows-specific functionality for working with UNC paths,
network mappings, security zones, and registry operations.
"""

import os
import logging

# Set up module-level logger
logger = logging.getLogger(__name__)

# Check if we're running on Windows
IS_WINDOWS = os.name == 'nt'

if not IS_WINDOWS:
    logger.warning("The windows module is being imported on a non-Windows platform. Some functionality will not be available.")

# Import key functions for the package namespace
from .registry import add_to_intranet_zone, fix_security_zone
from .network import (
    create_network_mapping, remove_network_mapping, 
    get_all_network_mappings, check_network_connection
)
from .security import (
    get_file_security, set_file_permissions, 
    take_ownership, check_access_rights, 
    bypass_security_dialog
)

# For convenience, re-export these functions at the package level
__all__ = [
    'add_to_intranet_zone', 
    'fix_security_zone',
    'create_network_mapping', 
    'remove_network_mapping',
    'get_all_network_mappings',
    'check_network_connection',
    'get_file_security',
    'set_file_permissions',
    'take_ownership',
    'check_access_rights',
    'bypass_security_dialog'
] if we're running on Windows
IS_WINDOWS = os.name == 'nt'

if not IS_WINDOWS:
    logger.warning("The windows module is being imported on a non-Windows platform. Some functionality will not be available.")

# Import key functions for the package namespace
from .registry import add_to_intranet_zone, fix_security_zone
from .network import (
    create_network_mapping, remove_network_mapping, 
    get_all_network_mappings, check_network_connection
)

# For convenience, re-export these functions at the package level
__all__ = [
    'add_to_intranet_zone', 
    'fix_security_zone',
    'create_network_mapping', 
    'remove_network_mapping',
    'get_all_network_mappings',
    'check_network_connection'
]
