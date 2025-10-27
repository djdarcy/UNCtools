"""Pytest configuration and fixtures for UNCtools tests."""
import pytest
import sys
import os

# Add parent directory to path to allow imports from unctools package
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


@pytest.fixture
def env():
    """
    Pytest fixture providing a test environment with temporary files.

    Yields a TestEnvironment instance with setup already called.
    Automatically cleans up after test completion.

    The environment provides:
    - temp_dir: Temporary directory path
    - test_files: List of test file paths
    - test_dirs: List of test directory paths

    Example:
        def test_something(env):
            test_file = env.test_files[0]
            # Use test_file in your test
    """
    from tests.test_operations import TestEnvironment

    environment = TestEnvironment()
    environment.setup()

    yield environment

    environment.teardown()
