"""Unit tests for AgentRuntime."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import ExecutionStatus, NamespaceConfig


class TestAgentRuntime:
    """Unit tests for AgentRuntime."""

    @pytest.fixture
    def runtime(self):
        """Create an agent runtime."""
        return AgentRuntime()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.mark.asyncio
    async def test_basic_execution(self, runtime, user_ctx):
        """Test basic code execution."""
        result = await runtime.execute(
            code="print('hello')",
            user_ctx=user_ctx,
        )

        assert result.status == ExecutionStatus.COMPLETED
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_execution_with_variables(self, runtime, user_ctx):
        """Test execution with variables."""
        result = await runtime.execute(
            code="x = 42; y = 8; print(x * y)",
            user_ctx=user_ctx,
        )

        assert result.status == ExecutionStatus.COMPLETED
        assert "336" in result.output

    @pytest.mark.asyncio
    async def test_execution_error(self, runtime, user_ctx):
        """Test error handling."""
        result = await runtime.execute(
            code="1/0",
            user_ctx=user_ctx,
        )

        assert result.status == ExecutionStatus.FAILED
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_timeout(self, runtime, user_ctx):
        """Test execution timeout."""
        result = await runtime.execute(
            code="import time; time.sleep(5)",
            user_ctx=user_ctx,
            timeout=1,
        )

        assert result.status == ExecutionStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_session_persistence(self, runtime, user_ctx):
        """Test session persistence across executions."""
        # First execution
        await runtime.execute(code="x = 1", user_ctx=user_ctx)

        # Session should be cached
        session = runtime.get_session(user_ctx.user_id)
        assert session is not None

    @pytest.mark.asyncio
    async def test_clear_session(self, runtime, user_ctx):
        """Test clearing session."""
        await runtime.execute(code="x = 1", user_ctx=user_ctx)

        runtime.clear_session(user_ctx.user_id)

        session = runtime.get_session(user_ctx.user_id)
        assert session is None

    @pytest.mark.asyncio
    async def test_custom_namespace_config(self, runtime, user_ctx):
        """Test execution with custom namespace config."""
        config = NamespaceConfig(include_tools=False, include_scope=False)
        result = await runtime.execute(
            code="print('test')",
            user_ctx=user_ctx,
            namespace_config=config,
        )

        assert result.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_user_isolation(self, runtime):
        """Test that different users have isolated sessions."""
        user1 = UserContext(user_id="user1")
        user2 = UserContext(user_id="user2")

        await runtime.execute(code="x = 1", user_ctx=user1)
        await runtime.execute(code="x = 2", user_ctx=user2)

        # Both should have sessions
        assert runtime.get_session(user1.user_id) is not None
        assert runtime.get_session(user2.user_id) is not None
