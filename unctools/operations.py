r"""
High-level file operations for working with UNC paths and network drives.

This module provides functions for higher-level operations like safely opening files,
batch converting paths, and copying files with automatic path conversion.
"""

import os
import re
import io
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable, TextIO, BinaryIO, Any, Tuple

# Import from our own modules
from .converter import convert_to_local, convert_to_unc, normalize_path
from .detector import is_unc_path, get_path_type, detect_path_issues, PATH_TYPE_UNC

# Set up module-level logger
logger = logging.getLogger(__name__)

def safe_open(file_path: Union[str, Path], mode: str = 'r', 
             encoding: Optional[str] = None, convert_paths: bool = True, 
             **kwargs) -> Union[TextIO, BinaryIO]:
    """
    Safely open a file, handling UNC paths and network drives automatically.
    
    This function attempts to open a file, automatically converting UNC paths to
    local drive paths if necessary to avoid permission issues.
    
    Args:
        file_path: The path to the file to open.
        mode: The mode to open the file in (same as built-in open).
        encoding: The encoding to use (same as built-in open).
        convert_paths: Whether to automatically convert between UNC and local paths.
        **kwargs: Additional keyword arguments to pass to open.
        
    Returns:
        A file object, as returned by the built-in open function.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If permission is denied (even after path conversion).
        OSError: If another OS-level error occurs.
    """
    original_path = Path(file_path)
    
    try:
        # First try to open the file as-is
        return open(original_path, mode=mode, encoding=encoding, **kwargs)
    except PermissionError:
        # If we get a permission error and conversion is enabled, try converting the path
        if convert_paths:
            try:
                if is_unc_path(original_path):
                    # Convert UNC to local
                    local_path = convert_to_local(original_path)
                    if local_path != original_path:
                        logger.debug(f"Converting UNC path {original_path} to local path {local_path}")
                        return open(local_path, mode=mode, encoding=encoding, **kwargs)
                else:
                    # Convert local to UNC
                    unc_path = convert_to_unc(original_path)
                    if unc_path != original_path:
                        logger.debug(f"Converting local path {original_path} to UNC path {unc_path}")
                        return open(unc_path, mode=mode, encoding=encoding, **kwargs)
            except Exception as e:
                logger.warning(f"Path conversion failed: {e}")
                
        # If conversion failed or is disabled, re-raise the original error
        raise

def file_exists(file_path: Union[str, Path], check_both_paths: bool = True) -> bool:
    """
    Check if a file exists, handling UNC paths and network drives.
    
    Args:
        file_path: The path to check.
        check_both_paths: Whether to check both UNC and local path variants.
        
    Returns:
        True if the file exists, False otherwise.
    """
    original_path = Path(file_path)
    
    # First check the original path
    if os.path.exists(original_path):
        return True
    
    # If requested, check the converted path too
    if check_both_paths:
        try:
            if is_unc_path(original_path):
                # Check local path
                local_path = convert_to_local(original_path)
                if local_path != original_path and os.path.exists(local_path):
                    return True
            else:
                # Check UNC path
                unc_path = convert_to_unc(original_path)
                if unc_path != original_path and os.path.exists(unc_path):
                    return True
        except Exception as e:
            logger.debug(f"Path conversion during file_exists check failed: {e}")
    
    return False

def batch_convert(paths: List[Union[str, Path]], to_unc: bool = False) -> Dict[str, str]:
    """
    Convert a batch of paths between UNC and local formats.
    
    Args:
        paths: List of paths to convert.
        to_unc: If True, convert to UNC paths; if False, convert to local paths.
        
    Returns:
        A dictionary mapping original paths to converted paths.
    """
    result = {}
    
    for path in paths:
        original_path = str(path)
        
        try:
            if to_unc:
                converted_path = str(convert_to_unc(path))
            else:
                converted_path = str(convert_to_local(path))
                
            result[original_path] = converted_path
        except Exception as e:
            logger.warning(f"Failed to convert path {original_path}: {e}")
            result[original_path] = original_path  # Keep original on failure
    
    return result

def safe_copy(src: Union[str, Path], dst: Union[str, Path], 
             convert_paths: bool = True, **kwargs) -> str:
    """
    Safely copy a file, handling UNC paths and network drives.
    
    Args:
        src: Source file path.
        dst: Destination file path.
        convert_paths: Whether to automatically convert between UNC and local paths.
        **kwargs: Additional keyword arguments to pass to shutil.copy2.
        
    Returns:
        The path of the destination file as a string.
        
    Raises:
        FileNotFoundError: If the source file does not exist.
        PermissionError: If permission is denied (even after path conversion).
        OSError: If another OS-level error occurs.
    """
    original_src = Path(src)
    original_dst = Path(dst)
    
    try:
        # First try to copy the file as-is
        shutil.copy2(original_src, original_dst, **kwargs)
        return str(original_dst)  # Always return the destination path string
    except PermissionError:
        # If we get a permission error and conversion is enabled, try converting the paths
        if convert_paths:
            # Try different combinations of path conversions
            path_variants = []
            
            # Convert source path
            try:
                if is_unc_path(str(original_src)):  # Convert to string before checking
                    local_src = convert_to_local(original_src)
                    if local_src != original_src:
                        path_variants.append((local_src, original_dst))
                else:
                    unc_src = convert_to_unc(original_src)
                    if unc_src != original_src:
                        path_variants.append((unc_src, original_dst))
            except Exception as e:
                logger.debug(f"Source path conversion failed: {e}")
            
            # Convert destination path
            try:
                if is_unc_path(str(original_dst)):  # Convert to string before checking
                    local_dst = convert_to_local(original_dst)
                    if local_dst != original_dst:
                        path_variants.append((original_src, local_dst))
                else:
                    unc_dst = convert_to_unc(original_dst)
                    if unc_dst != original_dst:
                        path_variants.append((original_src, unc_dst))
            except Exception as e:
                logger.debug(f"Destination path conversion failed: {e}")
            
            # Convert both paths
            try:
                if is_unc_path(original_src) and not is_unc_path(original_dst):
                    local_src = convert_to_local(original_src)
                    unc_dst = convert_to_unc(original_dst)
                    if local_src != original_src and unc_dst != original_dst:
                        path_variants.append((local_src, unc_dst))
                elif not is_unc_path(original_src) and is_unc_path(original_dst):
                    unc_src = convert_to_unc(original_src)
                    local_dst = convert_to_local(original_dst)
                    if unc_src != original_src and local_dst != original_dst:
                        path_variants.append((unc_src, local_dst))
            except Exception as e:
                logger.debug(f"Dual path conversion failed: {e}")
            
            # Try each variant
            for src_variant, dst_variant in path_variants:
                try:
                    logger.debug(f"Trying copy with converted paths: {src_variant} -> {dst_variant}")
                    # Make sure to return a string, not the result from shutil.copy2 which may be a Path
                    shutil.copy2(src_variant, dst_variant, **kwargs)
                    return str(dst_variant)  # Return the destination path as a string
                except Exception as e:
                    logger.debug(f"Copy attempt failed: {e}")
        
        # If all conversion attempts failed or conversion is disabled, re-raise the original error
        raise

def batch_copy(src_paths: List[Union[str, Path]], dst_dir: Union[str, Path], 
              convert_paths: bool = True, max_retries: int = 1) -> Dict[str, Tuple[bool, Optional[str]]]:
    """
    Copy multiple files to a destination directory, handling UNC paths.
    
    Args:
        src_paths: List of source file paths to copy.
        dst_dir: Destination directory.
        convert_paths: Whether to automatically convert between UNC and local paths.
        max_retries: Maximum number of retries for each file if copy fails.
        
    Returns:
        A dictionary mapping source paths to tuples of (success, destination_path).
        If success is False, destination_path will be None.
    """
    dst_dir_path = Path(dst_dir)
    
    # Make sure the destination directory exists
    try:
        os.makedirs(dst_dir_path, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create destination directory {dst_dir_path}: {e}")
        
        # If conversion is enabled, try with converted path
        if convert_paths:
            try:
                if is_unc_path(str(dst_dir_path)):  # Convert Path to string before checking
                    local_dst_dir = convert_to_local(dst_dir_path)
                    if local_dst_dir != dst_dir_path:
                        logger.debug(f"Trying to create directory with converted path: {local_dst_dir}")
                        os.makedirs(local_dst_dir, exist_ok=True)
                        dst_dir_path = local_dst_dir
                else:
                    unc_dst_dir = convert_to_unc(dst_dir_path)
                    if unc_dst_dir != dst_dir_path:
                        logger.debug(f"Trying to create directory with converted path: {unc_dst_dir}")
                        os.makedirs(unc_dst_dir, exist_ok=True)
                        dst_dir_path = unc_dst_dir
            except Exception as e2:
                logger.error(f"Failed to create destination directory with converted path: {e2}")
                # Return empty results since we can't proceed
                return {str(src): (False, None) for src in src_paths}
    
    # Copy each file
    results = {}
    
    for src in src_paths:
        src_path = Path(src)
        filename = src_path.name
        dst_path = dst_dir_path / filename
        
        # Try to copy with retries
        success = False
        dst_result = None
        retry_count = 0
        last_error = None
        
        while not success and retry_count <= max_retries:
            try:
                # Attempt to copy the file
                dst_result = safe_copy(src_path, dst_path, convert_paths=convert_paths)
                # If we get here, the copy was successful
                success = True
                # Ensure the result is a string for consistency
                dst_result = str(dst_result) if dst_result is not None else None
            except Exception as e:
                last_error = e
                if retry_count < max_retries:
                    logger.debug(f"Copy attempt {retry_count + 1} failed for {src_path}, retrying: {e}")
                    retry_count += 1
                else:
                    # Last attempt failed
                    logger.error(f"Failed to copy {src_path} to {dst_path} after {max_retries + 1} attempts: {e}")
                    break
        
        # Record the result for this file
        if success:
            results[str(src)] = (True, dst_result)
        else:
            logger.error(f"Failed to copy {src_path} to {dst_path}: {last_error}")
            results[str(src)] = (False, None)
    
    return results

def process_files(directory: Union[str, Path], callback: Callable[[Path], Any], 
                 pattern: str = "*", recursive: bool = True, 
                 convert_paths: bool = True) -> Dict[str, Any]:
    """
    Process files in a directory, handling UNC paths and network drives.
    
    Args:
        directory: The directory to process.
        callback: A function to call for each file. It should accept a Path object
                 and return any value, which will be included in the results.
        pattern: A glob pattern to match files against.
        recursive: Whether to process subdirectories recursively.
        convert_paths: Whether to automatically convert between UNC and local paths.
        
    Returns:
        A dictionary mapping file paths to the results of the callback function.
    """
    dir_path = Path(directory)
    results = {}
    
    # Check if we need to try a path conversion
    if not os.path.exists(dir_path) and convert_paths:
        try:
            if is_unc_path(str(dir_path)):  # Convert Path to string before checking
                local_dir = convert_to_local(dir_path)
                if local_dir != dir_path and os.path.exists(local_dir):
                    logger.debug(f"Converting UNC path {dir_path} to local path {local_dir}")
                    dir_path = local_dir
            else:
                unc_dir = convert_to_unc(dir_path)
                if unc_dir != dir_path and os.path.exists(unc_dir):
                    logger.debug(f"Converting local path {dir_path} to UNC path {unc_dir}")
                    dir_path = unc_dir
        except Exception as e:
            logger.warning(f"Path conversion failed: {e}")
    
    # Make sure the directory exists
    if not os.path.exists(dir_path):
        logger.error(f"Directory not found: {dir_path}")
        return results
    
    # Process files
    if recursive:
        glob_pattern = f"**/{pattern}"
    else:
        glob_pattern = pattern
    
    for file_path in dir_path.glob(glob_pattern):
        if file_path.is_file():
            try:
                # Call the callback function
                result = callback(file_path)
                results[str(file_path)] = result
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                results[str(file_path)] = None
    
    return results

def replace_in_file(file_path: Union[str, Path], old_text: str, new_text: str,
                  encoding: str = 'utf-8', convert_paths: bool = True) -> bool:
    """
    Replace text in a file, handling UNC paths and network drives.
    
    Args:
        file_path: The path to the file.
        old_text: The text to replace.
        new_text: The new text.
        encoding: The encoding to use when reading/writing the file.
        convert_paths: Whether to automatically convert between UNC and local paths.
        
    Returns:
        True if the file was modified, False otherwise.
    """
    try:
        # Read the file content
        with safe_open(file_path, 'r', encoding=encoding, convert_paths=convert_paths) as f:
            content = f.read()
        
        # Check if the old text exists
        if old_text not in content:
            logger.warning(f"Text not found in file {file_path}")
            return False
        
        # Replace the text
        new_content = content.replace(old_text, new_text)
        
        # Write back to the file
        with safe_open(file_path, 'w', encoding=encoding, convert_paths=convert_paths) as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        logger.error(f"Error replacing text in file {file_path}: {e}")
        return False

def batch_replace_in_files(directory: Union[str, Path], old_text: str, new_text: str,
                         pattern: str = "*.txt", recursive: bool = True,
                         encoding: str = 'utf-8', convert_paths: bool = True) -> Dict[str, bool]:
    """
    Replace text in multiple files, handling UNC paths and network drives.
    
    Args:
        directory: The directory containing files to process.
        old_text: The text to replace.
        new_text: The new text.
        pattern: A glob pattern to match files against.
        recursive: Whether to process subdirectories recursively.
        encoding: The encoding to use when reading/writing the files.
        convert_paths: Whether to automatically convert between UNC and local paths.
        
    Returns:
        A dictionary mapping file paths to booleans indicating success.
    """
    def replace_callback(file_path):
        return replace_in_file(file_path, old_text, new_text, encoding, convert_paths)
    
    return process_files(directory, replace_callback, pattern, recursive, convert_paths)

def get_unc_path_elements(path: Union[str, Path]) -> Optional[Tuple[str, str, str]]:
    """
    Extract server, share, and path components from a UNC path.
    
    Args:
        path: The UNC path to analyze.
        
    Returns:
        A tuple of (server, share, relative_path) if the path is a valid UNC path,
        or None if the path is not a UNC path.
    """
    original_path_str = str(path)
    path_str = original_path_str.replace('/', '\\')
    
    # Check if it's a UNC path
    if not path_str.startswith('\\\\'):
        return None
    
    # Parse the UNC path
    match = re.match(r'^\\\\([^\\]+)\\([^\\]+)(?:\\(.*))?', path_str)
    if match:
        server = match.group(1)
        share = match.group(2)
        relative_path = match.group(3) or ""
        
        # If original path used forward slashes, preserve them in the relative path
        if '/' in original_path_str:
            # Replace backslashes with forward slashes in the relative path
            relative_path = relative_path.replace('\\', '/')
            
        return (server, share, relative_path)
    return None

def build_unc_path(server: str, share: str, relative_path: Optional[str] = None) -> str:
    """
    Build a UNC path from server, share, and path components.
    
    Args:
        server: The server name.
        share: The share name.
        relative_path: The relative path within the share (optional).
        
    Returns:
        A properly formatted UNC path.
    """
    unc_base = f"\\\\{server}\\{share}"
    
    if not relative_path:
        return unc_base
    
    # Ensure relative path doesn't start with a backslash
    rel_path = relative_path.lstrip('\\').lstrip('/')
    
    if rel_path:
        return f"{unc_base}\\{rel_path}"
    else:
        return unc_base

def is_path_accessible(path: Union[str, Path], check_both_paths: bool = True) -> bool:
    """
    Check if a path is accessible for reading.
    
    Args:
        path: The path to check.
        check_both_paths: Whether to check both UNC and local path variants.
        
    Returns:
        True if the path is accessible, False otherwise.
    """
    # For files, check if they exist and are readable
    if os.path.isfile(path):
        try:
            with open(path, 'r') as f:
                f.read(1)  # Try to read 1 byte
            return True
        except:
            pass
    
    # For directories, check if we can list their contents
    elif os.path.isdir(path):
        try:
            os.listdir(path)
            return True
        except:
            pass
    
    # If the original path isn't accessible and check_both_paths is enabled
    if check_both_paths:
        try:
            # Try the converted path
            if is_unc_path(str(path)):  # Convert Path to string before checking
                local_path = convert_to_local(path)
                if local_path != path:
                    return is_path_accessible(local_path, check_both_paths=False)
            else:
                unc_path = convert_to_unc(path)
                if unc_path != path:
                    return is_path_accessible(unc_path, check_both_paths=False)
        except Exception as e:
            logger.debug(f"Path conversion during accessibility check failed: {e}")
    
    return False

def find_accessible_path(path: Union[str, Path]) -> Optional[Path]:
    """
    Find an accessible variant of a path, trying both UNC and local formats.
    
    Args:
        path: The original path to find an accessible variant for.
        
    Returns:
        An accessible Path object, or None if no accessible variant is found.
    """
    original_path = Path(path)
    
    # Check the original path first
    if is_path_accessible(original_path, check_both_paths=False):
        return original_path
    
    # Try converted paths
    try:
        if is_unc_path(str(original_path)):  # Convert Path to string before checking
            # Try local path
            local_path = convert_to_local(original_path)
            if local_path != original_path and is_path_accessible(local_path, check_both_paths=False):
                return local_path
        else:
            # Try UNC path
            unc_path = convert_to_unc(original_path)
            if unc_path != original_path and is_path_accessible(unc_path, check_both_paths=False):
                return unc_path
    except Exception as e:
        logger.debug(f"Path conversion during accessibility check failed: {e}")
    
    # If we got here, no accessible variant was found
    return None