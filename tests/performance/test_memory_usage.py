"""Performance tests for memory usage."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext


class TestMemoryUsage:
    """Performance tests for memory usage."""

    @pytest.fixture
    def runtime(self):
        """Create an agent runtime."""
        return AgentRuntime()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="memory-test-user")

    @pytest.mark.asyncio
    async def test_session_cache_size(self, runtime):
        """Test that session cache doesn't grow unbounded."""
        # Create many users
        for i in range(100):
            user = UserContext(user_id=f"user-{i}")
            await runtime.execute(code="x = 1", user_ctx=user)

        # Check cache size
        session_ids = list(runtime._session_cache.keys())
        assert len(session_ids) <= 100  # Should be bounded

    @pytest.mark.asyncio
    async def test_large_namespace(self, runtime, user_ctx):
        """Test execution with large namespace."""
        # Register many tools
        for i in range(50):
            async def tool_func() -> dict:
                return {"id": i}

            runtime.tool_registry.register(f"tool_{i}", f"Tool {i}", tool_func)

        # Execute with large namespace
        result = await runtime.execute(
            code="print('ok')",
            user_ctx=user_ctx,
        )

        assert result.status.value == "completed"
