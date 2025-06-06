#!/usr/bin/env python3
"""
UNCtools Test Runner

This script runs all UNCtools tests and logs the results to the logs directory.
It provides a comprehensive overview of test results and helps identify any issues.
"""

import os
import sys
import time
import logging
import importlib
import subprocess
import re
from pathlib import Path
from datetime import datetime

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_runner")

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Define log file path with timestamp
LOG_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOGS_DIR / f"test_run_{LOG_TIMESTAMP}.log"

# Configure file logging
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Suppress specific warnings
def suppress_warnings():
    """Suppress specific warnings during testing."""
    # Set higher level for specific loggers
    logging.getLogger("unctools.windows.network").setLevel(logging.ERROR)
    
    # Filter out specific messages
    class WarningFilter(logging.Filter):
        def filter(self, record):
            return not (
                record.levelname == 'WARNING' and 
                "win32net module not available" in record.getMessage()
            )
    
    # Add filter to the root logger
    logging.getLogger().addFilter(WarningFilter())

# Define test modules to run
TEST_MODULES = [
    "tests.basic_functionality_test",
    "tests.test_converter_v2",
    "tests.test_detector",
    "tests.test_operations",
    "tests.test_windows_imports"
]

# Define standalone test scripts
TEST_SCRIPTS = [
    "tests/basic_functionality_test.py",
    "tests/test_converter_v2.py",
    "tests/test_detector.py",
    "tests/test_operations.py",
    "tests/test_windows_imports.py",
    "tests/test_windows.py"
]

def print_section(title):
    """Print a section header to console and log."""
    section = f"\n{'=' * 80}\n{title}\n{'=' * 80}"
    print(section)
    logger.info(section)

def fix_test_imports():
    """Fix test imports to make tests work properly."""
    print_section("Fixing test imports")
    
    # Add the parent directory to the system path for direct script execution
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Check if tests/__init__.py exists
    init_file = os.path.join(current_dir, "tests", "__init__.py")
    if not os.path.exists(init_file):
        logger.info("Creating tests/__init__.py")
        with open(init_file, 'w') as f:
            f.write('# This file marks the directory as a Python package\n')
    
    # Update import statements in test files if needed
    test_files = [
        os.path.join(current_dir, "tests", "test_converter_v2.py"),
        os.path.join(current_dir, "tests", "test_detector.py"),
        os.path.join(current_dir, "tests", "test_operations.py"),
        os.path.join(current_dir, "tests", "test_windows_imports.py"),
        os.path.join(current_dir, "tests", "test_windows.py")
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            logger.info(f"Checking imports in {file_path}")
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check if we need to add the sys.path insert
            if "import sys" in content and "sys.path.insert" not in content:
                logger.info(f"Adding sys.path modification to {file_path}")
                
                # Find the import section
                import_section_match = re.search(r'import .*?\n\n', content, re.DOTALL)
                if import_section_match:
                    import_section = import_section_match.group(0)
                    
                    # Add sys.path insert after the imports
                    sys_path_insert = "\n# Add parent directory to path for imports\nsys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))\n\n"
                    new_content = content.replace(import_section, import_section + sys_path_insert)
                    
                    # Write the file back
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
            
            # Replace relative imports with absolute imports
            if "from .test_framework import" in content:
                logger.info(f"Replacing relative imports in {file_path}")
                
                # Replace the import
                new_content = content.replace(
                    "from .test_framework import",
                    "from tests.test_framework import"
                )
                
                # Write the file back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

def fix_encoding_issues():
    """Fix encoding issues in test files."""
    print_section("Fixing encoding issues")
    
    # Fix basic_functionality_test.py
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            "tests", "basic_functionality_test.py")
    
    if os.path.exists(file_path):
        logger.info(f"Checking encoding issues in {file_path}")
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check if it contains problematic characters
        if "✓" in content or "✗" in content:
            logger.info(f"Fixing Unicode characters in {file_path}")
            
            # Define a new check function
            new_check_function = '''
def check(condition, message):
    """Check a condition and print the result."""
    if condition:
        print(f"[PASS] {message}")
        return True
    else:
        print(f"[FAIL] {message}")
        return False
'''
            
            # Replace the check function definition
            pattern = r'def check\(condition, message\):.*?return False'
            new_content = re.sub(pattern, new_check_function.strip(), content, flags=re.DOTALL)
            
            # Update any ✓ character in the rest of the file
            new_content = new_content.replace("✓", "[PASS]")
            new_content = new_content.replace("✗", "[FAIL]")
            
            # Write the file back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

def fix_missing_functions():
    """Fix missing functions in test files."""
    print_section("Fixing missing functions")
    
    # Fix test_operations.py
    operations_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 "tests", "test_operations.py")
    
    if os.path.exists(operations_file):
        logger.info(f"Checking for missing functions in {operations_file}")
        
        # Read the file
        with open(operations_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check if the test_replace_in_file function is missing
        if "def test_replace_in_file" not in content:
            logger.info(f"Adding test_replace_in_file function to {operations_file}")
            
            # Find the position to insert the function
            match = re.search(r'def test_find_accessible_path.*?\n}', content, re.DOTALL)
            if match:
                insert_position = match.end()
                
                # Add the missing functions
                missing_functions = '''

def test_replace_in_file(env):
    """Test replace_in_file function."""
    # Create a test file with specific content
    test_file = os.path.join(env.temp_dir, 'replace_test.txt')
    with open(test_file, 'w') as f:
        f.write('This is a test. This is only a test.')
    
    # Replace text in the file
    result = replace_in_file(test_file, 'test', 'demo')
    assert_true(result, "Replace should succeed")
    
    # Check the file content
    with open(test_file, 'r') as f:
        content = f.read()
        assert_equal(content, 'This is a demo. This is only a demo.', 
                    "File content should be updated")
    
    # Test replacing text that doesn't exist
    result = replace_in_file(test_file, 'nonexistent', 'replacement')
    assert_false(result, "Replace should fail for non-existent text")

def test_batch_replace_in_files(env):
    """Test batch_replace_in_files function."""
    # Create test files with similar content
    for i in range(3):
        file_path = os.path.join(env.temp_dir, f'batch_replace_{i}.txt')
        with open(file_path, 'w') as f:
            f.write(f'This is file {i}. This is a test.')
    
    # Perform batch replace
    results = batch_replace_in_files(
        env.temp_dir, 'test', 'demo', 
        pattern='batch_replace_*.txt', 
        recursive=False
    )
    
    # Check results
    assert_is_not_none(results, "Results should not be None")
    assert_equal(len(results), 3, "Should have results for 3 files")
    
    # Verify content was replaced in all files
    for i in range(3):
        file_path = os.path.join(env.temp_dir, f'batch_replace_{i}.txt')
        with open(file_path, 'r') as f:
            content = f.read()
            assert_equal(content, f'This is file {i}. This is a demo.', 
                        f"Content in file {i} should be updated")
    
    # Test replacing text that doesn't exist
    results = batch_replace_in_files(
        env.temp_dir, 'nonexistent', 'replacement', 
        pattern='batch_replace_*.txt',
        recursive=False
    )
    
    # Check results - should have entries for all files but all should be False
    assert_equal(len(results), 3, "Should have results for 3 files")
    assert_true(all(not success for success in results.values()), 
               "All replacements should fail for non-existent text")
'''
                
                # Insert the functions
                new_content = content[:insert_position] + missing_functions + content[insert_position:]
                
                # Write the file back
                with open(operations_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
        
        # Check if the functions are not added to the test suite
        if "test_replace_in_file" not in content or "test_batch_replace_in_files" not in content:
            logger.info(f"Adding missing functions to test suite in {operations_file}")
            
            # Find the run_tests function
            match = re.search(r'def run_tests\(\):.*?suite\.add_test\(([^)]+)\)', content, re.DOTALL)
            if match:
                # Find the last add_test call
                last_add_test = match.group(0)
                
                # Add the missing test functions
                if "test_replace_in_file" not in last_add_test:
                    new_add_test = last_add_test + '\n    suite.add_test(test_replace_in_file)'
                    new_content = content.replace(last_add_test, new_add_test)
                    content = new_content
                
                if "test_batch_replace_in_files" not in content:
                    match = re.search(r'def run_tests\(\):.*?suite\.add_test\(([^)]+)\)', content, re.DOTALL)
                    if match:
                        last_add_test = match.group(0)
                        new_add_test = last_add_test + '\n    suite.add_test(test_batch_replace_in_files)'
                        new_content = content.replace(last_add_test, new_add_test)
                        
                        # Write the file back
                        with open(operations_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)

def analyze_test_log(log_file, script_name):
    """
    Analyze a test log file to determine if the tests really passed.
    
    Args:
        log_file: Path to the log file.
        script_name: Name of the test script.
        
    Returns:
        True if all tests passed, False if any tests failed.
    """
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Check for explicit failure indicators
        if "SOME TESTS FAILED!" in content:
            logger.warning(f"Found explicit failure message in {script_name}")
            return False
        
        # Check for test failures
        failed_count = content.count("FAIL ")
        
        # Check for teardown errors
        teardown_errors = content.count("Teardown error")
        
        # Count passed tests - look for patterns in both output formats
        pass_patterns = ["PASS ", "[PASS]", "ALL TESTS PASSED"]
        passed_count = sum(content.count(pattern) for pattern in pass_patterns)
        
        # If we found failures or teardown errors, log them
        if failed_count > 0 or teardown_errors > 0:
            logger.warning(f"Found {failed_count} failures and {teardown_errors} teardown errors in {script_name}")
            
            # Extract the specific failure messages
            import re
            failures = re.findall(r'FAIL \((.*?)\)', content)
            if failures:
                logger.warning(f"Failure details in {script_name}:")
                for failure in failures:
                    logger.warning(f"  - {failure}")
            
            return False
        
        # Look for successful test summary phrases
        if "ALL TESTS PASSED" in content or "completed successfully" in content:
            return True
            
        # If we found no failures but also no passes, that's suspicious
        if passed_count == 0:
            logger.warning(f"No passes found in {script_name}, this may indicate a problem")
            return False
        
        # Otherwise, tests passed
        return True
        
    except Exception as e:
        logger.exception(f"Error analyzing log file {log_file}: {e}")
        return False
    

def run_module_test(module_name):
    """
    Run a test by importing the module.
    
    Args:
        module_name: The name of the module to import and run.
        
    Returns:
        True if the test passed, False otherwise.
    """
    print_section(f"Running test module: {module_name}")
    
    try:
        # Add current directory to sys.path to enable module imports
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        
        # Import the module
        module = importlib.import_module(module_name)
        
        # Check if the module has a run_tests function
        if hasattr(module, "run_tests"):
            # Call the run_tests function
            result = module.run_tests()
            success = result == 0 if isinstance(result, int) else bool(result)
        elif hasattr(module, "main"):
            # Call the main function
            result = module.main()
            success = result == 0 if isinstance(result, int) else bool(result)
        else:
            # Just importing the module should run the tests
            success = True
            
        if success:
            logger.info(f"Module test '{module_name}' passed")
        else:
            logger.error(f"Module test '{module_name}' failed")
            
        return success
    except Exception as e:
        logger.exception(f"Error running module test '{module_name}': {e}")
        return False

def run_script_test(script_path):
    """
    Run a test by executing the script as a subprocess.
    
    Args:
        script_path: The path to the script to execute.
        
    Returns:
        True if the test passed, False otherwise.
    """
    print_section(f"Running test script: {script_path}")
    
    try:
        # Run the script as a subprocess
        script_log_file = LOGS_DIR / f"{Path(script_path).stem}_{LOG_TIMESTAMP}.log"
        
        with open(script_log_file, "w") as log_file:
            # Start the subprocess
            result = subprocess.run(
                [sys.executable, script_path],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True
            )
        
        # Check if the script ran without crashing
        returncode_success = result.returncode == 0
        
        # Analyze the log file for test failures
        log_success = analyze_test_log(script_log_file, script_path)
        
        # Consider the test successful only if both checks pass
        success = returncode_success and log_success
        
        if success:
            logger.info(f"Script test '{script_path}' passed")
        else:
            if not returncode_success:
                logger.error(f"Script test '{script_path}' failed with return code {result.returncode}")
            else:
                logger.error(f"Script test '{script_path}' failed based on log analysis")
            
            # Read the log file and add it to our log
            with open(script_log_file, "r", encoding='utf-8', errors='ignore') as log_file:
                logger.error(f"Script output:\n{log_file.read()}")
            
        return success
    except Exception as e:
        logger.exception(f"Error running script test '{script_path}': {e}")
        return False

def install_package():
    """
    Install the UNCtools package in development mode.
    
    Returns:
        True if installation succeeded, False otherwise.
    """
    print_section("Installing UNCtools package in development mode")
    
    try:
        # Run pip install in development mode
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Check if installation succeeded
        success = result.returncode == 0
        
        if success:
            logger.info("Package installation succeeded")
            
            # Try to install windows extras if on Windows
            if os.name == "nt":
                logger.info("Installing Windows extras")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", ".[windows]"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info("Windows extras installation succeeded")
                else:
                    logger.error(f"Windows extras installation failed:\n{result.stdout}")
        else:
            logger.error(f"Package installation failed:\n{result.stdout}")
            
        return success
    except Exception as e:
        logger.exception(f"Error installing package: {e}")
        return False

def check_imports():
    """
    Test importing the UNCtools package.
    
    Returns:
        True if imports succeeded, False otherwise.
    """
    print_section("Testing UNCtools imports")
    
    try:
        # Import the package
        import unctools
        logger.info(f"UNCtools version: {unctools.__version__}")
        logger.info(f"UNCtools loaded from: {unctools.__file__}")
        
        # Import core modules
        from unctools import converter, detector, operations
        logger.info("Core modules imported successfully")
        
        # Import utility modules
        from unctools.utils import compat, logger as utils_logger, validation
        logger.info("Utility modules imported successfully")
        
        # Import Windows modules (will use stubs on non-Windows)
        from unctools.windows import registry, network, security
        logger.info("Windows modules imported successfully")
        
        # Check if running on Windows
        if os.name == "nt":
            # Check if win32net is available
            if unctools.converter.HAVE_WIN32NET:
                logger.info("win32net module is available")
            else:
                logger.warning("win32net module is not available, some features will use fallbacks")
        
        return True
    except Exception as e:
        logger.exception(f"Error importing UNCtools: {e}")
        return False

def run_all_tests():
    """
    Run all tests.
    
    Returns:
        The number of failed tests.
    """
    print_section("STARTING UNCTOOLS TEST RUN")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Suppress warnings
    suppress_warnings()
    
    # Fix test issues
    fix_test_imports()
    fix_encoding_issues()
    fix_missing_functions()
    
    # Track test results
    results = {
        "install": False,
        "imports": False,
        "module_tests": [],
        "script_tests": []
    }
    
    # Step 1: Install the package
    results["install"] = install_package()
    
    if not results["install"]:
        logger.error("Package installation failed, skipping remaining tests")
        return sum(1 for r in results.values() if r is False or (isinstance(r, list) and False in r))
    
    # Step 2: Test imports
    results["imports"] = check_imports()
    
    if not results["imports"]:
        logger.error("Import test failed, skipping remaining tests")
        return sum(1 for r in results.values() if r is False or (isinstance(r, list) and False in r))
    
    # Step 3: Run module tests
    #for module_name in TEST_MODULES:
    #    success = run_module_test(module_name)
    #    results["module_tests"].append((module_name, success))
    
    # Step 4: Run script tests
    for script_path in TEST_SCRIPTS:
        success = run_script_test(script_path)
        results["script_tests"].append((script_path, success))
    
    # Step 5: Generate test summary
    print_section("TEST RUN SUMMARY")
    
    # Installation and import results
    logger.info(f"Package installation: {'PASSED' if results['install'] else 'FAILED'}")
    logger.info(f"Import tests: {'PASSED' if results['imports'] else 'FAILED'}")
    
    # Module test results
    logger.info("\nModule test results:")
    for module_name, success in results["module_tests"]:
        logger.info(f"  {module_name}: {'PASSED' if success else 'FAILED'}")
    
    # Script test results
    logger.info("\nScript test results:")
    for script_path, success in results["script_tests"]:
        logger.info(f"  {script_path}: {'PASSED' if success else 'FAILED'}")
    
    # Calculate failed tests
    failed_tests = 0
    if not results["install"]:
        failed_tests += 1
    if not results["imports"]:
        failed_tests += 1
    failed_tests += sum(1 for _, success in results["module_tests"] if not success)
    failed_tests += sum(1 for _, success in results["script_tests"] if not success)
    
    # Overall result
    total_tests = 2 + len(results["module_tests"]) + len(results["script_tests"])
    passed_tests = total_tests - failed_tests
    
    logger.info(f"\nOverall result: {passed_tests}/{total_tests} tests passed")
    
    if failed_tests == 0:
        logger.info("ALL TESTS PASSED!")
    else:
        logger.error(f"{failed_tests} TESTS FAILED!")
    
    logger.info(f"\nTest log saved to: {LOG_FILE}")
    
    return failed_tests

if __name__ == "__main__":
    start_time = time.time()
    
    try:
        failed_tests = run_all_tests()
        
        # Print execution time
        execution_time = time.time() - start_time
        print(f"\nTest execution completed in {execution_time:.2f} seconds")
        logger.info(f"Test execution completed in {execution_time:.2f} seconds")
        
        # Exit with appropriate code
        sys.exit(1 if failed_tests > 0 else 0)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        logger.warning("Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError running tests: {e}")
        logger.exception(f"Error running tests: {e}")
        sys.exit(1)
