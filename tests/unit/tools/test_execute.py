"""Unit tests for execute tool."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.tools.execute import execute, get_runtime, set_runtime


class TestExecuteTool:
    """Unit tests for execute tool."""

    @pytest.fixture
    def runtime(self):
        """Create and wire runtime."""
        runtime = AgentRuntime()
        set_runtime(runtime)
        return runtime

    @pytest.mark.asyncio
    async def test_execute_basic(self, runtime):
        """Test basic execute function."""
        result = await execute(code="print('test')")

        assert result["status"] == "completed"
        assert "test" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_with_error(self, runtime):
        """Test execute with error."""
        result = await execute(
            code="""
try:
    await scope.session.set("x", 42)
    print("ok")
except Exception as e:
    print(f"Error: {e}")
"""
        )

        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_timeout(self, runtime):
        """Test execute with timeout."""
        result = await execute(
            code="import time; time.sleep(10)",
            timeout=1,
        )

        assert result["status"] == "timeout"

    @pytest.mark.asyncio
    async def test_get_runtime(self, runtime):
        """Test get_runtime function."""
        retrieved = get_runtime()
        assert retrieved is runtime

    @pytest.mark.asyncio
    async def test_get_runtime_not_set(self):
        """Test get_runtime when not set."""
        # Clear runtime
        set_runtime(None)

        with pytest.raises(RuntimeError, match="not initialized"):
            get_runtime()

        # Restore for other tests
        runtime = AgentRuntime()
        set_runtime(runtime)
