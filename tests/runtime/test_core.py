"""Tests for AgentRuntime core."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import ExecutionStatus, NamespaceConfig


class TestAgentRuntime:
    """Tests for AgentRuntime class."""

    @pytest.fixture
    def runtime(self):
        """Create a runtime instance for testing."""
        return AgentRuntime()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context for testing."""
        return UserContext(user_id="test-user-123")

    @pytest.mark.asyncio
    async def test_basic_execution(self, runtime, user_ctx):
        """Test basic code execution through runtime."""
        result = await runtime.execute(
            code="print('hello from runtime')",
            user_ctx=user_ctx,
        )

        assert result.status == ExecutionStatus.COMPLETED
        assert "hello from runtime" in result.output

    @pytest.mark.asyncio
    async def test_execution_with_variables(self, runtime, user_ctx):
        """Test execution with variable definitions."""
        result = await runtime.execute(
            code="x = 42; y = 8; print(x * y)",
            user_ctx=user_ctx,
        )

        assert result.status == ExecutionStatus.COMPLETED
        assert "336" in result.output

    @pytest.mark.asyncio
    async def test_execution_error_handling(self, runtime, user_ctx):
        """Test error handling in runtime."""
        result = await runtime.execute(
            code="1/0",
            user_ctx=user_ctx,
        )

        assert result.status == ExecutionStatus.FAILED
        assert result.error is not None
        assert "ZeroDivision" in result.error

    @pytest.mark.asyncio
    async def test_clear_session(self, runtime, user_ctx):
        """Test clearing user session."""
        # Create some session state
        await runtime.execute(code="x = 1", user_ctx=user_ctx)

        # Clear session
        runtime.clear_session(user_ctx.user_id)

        # Verify session is cleared
        session = runtime.get_session(user_ctx.user_id)
        assert session is None

    @pytest.mark.asyncio
    async def test_timeout_override(self, runtime, user_ctx):
        """Test timeout override parameter."""
        # Use a very short timeout
        result = await runtime.execute(
            code="import time; time.sleep(5)",
            user_ctx=user_ctx,
            timeout=1,
        )

        assert result.status == ExecutionStatus.TIMEOUT


class TestNamespaceConfig:
    """Tests for NamespaceConfig."""

    def test_default_config(self):
        """Test default namespace configuration."""
        config = NamespaceConfig()
        assert config.include_tools is True
        assert config.include_scope is True
        assert config.include_mcp is False
        assert config.include_skills is False
        assert config.include_background is False
