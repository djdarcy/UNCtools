#!/usr/bin/env python3
"""
Batch operations example for UNCtools.

This script demonstrates how to use UNCtools to perform batch operations
on files across UNC paths, network drives, and local paths.
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import UNCtools
import unctools
from unctools import (
    convert_to_local, convert_to_unc, is_unc_path,
    batch_convert, batch_copy, process_files,
    safe_open
)

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch operations example for UNCtools"
    )
    parser.add_argument(
        "operation",
        choices=["convert", "copy", "process"],
        help="Operation to perform (convert, copy, process)"
    )
    parser.add_argument(
        "source",
        help="Source directory or file"
    )
    parser.add_argument(
        "--dest", "-d",
        help="Destination directory (for copy operation)"
    )
    parser.add_argument(
        "--pattern", "-p",
        default="*",
        help="File pattern to match (glob pattern, default: *)"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Process directories recursively"
    )
    parser.add_argument(
        "--to-unc",
        action="store_true",
        help="Convert to UNC paths (for convert operation)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    return parser.parse_args()

def demonstrate_path_conversion(source: str, pattern: str, recursive: bool, to_unc: bool):
    """
    Demonstrate path conversion using UNCtools.
    
    Args:
        source: The source directory.
        pattern: File pattern to match.
        recursive: Whether to process directories recursively.
        to_unc: Whether to convert to UNC paths.
    """
    print_section("Path Conversion Example")
    source_path = Path(source)
    
    # Verify the source directory exists
    if not source_path.exists():
        print(f"Error: {source} does not exist.")
        return
    
    # Get all matching files
    if recursive:
        files = list(source_path.glob(f"**/{pattern}"))
    else:
        files = list(source_path.glob(pattern))
    
    if not files:
        print(f"No files found matching {pattern} in {source}")
        return
    
    print(f"Found {len(files)} files matching {pattern} in {source}")
    
    # Convert paths
    start_time = time.time()
    converted = batch_convert([str(f) for f in files], to_unc=to_unc)
    end_time = time.time()
    
    print(f"\nConverted {len(converted)} paths in {end_time - start_time:.2f} seconds")
    print(f"Direction: {'Local -> UNC' if to_unc else 'UNC -> Local'}")
    
    # Display a sample of conversions
    max_display = min(5, len(converted))
    print(f"\nSample conversions (showing {max_display} of {len(converted)}):")
    
    for i, (original, converted_path) in enumerate(list(converted.items())[:max_display]):
        print(f"  {i+1}. {original}\n     -> {converted_path}")
    
    # Display conversion statistics
    unchanged_count = sum(1 for orig, conv in converted.items() if orig == conv)
    changed_count = len(converted) - unchanged_count
    
    print(f"\nConversion statistics:")
    print(f"  Total paths: {len(converted)}")
    print(f"  Changed paths: {changed_count} ({changed_count/len(converted)*100:.1f}%)")
    print(f"  Unchanged paths: {unchanged_count} ({unchanged_count/len(converted)*100:.1f}%)")

def demonstrate_batch_copy(source: str, dest: str, pattern: str, recursive: bool):
    """
    Demonstrate batch copying using UNCtools.
    
    Args:
        source: The source directory.
        dest: The destination directory.
        pattern: File pattern to match.
        recursive: Whether to process directories recursively.
    """
    print_section("Batch Copy Example")
    
    if not dest:
        print("Error: Destination directory is required for copy operation.")
        return
    
    source_path = Path(source)
    dest_path = Path(dest)
    
    # Verify the source directory exists
    if not source_path.exists():
        print(f"Error: {source} does not exist.")
        return
    
    # Create destination directory if it doesn't exist
    if not dest_path.exists():
        print(f"Creating destination directory: {dest}")
        dest_path.mkdir(parents=True, exist_ok=True)
    
    # Get all matching files
    if recursive:
        files = list(source_path.glob(f"**/{pattern}"))
    else:
        files = list(source_path.glob(pattern))
    
    if not files:
        print(f"No files found matching {pattern} in {source}")
        return
    
    print(f"Found {len(files)} files matching {pattern} in {source}")
    print(f"Copying to {dest}...")
    
    # Perform batch copy
    start_time = time.time()
    results = batch_copy([str(f) for f in files], str(dest_path))
    end_time = time.time()
    
    # Count successes and failures
    successes = sum(1 for success, _ in results.values() if success)
    failures = len(results) - successes
    
    print(f"\nCopied {successes} files in {end_time - start_time:.2f} seconds")
    print(f"  Success: {successes} files")
    print(f"  Failed: {failures} files")
    
    # Display failures if any
    if failures > 0:
        print("\nFailed copies:")
        for src, (success, dst) in results.items():
            if not success:
                print(f"  {src} -> FAILED")

def demonstrate_file_processing(source: str, pattern: str, recursive: bool):
    """
    Demonstrate file processing using UNCtools.
    
    Args:
        source: The source directory.
        pattern: File pattern to match.
        recursive: Whether to process directories recursively.
    """
    print_section("File Processing Example")
    source_path = Path(source)
    
    # Verify the source directory exists
    if not source_path.exists():
        print(f"Error: {source} does not exist.")
        return
    
    # Define a file processing function
    def process_file(file_path: Path) -> Dict[str, Any]:
        """
        Process a single file and return some information about it.
        
        Args:
            file_path: The path to the file.
            
        Returns:
            A dictionary with file information.
        """
        stats = file_path.stat()
        
        # Try to read the first line if it's a text file
        first_line = None
        if file_path.suffix.lower() in ('.txt', '.md', '.py', '.json', '.csv', '.ini', '.log'):
            try:
                with safe_open(file_path, 'r', errors='ignore') as f:
                    first_line = f.readline().strip()
            except:
                pass
        
        return {
            'size': stats.st_size,
            'modified': stats.st_mtime,
            'is_unc': is_unc_path(file_path),
            'first_line': first_line,
            'local_path': str(convert_to_local(file_path)),
            'unc_path': str(convert_to_unc(file_path))
        }
    
    # Process all files in the directory
    print(f"Processing files in {source} matching {pattern}...")
    
    start_time = time.time()
    results = process_files(source, process_file, pattern=pattern, recursive=recursive)
    end_time = time.time()
    
    if not results:
        print(f"No files found matching {pattern} in {source}")
        return
    
    print(f"\nProcessed {len(results)} files in {end_time - start_time:.2f} seconds")
    
    # Calculate statistics
    total_size = sum(info['size'] for info in results.values())
    unc_count = sum(1 for info in results.values() if info['is_unc'])
    
    print(f"\nFile statistics:")
    print(f"  Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    print(f"  UNC paths: {unc_count} ({unc_count/len(results)*100:.1f}%)")
    print(f"  Non-UNC paths: {len(results) - unc_count} ({(len(results) - unc_count)/len(results)*100:.1f}%)")
    
    # Show details for a few files
    max_display = min(5, len(results))
    print(f"\nSample file details (showing {max_display} of {len(results)}):")
    
    for i, (path, info) in enumerate(list(results.items())[:max_display]):
        print(f"  {i+1}. {path}")
        print(f"     Size: {info['size']:,} bytes")
        print(f"     Modified: {time.ctime(info['modified'])}")
        print(f"     Is UNC path: {info['is_unc']}")
        
        if info['first_line']:
            # Truncate first line if it's too long
            first_line = info['first_line']
            if len(first_line) > 50:
                first_line = first_line[:47] + "..."
            print(f"     First line: {first_line}")
        
        # Show path conversions
        if info['local_path'] != str(path):
            print(f"     Local path: {info['local_path']}")
        if info['unc_path'] != str(path):
            print(f"     UNC path: {info['unc_path']}")
        print()

def main():
    """Main function."""
    args = parse_arguments()
    
    # Set verbose mode if requested
    if args.verbose:
        logging.getLogger("unctools").setLevel(logging.DEBUG)
    
    # Execute the requested operation
    if args.operation == "convert":
        demonstrate_path_conversion(args.source, args.pattern, args.recursive, args.to_unc)
    elif args.operation == "copy":
        demonstrate_batch_copy(args.source, args.dest, args.pattern, args.recursive)
    elif args.operation == "process":
        demonstrate_file_processing(args.source, args.pattern, args.recursive)

if __name__ == "__main__":
    main()
