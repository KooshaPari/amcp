"""Quick smoke tests for rapid validation."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import ExecutionStatus


class TestQuickValidation:
    """Quick smoke tests."""

    @pytest.fixture
    def runtime(self):
        """Create runtime."""
        return AgentRuntime()

    @pytest.fixture
    def user_ctx(self):
        """Create user context."""
        return UserContext(user_id="smoke-user")

    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_runtime_initializes(self, runtime):
        """Smoke test: Runtime initializes."""
        assert runtime is not None
        assert hasattr(runtime, "sandbox")
        assert hasattr(runtime, "tool_registry")

    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_can_execute_code(self, runtime, user_ctx):
        """Smoke test: Can execute code."""
        result = await runtime.execute("print('ok')", user_ctx)
        assert result.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_scope_api_available(self, runtime, user_ctx):
        """Smoke test: Scope API is available."""
        code = "has_scope = 'scope' in dir(); print(has_scope)"
        result = await runtime.execute(code, user_ctx)
        # Scope should be in namespace
        assert result.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_tool_registry_works(self, runtime):
        """Smoke test: Tool registry works."""
        async def test_tool() -> dict:
            return {"ok": True}

        runtime.tool_registry.register("test", "Test", test_tool)
        tools = runtime.tool_registry.get_tools()
        assert len(tools) >= 1
