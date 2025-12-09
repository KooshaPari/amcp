"""
Shared fixtures for optimization tests.

Provides common fixtures used across all optimization test modules.
"""

import asyncio
import pytest
import sys
import os
from pathlib import Path

# Ensure project root is in path (already handled by root conftest.py, but ensure here too)
project_root = Path(__file__).parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_tool_executor():
    """Create a mock tool executor for testing."""

    async def execute(tool_name: str, params: dict):
        """Mock tool execution."""
        # Simulate different tool behaviors
        if "fail" in tool_name.lower():
            raise ValueError(f"Mock failure for {tool_name}")

        if "slow" in tool_name.lower():
            await asyncio.sleep(0.1)

        return {"success": True, "result": f"Result from {tool_name}", "params": params}

    return execute


@pytest.fixture
def mock_simple_executor():
    """Create a simple mock executor that always succeeds."""

    async def execute(tool_name: str, params: dict):
        """Simple mock that returns immediately."""
        return {"success": True, "data": f"Data from {tool_name}"}

    return execute


@pytest.fixture
def mock_failing_executor():
    """Create a mock executor that always fails."""

    async def execute(tool_name: str, params: dict):
        """Mock that always raises an exception."""
        raise RuntimeError(f"Mock failure for {tool_name}")

    return execute


@pytest.fixture(autouse=False)
def cleanup_event_loop():
    """Ensure clean event loop for each test."""
    yield
    # Cleanup any pending tasks and force garbage collection
    try:
        loop = asyncio.get_event_loop()
        pending = asyncio.all_tasks(loop)
        for task in pending:
            if not task.done():
                task.cancel()
        # Wait briefly for cancellations
        if pending:
            asyncio.wait(pending, timeout=0.1, return_when=asyncio.ALL_COMPLETED)
    except (RuntimeError, asyncio.TimeoutError):
        pass
    finally:
        # Force garbage collection to free memory
        import gc
        gc.collect()
