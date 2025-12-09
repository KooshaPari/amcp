"""Pytest configuration and shared fixtures for SmartCP tests.

This module provides:
- pytest configuration and path setup
- Common asyncio event loop fixtures
- Test markers and custom hooks
- Imports from centralized fixtures in tests/fixtures/
"""

import pytest
import asyncio
import sys
from pathlib import Path
from functools import wraps
from inspect import iscoroutinefunction

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Register pytest-asyncio plugin
pytest_plugins = ["pytest_asyncio"]

# Import consolidated fixtures from fixtures submodule
# This makes all fixture modules available to tests
pytest_plugins += ["tests.fixtures"]


def pytest_configure(config):
    """Configure pytest."""
    # Ensure project root is in Python path before collection
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    config.addinivalue_line("markers", "asyncio: mark test as asyncio")
    config.addinivalue_line("markers", "smoke: mark test as smoke test (fast)")
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "performance: mark test as performance test")


@pytest.fixture
def anyio_backend():
    """Configure anyio to use asyncio backend."""
    return "asyncio"


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case.

    This fixture is used by all async tests. It creates a fresh event loop
    for each test and cleans it up afterward.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


def pytest_pyfunc_call(pyfuncitem):
    """Wrapper for running async tests.

    This allows @pytest.mark.asyncio tests to run without the pytest-asyncio plugin.
    """
    if pyfuncitem.get_closest_marker("asyncio"):
        if iscoroutinefunction(pyfuncitem.obj):
            # Run the async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(pyfuncitem.obj(**pyfuncitem.funcargs))
            finally:
                loop.close()
            return True
    return None
