#!/usr/bin/env python3
"""
Basic usage examples for UNCtools.

This script demonstrates the core functionality of UNCtools,
including path conversion, detection, and file operations.
"""

import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import UNCtools
import unctools
from unctools import (
    convert_to_local, convert_to_unc, normalize_path,
    is_unc_path, is_network_drive, is_subst_drive, get_path_type,
    safe_open, safe_copy, batch_convert, process_files
)

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def demonstrate_path_conversion():
    """Demonstrate path conversion functionality."""
    print_section("Path Conversion")
    
    # Example UNC path
    unc_path = "\\\\server\\share\\folder\\file.txt"
    print(f"UNC path: {unc_path}")
    
    # Example local path
    local_path = "Z:\\folder\\file.txt"
    print(f"Local path: {local_path}")
    
    # Show network mappings if on Windows
    if os.name == 'nt':
        print("\nNetwork Mappings:")
        mappings = unctools.get_mappings()
        for unc, drive in mappings.items():
            print(f"  {unc} -> {drive}")
    
    # Convert paths
    print("\nPath Conversion:")
    print(f"  UNC -> Local: {unc_path} -> {convert_to_local(unc_path)}")
    print(f"  Local -> UNC: {local_path} -> {convert_to_unc(local_path)}")
    
    # Normalize paths
    print("\nPath Normalization:")
    print(f"  Normalize (prefer local): {normalize_path(unc_path, prefer_unc=False)}")
    print(f"  Normalize (prefer UNC): {normalize_path(local_path, prefer_unc=True)}")

def demonstrate_path_detection():
    """Demonstrate path detection functionality."""
    print_section("Path Detection")
    
    # Example paths
    paths = [
        "C:\\Windows\\System32",
        "\\\\server\\share\\folder",
        "Z:\\documents",
        "/usr/local/bin",
        "\\\\?\\C:\\Very\\Long\\Path"
    ]
    
    print("Path Type Detection:")
    for path in paths:
        path_type = get_path_type(path)
        is_unc = is_unc_path(path)
        print(f"  {path}:")
        print(f"    Type: {path_type}")
        print(f"    Is UNC: {is_unc}")
        
        # Check if it's a drive
        if path.endswith(':'):
            print(f"    Is Network Drive: {is_network_drive(path)}")
            print(f"    Is Subst Drive: {is_subst_drive(path)}")
    
    # Detect path issues
    print("\nPath Issue Detection:")
    problematic_paths = [
        "\\\\server\\share\\folder",
        "Z:\\very\\long\\path" + "\\subfolder" * 20,
        "C:" + "\\a" * 300
    ]
    
    for path in problematic_paths:
        issues = unctools.detector.detect_path_issues(path)
        print(f"  {path}:")
        if issues:
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("    No issues detected")

def demonstrate_file_operations():
    """Demonstrate file operation functionality."""
    print_section("File Operations")
    
    # Create a temporary file
    temp_dir = os.path.dirname(os.path.abspath(__file__))
    temp_file = os.path.join(temp_dir, "temp_file.txt")
    
    print(f"Creating temporary file: {temp_file}")
    with open(temp_file, "w") as f:
        f.write("Hello, UNCtools!")
    
    # Safe open
    print("\nSafe Open:")
    try:
        with safe_open(temp_file, "r") as f:
            content = f.read()
            print(f"  Content: {content}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Batch operations
    print("\nBatch Operations:")
    
    # Create a few more files
    for i in range(3):
        with open(os.path.join(temp_dir, f"temp_file_{i}.txt"), "w") as f:
            f.write(f"Test file {i}")
    
    # Process files
    print("  Processing files:")
    def process_callback(path):
        return path.stat().st_size
    
    results = process_files(temp_dir, process_callback, pattern="temp_file*.txt")
    for path, size in results.items():
        print(f"    {path}: {size} bytes")
    
    # Batch convert
    print("\n  Batch conversion:")
    paths = [os.path.join(temp_dir, f"temp_file_{i}.txt") for i in range(3)]
    converted = batch_convert(paths, to_unc=True)
    for original, converted_path in converted.items():
        print(f"    {original} -> {converted_path}")
    
    # Clean up
    for path in [temp_file] + [os.path.join(temp_dir, f"temp_file_{i}.txt") for i in range(3)]:
        try:
            os.remove(path)
        except:
            pass

def demonstrate_windows_features():
    """Demonstrate Windows-specific features."""
    print_section("Windows-Specific Features")
    
    # Skip if not on Windows
    if os.name != 'nt':
        print("Skipping Windows-specific features on non-Windows platform.")
        return
    
    # Import Windows-specific modules
    from unctools.windows import (
        fix_security_zone, add_to_intranet_zone,
        get_all_network_mappings, check_network_connection
    )
    
    # Security zones
    print("Security Zones:")
    print("  - Adding a server to the intranet zone would look like:")
    print("    add_to_intranet_zone('server')")
    print("  - Fixing security zone issues would look like:")
    print("    fix_security_zone('server')")
    
    # Network operations
    print("\nNetwork Operations:")
    print("  - Network mappings:")
    mappings = get_all_network_mappings()
    if mappings:
        for drive, unc in mappings.items():
            print(f"    {drive} -> {unc}")
    else:
        print("    No network mappings found")
    
    # Check network connection
    test_server = "localhost"
    print(f"\n  - Network connection to {test_server}:")
    connected = check_network_connection(test_server)
    print(f"    Connected: {connected}")

def main():
    """Main function to run all demonstrations."""
    print_section("UNCtools Basic Usage Examples")
    print(f"UNCtools version: {unctools.get_version()}")
    print(f"Running on: {os.name}")
    
    # Run demonstrations
    demonstrate_path_conversion()
    demonstrate_path_detection()
    demonstrate_file_operations()
    demonstrate_windows_features()
    
    print("\nDemonstration completed!")

if __name__ == "__main__":
    main()
