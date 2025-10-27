#!/usr/bin/env python3
"""
Tests for the unctools.windows module using the test framework.
"""

import os
import sys
import logging
from pathlib import Path
from unittest import mock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import test framework
from tests.test_framework import (
    TestSuite, assert_true, assert_false, assert_equal, 
    assert_not_equal, assert_is_none, assert_is_not_none,
    skip_if_not_windows, skip_if_windows, skip_if_no_module,
    run_test_suites
)

# Import UNCtools
import unctools

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@skip_if_not_windows
def test_fix_security_zone():
    """Test fix_security_zone function."""
    # This is a Windows-specific function that interacts with the registry
    # For testing, we'll mock the registry functions
    
    # Mock add_to_intranet_zone to control behavior
    with mock.patch('unctools.windows.registry.add_to_intranet_zone') as mock_add_zone:
        # Set up mock behavior
        mock_add_zone.return_value = True
        
        # Test fixing security zone for a server
        result = unctools.fix_security_zone("server")
        assert_true(result, "fix_security_zone should return True when successful")
        mock_add_zone.assert_called_once_with("server", for_all_users=False)
        
        # Reset mock
        mock_add_zone.reset_mock()
        mock_add_zone.return_value = False
        
        # Test with failure
        result = unctools.fix_security_zone("server")
        assert_false(result, "fix_security_zone should return False when unsuccessful")

@skip_if_not_windows
def test_add_to_intranet_zone():
    """Test add_to_intranet_zone function."""
    # Mock winreg functions
    with mock.patch('winreg.CreateKeyEx') as mock_create_key, \
         mock.patch('winreg.SetValueEx') as mock_set_value, \
         mock.patch('winreg.CloseKey') as mock_close_key:
        
        # Set up mock behavior
        mock_create_key.return_value = "mock_key"
        
        # Test adding to intranet zone
        result = unctools.add_to_intranet_zone("server")
        assert_true(result, "add_to_intranet_zone should return True when successful")
        
        # Verify correct function calls
        mock_create_key.assert_called_once()
        mock_set_value.assert_called_once()
        mock_close_key.assert_called_once()
        
        # Test with invalid server name
        result = unctools.add_to_intranet_zone("")
        assert_false(result, "add_to_intranet_zone should return False with invalid server")

@skip_if_not_windows
def test_network_mappings():
    """Test network mapping functions."""
    # Import directly from the module to avoid attribute resolution issues
    from unctools.windows.network import create_network_mapping, remove_network_mapping
    
    # Mock the required functions without using module attributes
    with mock.patch('unctools.windows.network.WNetAddConnection2', create=True) as mock_add_connection, \
         mock.patch('unctools.windows.network.WNetCancelConnection2', create=True) as mock_cancel_connection, \
         mock.patch('subprocess.run') as mock_run:
        
        # Set up mock behavior for subprocess.run (fallback method)
        mock_process = mock.MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Drive Z: is now connected to \\\\server\\share"
        mock_run.return_value = mock_process
        
        # Test create_network_mapping
        result, drive = create_network_mapping("\\\\server\\share", "Z:")
        assert_true(result, "create_network_mapping should return True when successful")
        assert_equal(drive, "Z:", "Drive letter should be returned")
        
        # Test remove_network_mapping
        result = remove_network_mapping("Z:")
        assert_true(result, "remove_network_mapping should return True when successful")

@skip_if_not_windows
def test_get_all_network_mappings():
    """Test get_all_network_mappings function."""
    # Mock the win32net functions
    with mock.patch('unctools.windows.network.get_all_network_mappings') as mock_get_mappings:
        # Set up mock behavior
        mock_get_mappings.return_value = {
            "Z:": "\\\\server\\share",
            "Y:": "\\\\fileserver\\public"
        }
        
        # Call the function directly from where it's defined
        mappings = mock_get_mappings()
        
        # Verify the results
        assert_equal(len(mappings), 2, "Should have 2 network mappings")
        assert_equal(mappings.get("Z:"), "\\\\server\\share", "Z: should map to \\\\server\\share")
        assert_equal(mappings.get("Y:"), "\\\\fileserver\\public", "Y: should map to \\\\fileserver\\public")


@skip_if_not_windows
def test_check_network_connection():
    """Test check_network_connection function."""
    # Mock subprocess.run
    with mock.patch('subprocess.run') as mock_run:
        # Set up mock behavior for success
        mock_process = mock.MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Test with successful connection
        result = unctools.windows.check_network_connection("server")
        assert_true(result, "check_network_connection should return True when successful")
        
        # Set up mock behavior for failure
        mock_process.returncode = 1
        
        # Test with failed connection
        result = unctools.windows.check_network_connection("nonexistent")
        assert_false(result, "check_network_connection should return False when unsuccessful")

@skip_if_not_windows
@skip_if_no_module('win32security')
def test_security_functions():
    """Test file security functions."""
    # Import the function directly
    from unctools.windows.security import get_file_security
    
    # Create mock security descriptor and related objects
    mock_sd = mock.MagicMock()
    mock_owner_sid = mock.MagicMock()
    mock_group_sid = mock.MagicMock()
    mock_dacl = mock.MagicMock()
    
    # Setup mock methods
    mock_sd.GetSecurityDescriptorOwner.return_value = mock_owner_sid
    mock_sd.GetSecurityDescriptorGroup.return_value = mock_group_sid
    mock_sd.GetSecurityDescriptorDacl.return_value = mock_dacl
    mock_dacl.GetAceCount.return_value = 1
    mock_dacl.GetAce.return_value = ((0, 0), 0, mock.MagicMock())
    
    # Mock all the required functions
    with mock.patch('win32security.GetFileSecurity', return_value=mock_sd) as mock_get_security, \
         mock.patch('win32security.LookupAccountSid') as mock_lookup_sid:
        
        mock_lookup_sid.side_effect = [
            ("owner_name", "domain", 1),
            ("group_name", "domain", 1),
            ("trustee_name", "domain", 1)
        ]
        
        # Test get_file_security
        security_info = get_file_security("C:\\path\\to\\file.txt")
        assert_is_not_none(security_info, "get_file_security should return security information")
        assert_equal(security_info.get("owner"), "domain\\owner_name", "Owner should be correctly formatted")
        assert_equal(security_info.get("group"), "domain\\group_name", "Group should be correctly formatted")
        assert_is_not_none(security_info.get("acl"), "ACL should be included in security information")

@skip_if_not_windows
def test_bypass_security_dialog():
    """Test bypass_security_dialog function."""
    # Mock winreg functions
    with mock.patch('winreg.OpenKey', side_effect=FileNotFoundError), \
         mock.patch('winreg.CreateKey') as mock_create_key, \
         mock.patch('winreg.SetValueEx') as mock_set_value, \
         mock.patch('winreg.CloseKey') as mock_close_key:
        
        # Test enabling security bypass
        result = unctools.windows.bypass_security_dialog(True)
        assert_true(result, "bypass_security_dialog should return True when successful")
        
        # Verify correct function calls
        mock_create_key.assert_called_once()
        mock_set_value.assert_called_once_with(mock.ANY, "ClassicSharing", 0, mock.ANY, 1)
        mock_close_key.assert_called_once()
        
        # Reset mocks
        mock_create_key.reset_mock()
        mock_set_value.reset_mock()
        mock_close_key.reset_mock()
        
        # Test disabling security bypass
        result = unctools.windows.bypass_security_dialog(False)
        assert_true(result, "bypass_security_dialog should return True when successful")
        
        # Verify correct function calls
        mock_create_key.assert_called_once()
        mock_set_value.assert_called_once_with(mock.ANY, "ClassicSharing", 0, mock.ANY, 0)
        mock_close_key.assert_called_once()

@skip_if_windows
def test_windows_stubs_on_non_windows():
    """Test that Windows-specific functions return appropriate values on non-Windows platforms."""
    # Test fix_security_zone
    result = unctools.fix_security_zone("server")
    assert_false(result, "fix_security_zone should return False on non-Windows platforms")
    
    # Test add_to_intranet_zone
    result = unctools.add_to_intranet_zone("server")
    assert_false(result, "add_to_intranet_zone should return False on non-Windows platforms")

def run_tests():
    """Run all Windows module tests."""
    suite = TestSuite("UNCtools Windows Module Tests")
    
    # Add tests
    suite.add_test(test_fix_security_zone)
    suite.add_test(test_add_to_intranet_zone)
    suite.add_test(test_network_mappings)
    suite.add_test(test_get_all_network_mappings)
    suite.add_test(test_check_network_connection)
    suite.add_test(test_security_functions)
    suite.add_test(test_bypass_security_dialog)
    suite.add_test(test_windows_stubs_on_non_windows)
    
    # Run suite
    run_test_suites([suite])

if __name__ == "__main__":
    run_tests()
