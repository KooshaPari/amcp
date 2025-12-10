"""Tests for SandboxWrapper."""

import pytest

from smartcp.runtime.sandbox import SandboxWrapper
from smartcp.runtime.types import ExecutionStatus


class TestSandboxWrapper:
    """Tests for SandboxWrapper class."""

    @pytest.fixture
    def sandbox(self):
        """Create a sandbox instance for testing."""
        return SandboxWrapper()

    @pytest.mark.asyncio
    async def test_basic_execution(self, sandbox):
        """Test basic code execution."""
        async with sandbox:
            result = await sandbox.execute("print('hello')")

        assert result.status == ExecutionStatus.COMPLETED
        assert "hello" in result.stdout
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_execution_with_namespace(self, sandbox):
        """Test code execution with injected namespace."""
        async with sandbox:
            namespace = {"x": 42, "y": 8}
            result = await sandbox.execute("print(x + y)", namespace=namespace)

        assert result.status == ExecutionStatus.COMPLETED
        assert "50" in result.stdout

    @pytest.mark.asyncio
    async def test_execution_error(self, sandbox):
        """Test error handling in execution."""
        async with sandbox:
            result = await sandbox.execute("raise ValueError('test error')")

        assert result.status == ExecutionStatus.FAILED
        assert "ValueError" in result.stderr or "test error" in result.stderr

    @pytest.mark.asyncio
    async def test_execution_timeout(self):
        """Test execution timeout."""
        sandbox = SandboxWrapper()

        async with sandbox:
            result = await sandbox.execute("import time; time.sleep(10)", timeout=1)

        assert result.status == ExecutionStatus.TIMEOUT
        assert "timeout" in result.stderr.lower()

    @pytest.mark.asyncio
    async def test_multiple_executions(self, sandbox):
        """Test multiple sequential executions."""
        async with sandbox:
            result1 = await sandbox.execute("x = 1; print(x)")
            result2 = await sandbox.execute("y = 2; print(y)")
            result3 = await sandbox.execute("z = 3; print(z)")

        assert result1.status == ExecutionStatus.COMPLETED
        assert result2.status == ExecutionStatus.COMPLETED
        assert result3.status == ExecutionStatus.COMPLETED
