"""End-to-end tests for execute tool."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.tools.execute import execute, set_runtime


class TestExecuteToolE2E:
    """End-to-end tests for execute tool."""

    @pytest.fixture
    def runtime(self):
        """Create and wire runtime."""
        runtime = AgentRuntime()
        set_runtime(runtime)
        return runtime

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="e2e-user")

    @pytest.mark.asyncio
    async def test_execute_simple_code(self, runtime):
        """Test executing simple code via execute tool."""
        result = await execute(
            code="print('hello world')",
            timeout=30,
        )

        assert result["status"] == "completed"
        assert "hello world" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_with_scope(self, runtime):
        """Test executing code that uses scope API."""
        result = await execute(
            code="""
await scope.session.set("name", "Alice")
name = await scope.session.get("name")
print(f"Hello, {name}")
""",
            timeout=30,
        )

        assert result["status"] == "completed"
        assert "Hello, Alice" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_with_tools(self, runtime):
        """Test executing code that uses tools."""
        # Register a tool first
        async def greet_tool(name: str) -> dict:
            return {"greeting": f"Hello, {name}!"}

        runtime.tool_registry.register("greet", "Greet tool", greet_tool)

        result = await execute(
            code="""
result = await greet("Bob")
print(result["greeting"])
""",
            timeout=30,
        )

        assert result["status"] == "completed"
        assert "Hello, Bob!" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_with_background_task(self, runtime):
        """Test executing code with background tasks."""
        result = await execute(
            code="""
async def slow_task():
    import asyncio
    await asyncio.sleep(0.1)
    return "done"

task = bg(slow_task())
result = await task
print(result)
""",
            timeout=30,
        )

        assert result["status"] == "completed"
        assert "done" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, runtime):
        """Test error handling in execute tool."""
        result = await execute(
            code="raise ValueError('test error')",
            timeout=30,
        )

        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "ValueError" in result["error"] or "test error" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_timeout(self, runtime):
        """Test timeout handling."""
        result = await execute(
            code="import time; time.sleep(10)",
            timeout=1,
        )

        assert result["status"] == "timeout"
