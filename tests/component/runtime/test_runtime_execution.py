"""Component tests for AgentRuntime execution with all components."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import ExecutionStatus, NamespaceConfig


class TestRuntimeExecution:
    """Component tests for full runtime execution."""

    @pytest.fixture
    def runtime(self):
        """Create an agent runtime."""
        return AgentRuntime()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user", workspace_id="ws-123")

    @pytest.mark.asyncio
    async def test_execution_with_scope(self, runtime, user_ctx):
        """Test execution with scope API."""
        code = """
await scope.session.set("count", 0)
count = await scope.session.get("count")
print(f"Count: {count}")
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED
        assert "Count: 0" in result.output

    @pytest.mark.asyncio
    async def test_execution_with_tools(self, runtime, user_ctx):
        """Test execution with tools in namespace."""
        # Register a tool first
        async def test_tool(param: str) -> dict:
            return {"result": param.upper()}

        runtime.tool_registry.register("test_tool", "Test", test_tool)

        code = """
result = await test_tool("hello")
print(result["result"])
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED
        assert "HELLO" in result.output

    @pytest.mark.asyncio
    async def test_execution_with_skills(self, runtime, user_ctx):
        """Test execution with skills API."""
        code = """
await skills.save("test_skill", "# Test Skill")
skills_list = await skills.list()
print(f"Skills: {skills_list}")
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execution_with_background_tasks(self, runtime, user_ctx):
        """Test execution with background tasks."""
        code = """
async def slow_task():
    import asyncio
    await asyncio.sleep(0.1)
    return "done"

task = bg(slow_task())
result = await task
print(result)
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED
        assert "done" in result.output

    @pytest.mark.asyncio
    async def test_execution_with_tool_decorator(self, runtime, user_ctx):
        """Test execution with @tool decorator."""
        code = """
@tool
async def my_custom_tool(x: int) -> dict:
    '''Custom tool.'''
    return {"doubled": x * 2}

result = await my_custom_tool(21)
print(result["doubled"])
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED
        assert "42" in result.output

    @pytest.mark.asyncio
    async def test_full_workflow(self, runtime, user_ctx):
        """Test a complete workflow."""
        code = """
# Use scope
await scope.session.set("step", 1)
step = await scope.session.get("step")

# Use background task
async def process():
    return step * 2

task = bg(process())
result = await task

# Promote to permanent
await scope.session.set("final_result", result)
await scope.promote("final_result", "session", "permanent")

print(f"Final: {result}")
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED
        assert "Final: 2" in result.output
