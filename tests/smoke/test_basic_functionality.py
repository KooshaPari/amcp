"""Smoke tests for basic functionality."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import ExecutionStatus


class TestBasicFunctionality:
    """Smoke tests for basic runtime functionality."""

    @pytest.fixture
    def runtime(self):
        """Create an agent runtime."""
        return AgentRuntime()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="smoke-test-user")

    @pytest.mark.asyncio
    async def test_can_execute_code(self, runtime, user_ctx):
        """Smoke test: Can execute basic code."""
        result = await runtime.execute("print('smoke test')", user_ctx)
        assert result.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_can_use_scope(self, runtime, user_ctx):
        """Smoke test: Can use scope API."""
        code = "await scope.session.set('test', 42); print('ok')"
        result = await runtime.execute(code, user_ctx)
        assert result.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_can_use_tools(self, runtime, user_ctx):
        """Smoke test: Can use tools."""
        async def test_tool() -> dict:
            return {"status": "ok"}

        runtime.tool_registry.register("test", "Test", test_tool)

        code = "result = await test(); print(result['status'])"
        result = await runtime.execute(code, user_ctx)
        assert result.status == ExecutionStatus.COMPLETED
        assert "ok" in result.output

    @pytest.mark.asyncio
    async def test_can_use_background_tasks(self, runtime, user_ctx):
        """Smoke test: Can use background tasks."""
        code = """
async def task():
    return "done"
result = await bg(task())
print(result)
"""
        result = await runtime.execute(code, user_ctx)
        assert result.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_can_define_tools(self, runtime, user_ctx):
        """Smoke test: Can define tools with decorator."""
        code = """
@tool
async def my_tool():
    return {"ok": True}
result = await my_tool()
print(result["ok"])
"""
        result = await runtime.execute(code, user_ctx)
        assert result.status == ExecutionStatus.COMPLETED
