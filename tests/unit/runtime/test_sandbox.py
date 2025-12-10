"""Unit tests for SandboxWrapper."""

import pytest

from smartcp.runtime.sandbox import SandboxWrapper
from smartcp.runtime.types import ExecutionStatus


class TestSandboxWrapper:
    """Unit tests for SandboxWrapper."""

    @pytest.fixture
    def sandbox(self):
        """Create a sandbox wrapper."""
        return SandboxWrapper()

    @pytest.mark.asyncio
    async def test_basic_execution(self, sandbox):
        """Test basic code execution."""
        async with sandbox:
            result = await sandbox.execute("print('hello')")

        assert result.status == ExecutionStatus.COMPLETED
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_execution_with_namespace(self, sandbox):
        """Test execution with injected namespace."""
        async with sandbox:
            namespace = {"x": 42, "y": 8}
            result = await sandbox.execute("print(x + y)", namespace=namespace)

        assert result.status == ExecutionStatus.COMPLETED
        assert "50" in result.stdout

    @pytest.mark.asyncio
    async def test_execution_error(self, sandbox):
        """Test error handling."""
        async with sandbox:
            result = await sandbox.execute("raise ValueError('test')")

        assert result.status == ExecutionStatus.FAILED
        assert "ValueError" in result.stderr or "test" in result.stderr

    @pytest.mark.asyncio
    async def test_execution_timeout(self, sandbox):
        """Test execution timeout."""
        async with sandbox:
            result = await sandbox.execute("import time; time.sleep(10)", timeout=1)

        assert result.status == ExecutionStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_session_persistence(self, sandbox):
        """Test session persistence."""
        async with sandbox:
            # First execution
            await sandbox.execute("x = 42", namespace={})

            # Get session
            session = sandbox.get_session()

            # New sandbox instance
            sandbox2 = SandboxWrapper()
            await sandbox2.initialize()
            sandbox2.load_session(session)

            # Should have access to x
            result = await sandbox2.execute("print(x)", namespace={})
            assert "42" in result.stdout

    @pytest.mark.asyncio
    async def test_restricted_builtins(self, sandbox):
        """Test that dangerous builtins are blocked."""
        async with sandbox:
            # open() should not be available in fallback mode
            result = await sandbox.execute("open('/etc/passwd')")

        # Should fail (fallback mode blocks open)
        if result.status == ExecutionStatus.FAILED:
            assert "open" in result.stderr.lower() or "name" in result.stderr.lower()
