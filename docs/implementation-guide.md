# UNCtools - Implementation Guide and Testing Instructions

## Implementation Status

We have successfully completed the initial implementation of the UNCtools package with the following components:

### Core Module Structure
- ✅ `unctools/__init__.py` - Package initialization and exports
- ✅ `unctools/converter.py` - Path conversion utilities
- ✅ `unctools/detector.py` - Path type detection utilities
- ✅ `unctools/operations.py` - High-level file operations

### Utility Modules
- ✅ `unctools/utils/__init__.py` - Utilities package initialization
- ✅ `unctools/utils/logger.py` - Logging configuration
- ✅ `unctools/utils/compat.py` - Cross-platform compatibility
- ✅ `unctools/utils/validation.py` - Path validation

### Windows-Specific Modules
- ✅ `unctools/windows/__init__.py` - Windows package initialization
- ✅ `unctools/windows/registry.py` - Registry operations
- ✅ `unctools/windows/network.py` - Network operations
- ✅ `unctools/windows/security.py` - Security operations

### Package Files
- ✅ `setup.py` - Installation script
- ✅ `setup.cfg` - Package configuration
- ✅ `pyproject.toml` - Modern packaging
- ✅ `MANIFEST.in` - Package file inclusion
- ✅ `LICENSE` - MIT License
- ✅ `README.md` - Package documentation
- ✅ `.gitignore` - Git ignore patterns

### Examples and Tests
- ✅ `examples/basic_usage.py` - Basic usage examples
- ✅ `examples/windows_zone_fix.py` - Windows security zone fixing
- ✅ `examples/batch_operations.py` - Batch file operations
- ✅ `tests/__init__.py` - Tests package initialization
- ✅ `tests/test_converter.py` - Test for the converter module
- ✅ `tests/basic_functionality_test.py` - Basic functionality verification

## Testing Instructions

To test the UNCtools package, follow these steps:

### 1. Install in Development Mode

First, install the package in development mode to allow for easy modifications:

```bash
# Navigate to the UNCtools directory
cd path/to/unctools

# Install in development mode
pip install -e .

# To include Windows-specific dependencies (on Windows)
pip install -e ".[windows]"

# To include development tools
pip install -e ".[dev]"
```

### 2. Run Basic Functionality Test

Test that the core functionality works correctly:

```bash
python tests/basic_functionality_test.py
```

This script verifies that all modules can be imported and basic functions work as expected.

### 3. Test Path Conversion

Test UNC path conversion with:

```bash
# On Windows with a mapped network drive (e.g., Z: mapped to \\server\share)
python examples/basic_usage.py
```

Look for proper path conversion and detection in the output.

### 4. Test Batch Operations

Test batch operations with:

```bash
# Convert paths in a directory
python examples/batch_operations.py convert /path/to/directory --pattern "*.txt" --recursive

# Copy files from a directory to another location
python examples/batch_operations.py copy /path/to/source --dest /path/to/destination --pattern "*.txt" --recursive

# Process files in a directory
python examples/batch_operations.py process /path/to/directory --pattern "*.txt" --recursive
```

### 5. Test Windows-Specific Features (Windows Only)

Test Windows security zone features with:

```bash
# Check and fix security zone issues for a UNC path
python examples/windows_zone_fix.py "\\server\share\folder"

# Scan a directory for UNC paths and fix security zones
python examples/windows_zone_fix.py --scan /path/to/directory --fix-all
```

### 6. Run Unit Tests

Run the unit tests for individual modules:

```bash
# Run all tests
pytest

# Run tests for a specific module
pytest tests/test_converter.py
```

## Expected Output

The basic functionality test should produce output similar to:

```
=== UNCtools Basic Functionality Tests ===

Testing imports...
✓ Import unctools

Checking version information...
✓ UNCtools version: 0.1.0

Testing core module imports...
✓ Import core functions

Testing utils module imports...
✓ Import utils functions

Testing Windows-specific module imports...
✓ Import Windows-specific functions

Testing basic functionality...
✓ is_unc_path(C:\Users\username) should be False
✓ is_unc_path(\\server\share\folder) should be True
✓ normalize_path(C:\Users\username) => C:\Users\username
✓ convert_to_local(\\server\share\folder) => \\server\share\folder
✓ convert_to_unc(C:\Users\username) => C:\Users\username
✓ batch_convert() returned 2 results
✓ Platform information: system: Windows, release: 10, ...

Testing file operations with a temporary file...
✓ safe_open() and read content: 'UNCtools test file'
✓ Temporary file operations completed

=== Test Summary ===
Platform: Windows 10
Python: 3.8.10
UNCtools: 0.1.0
All tests completed. Check the results above for any failures.

Basic functionality tests completed successfully.
```

## Common Issues and Troubleshooting

### Import Errors

If you see import errors:

```
✗ Import unctools: No module named 'unctools'
```

Ensure you've installed the package in development mode and are running Python from the correct environment.

### Missing Windows Functionality

If Windows-specific features are unavailable:

```
✗ Import Windows-specific functions: No module named 'win32api'
```

Install the Windows extras:

```bash
pip install -e ".[windows]"
```

### Path Conversion Issues

If path conversion doesn't work as expected, check:

1. Your network drive mappings are active
2. The UNC paths are correctly formatted
3. You have appropriate permissions for the paths

## Next Steps

After completing these tests, we should:

1. Expand the test suite with more comprehensive tests
2. Create detailed API documentation
3. Consider integration with your existing tools like `psdelta.py`
4. Prepare for PyPI distribution

## Conclusion

This initial implementation provides a solid foundation for the UNCtools package. By following these testing instructions, you can verify that the package works correctly in your environment and identify any issues that need to be addressed before further development.