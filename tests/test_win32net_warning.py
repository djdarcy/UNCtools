#!/usr/bin/env python3
"""
Test for win32net module warning issue.

This script specifically tests the win32net module import behavior
to ensure no unnecessary warnings are generated.
"""

import io
import os
import sys
import logging
import importlib
from pathlib import Path

# Set up the log capture
log_capture = io.StringIO()
handler = logging.StreamHandler(log_capture)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
handler.setFormatter(formatter)

# Get the unctools logger
logger = logging.getLogger("unctools")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 80}\n{title}\n{'=' * 80}")

def test_import_behavior():
    """Test the module import behavior for win32net warnings."""
    print_section("Testing win32net import behavior")
    
    # Clear any existing imports
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('unctools'):
            del sys.modules[module_name]
    
    # Import the core modules
    print("Importing unctools...")
    import unctools
    
    print("Importing converter module...")
    from unctools import converter
    
    print("Importing detector module...")
    from unctools import detector
    
    print("Importing operations module...")
    from unctools import operations
    
    # Get the log output
    log_output = log_capture.getvalue()
    
    # Check for warnings
    win32net_warnings = [line for line in log_output.splitlines() 
                        if "win32net" in line and "not available" in line]
    
    if win32net_warnings:
        print("\nWARNING: win32net warnings were detected:")
        for warning in win32net_warnings:
            print(f"  {warning}")
    else:
        print("\nSUCCESS: No win32net warnings were detected.")
    
    # Check HAVE_WIN32NET value
    print(f"\nHAVE_WIN32NET = {converter.HAVE_WIN32NET}")
    
    # Return True if no warnings, False otherwise
    return len(win32net_warnings) == 0

def check_module_availability():
    """Check which Windows modules are available."""
    print_section("Checking module availability")
    
    from unctools.utils.compat import is_module_available
    
    modules_to_check = [
        'win32net',
        'win32api',
        'win32security',
        'win32con',
        'win32file',
        'win32wnet',
        'ntsecuritycon',
        'winreg'
    ]
    
    # Check if pip is installed correctly
    try:
        import pip
        print(f"pip version: {pip.__version__}")
        
        # Get a list of installed packages
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                               capture_output=True, text=True)
        print("\nInstalled packages:")
        for line in result.stdout.splitlines():
            if any(module in line for module in ['pywin32', 'pypiwin32']):
                print(f"  {line}")
    except ImportError:
        print("pip not available")
    
    results = {}
    
    for module_name in modules_to_check:
        available = is_module_available(module_name)
        results[module_name] = available
        print(f"{module_name}: {'Available' if available else 'Not available'}")
        
        # If available, try to import it and get version
        if available:
            try:
                module = __import__(module_name)
                version = getattr(module, '__version__', 'Unknown')
                print(f"  Version: {version}")
            except ImportError:
                print(f"  Import failed despite being available")
    
    return results

def main():
    """Run all tests."""
    print_section("WIN32NET WARNING TEST")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Running on Windows: {os.name == 'nt'}")
    
    # Test module availability
    modules = check_module_availability()
    
    # Test import behavior
    warnings_fixed = test_import_behavior()
    
    # Save log output
    log_file = LOGS_DIR / "test_win32net_warning.log"
    with open(log_file, 'w') as f:
        f.write(f"Python version: {sys.version}\n")
        f.write(f"Platform: {sys.platform}\n")
        f.write(f"Running on Windows: {os.name == 'nt'}\n\n")
        
        f.write("Module Availability:\n")
        for module_name, available in modules.items():
            f.write(f"{module_name}: {'Available' if available else 'Not available'}\n")
        
        f.write("\nLog Output:\n")
        f.write(log_capture.getvalue())
    
    print(f"\nLog saved to: {log_file}")
    
    # Return success or failure
    return warnings_fixed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
