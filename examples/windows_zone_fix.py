#!/usr/bin/env python3
"""
Windows security zone fix example for UNCtools.

This script demonstrates how to use UNCtools to fix Windows security zone
issues for UNC paths, which can help resolve permission and access problems.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import UNCtools
import unctools
from unctools.detector import is_unc_path, detect_path_issues

# Check if running on Windows
if os.name != 'nt':
    print("This example is specific to Windows and won't work on other platforms.")
    sys.exit(1)

# Import Windows-specific modules
from unctools.windows import fix_security_zone, add_to_intranet_zone

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Windows security zone fix example for UNCtools"
    )
    parser.add_argument(
        "path", 
        nargs="?", 
        help="UNC path or server name to check/fix"
    )
    parser.add_argument(
        "--scan", 
        metavar="DIRECTORY", 
        help="Scan a directory for UNC paths with potential security issues"
    )
    parser.add_argument(
        "--fix-all", 
        action="store_true", 
        help="Automatically fix all security zone issues found during scan"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose output"
    )
    return parser.parse_args()

def extract_server_from_unc(path):
    """Extract the server name from a UNC path."""
    if not is_unc_path(path):
        return None
    
    # Use regex to extract server name
    import re
    match = re.match(r"\\\\([^\\]+)\\", str(path))
    if match:
        return match.group(1)
    
    return None

def fix_single_path(path):
    """Check and fix security zone issues for a single path."""
    print_section(f"Checking path: {path}")
    
    # Check if it's a UNC path
    if is_unc_path(path):
        print(f"Path is a UNC path")
        server = extract_server_from_unc(path)
        
        if server:
            print(f"Server name: {server}")
            
            # Check for potential issues
            issues = detect_path_issues(path)
            if issues:
                print("Detected issues:")
                for issue in issues:
                    print(f"  - {issue}")
                
                # Offer to fix if security zone issue is found
                if any("security zone" in issue for issue in issues):
                    choice = input("Would you like to fix the security zone issue? (y/n): ")
                    if choice.lower() == 'y':
                        if fix_security_zone(server):
                            print(f"Successfully added {server} to the Local Intranet zone")
                        else:
                            print(f"Failed to add {server} to the Local Intranet zone")
            else:
                print("No issues detected.")
        else:
            print("Failed to extract server name from UNC path.")
    else:
        # If it's not a UNC path, check if it's a server name
        print(f"Not a UNC path, checking if it's a server name")
        
        # Try to add it to the Intranet zone directly
        choice = input(f"Would you like to add '{path}' to the Local Intranet zone? (y/n): ")
        if choice.lower() == 'y':
            if add_to_intranet_zone(path):
                print(f"Successfully added {path} to the Local Intranet zone")
            else:
                print(f"Failed to add {path} to the Local Intranet zone")

def scan_directory(directory, fix_all=False):
    """Scan a directory for UNC paths with potential security issues."""
    print_section(f"Scanning directory: {directory}")
    
    # Use pathlib to handle the directory
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"Error: {directory} is not a valid directory")
        return
    
    # Track UNC paths and servers
    unc_paths = []
    servers = set()
    
    # Walk the directory
    for root, dirs, files in os.walk(directory):
        # Check if the root is a UNC path
        if is_unc_path(root):
            unc_paths.append(root)
            server = extract_server_from_unc(root)
            if server:
                servers.add(server)
        
        # Check filenames for UNC paths (e.g., in text files)
        for file in files:
            if file.endswith((".txt", ".ini", ".conf", ".cfg", ".bat", ".cmd", ".ps1")):
                # These files might contain UNC paths
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                        
                        # Look for UNC paths in the content
                        import re
                        for match in re.finditer(r'\\\\([^\\]+)\\([^\\]+)', content):
                            unc_path = match.group(0)
                            unc_paths.append(unc_path)
                            server = match.group(1)
                            servers.add(server)
                except:
                    # Skip files that can't be read
                    pass
    
    print(f"Found {len(unc_paths)} UNC paths referencing {len(servers)} servers")
    
    if servers:
        print("\nServers referenced:")
        for server in sorted(servers):
            print(f"  - {server}")
        
        if fix_all:
            print("\nAutomatically fixing security zones for all servers...")
            for server in servers:
                if fix_security_zone(server):
                    print(f"  ✓ Successfully added {server} to the Local Intranet zone")
                else:
                    print(f"  ✗ Failed to add {server} to the Local Intranet zone")
        else:
            print("\nTo fix security zones for all servers, run with --fix-all")

def main():
    """Main function."""
    args = parse_arguments()
    
    # Set verbose mode if requested
    if args.verbose:
        logging.getLogger("unctools").setLevel(logging.DEBUG)
    
    print_section("Windows Security Zone Fix Example")
    print("This example demonstrates how to use UNCtools to fix Windows security zone issues.")
    
    # Check which operation to perform
    if args.scan:
        scan_directory(args.scan, args.fix_all)
    elif args.path:
        fix_single_path(args.path)
    else:
        print("Please provide a path to check, or use --scan to scan a directory.")
        print("For more information, run: python windows_zone_fix.py --help")

if __name__ == "__main__":
    main()
