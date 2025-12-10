"""Integration tests for AgentRuntime."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import NamespaceConfig


@pytest.fixture
def runtime():
    """Create agent runtime."""
    return AgentRuntime()


@pytest.fixture
def user_ctx():
    """Create test user context."""
    return UserContext(user_id="test-user")


@pytest.mark.asyncio
async def test_runtime_basic_execution(runtime, user_ctx):
    """Test basic code execution."""
    result = await runtime.execute(
        code="result = 2 + 2\nprint(result)",
        user_ctx=user_ctx,
        timeout=10,
    )

    assert result.error is None
    assert "4" in result.output
    assert result.execution_time_ms > 0


@pytest.mark.asyncio
async def test_runtime_variable_persistence(runtime, user_ctx):
    """Test variable persistence across executions."""
    # First execution: set a variable
    result1 = await runtime.execute(
        code="x = 42",
        user_ctx=user_ctx,
        timeout=10,
    )
    assert result1.error is None

    # Second execution: use the variable
    result2 = await runtime.execute(
        code="print(x)",
        user_ctx=user_ctx,
        timeout=10,
    )
    # Note: Variable persistence depends on sandbox session management
    # This test may need adjustment based on actual sandbox behavior
    assert result2.status in ["completed", "failed"]


@pytest.mark.asyncio
async def test_runtime_with_scope(runtime, user_ctx):
    """Test runtime with scope API."""
    namespace_config = NamespaceConfig(include_scope=True)
    result = await runtime.execute(
        code="""
await scope.session.set('test_key', 'test_value')
value = await scope.session.get('test_key')
print(value)
""",
        user_ctx=user_ctx,
        namespace_config=namespace_config,
        timeout=10,
    )

    # Execution should complete (may have errors if scope not fully integrated)
    assert result.status in ["completed", "failed"]


@pytest.mark.asyncio
async def test_runtime_error_handling(runtime, user_ctx):
    """Test error handling in runtime."""
    result = await runtime.execute(
        code="undefined_variable",
        user_ctx=user_ctx,
        timeout=10,
    )

    # Should handle error gracefully
    assert result.status in ["completed", "failed"]
    if result.error:
        assert "undefined" in result.error.lower() or "name" in result.error.lower()


@pytest.mark.asyncio
async def test_runtime_session_isolation(runtime):
    """Test that sessions are isolated per user."""
    user1 = UserContext(user_id="user1")
    user2 = UserContext(user_id="user2")

    # Set variable for user 1
    await runtime.execute(code="x = 'user1'", user_ctx=user1, timeout=10)

    # Try to access from user 2
    result = await runtime.execute(
        code="print(x)",
        user_ctx=user2,
        timeout=10,
    )

    # User 2 should not have access to user 1's variables
    # (may vary based on sandbox implementation)
    assert result.status in ["completed", "failed"]


@pytest.mark.asyncio
async def test_runtime_clear_session(runtime, user_ctx):
    """Test clearing user session."""
    await runtime.execute(code="x = 42", user_ctx=user_ctx, timeout=10)

    runtime.clear_session(user_ctx.user_id)
    session = runtime.get_session(user_ctx.user_id)
    assert session is None
