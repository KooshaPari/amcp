"""Integration tests for full runtime system."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import ExecutionStatus


class TestRuntimeIntegration:
    """Integration tests for complete runtime system."""

    @pytest.fixture
    def runtime(self):
        """Create an agent runtime."""
        return AgentRuntime()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user", workspace_id="ws-123")

    @pytest.mark.asyncio
    async def test_full_execution_flow(self, runtime, user_ctx):
        """Test complete execution flow with all APIs."""
        code = """
# 1. Use scope API
await scope.session.set("counter", 0)
counter = await scope.session.get("counter")

# 2. Define a tool
@tool
async def increment() -> dict:
    current = await scope.session.get("counter")
    new_value = current + 1
    await scope.session.set("counter", new_value)
    return {"value": new_value}

# 3. Use the tool
result = await increment()
print(f"Counter: {result['value']}")

# 4. Use background task
async def expensive():
    import asyncio
    await asyncio.sleep(0.1)
    return "completed"

task = bg(expensive())
bg_result = await task
print(f"Background: {bg_result}")

# 5. Save a skill
await skills.save("my_skill", "# My Skill\\n\\nContent here.")

# 6. Promote value
await scope.promote("counter", "session", "permanent")
final = await scope.permanent.get("counter")
print(f"Final counter: {final}")
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED
        assert "Counter: 1" in result.output
        assert "Background: completed" in result.output
        assert "Final counter: 1" in result.output

    @pytest.mark.asyncio
    async def test_multi_user_isolation(self, runtime):
        """Test that multiple users are properly isolated."""
        user1 = UserContext(user_id="user1")
        user2 = UserContext(user_id="user2")

        code1 = """
await scope.session.set("user", "user1")
value = await scope.session.get("user")
print(value)
"""

        code2 = """
await scope.session.set("user", "user2")
value = await scope.session.get("user")
print(value)
"""

        result1 = await runtime.execute(code1, user1)
        result2 = await runtime.execute(code2, user2)

        assert result1.status == ExecutionStatus.COMPLETED
        assert result2.status == ExecutionStatus.COMPLETED
        assert "user1" in result1.output
        assert "user2" in result2.output

    @pytest.mark.asyncio
    async def test_session_persistence_across_executions(self, runtime, user_ctx):
        """Test that session persists across multiple executions."""
        # First execution
        result1 = await runtime.execute(
            code="await scope.session.set('x', 42); print('set')",
            user_ctx=user_ctx,
        )
        assert result1.status == ExecutionStatus.COMPLETED

        # Second execution - should have access to x
        result2 = await runtime.execute(
            code="x = await scope.session.get('x'); print(f'x={x}')",
            user_ctx=user_ctx,
        )
        assert result2.status == ExecutionStatus.COMPLETED
        assert "x=42" in result2.output

    @pytest.mark.asyncio
    async def test_error_recovery(self, runtime, user_ctx):
        """Test that errors don't break subsequent executions."""
        # First execution with error
        result1 = await runtime.execute(
            code="raise ValueError('test error')",
            user_ctx=user_ctx,
        )
        assert result1.status == ExecutionStatus.FAILED

        # Second execution should work fine
        result2 = await runtime.execute(
            code="print('recovered')",
            user_ctx=user_ctx,
        )
        assert result2.status == ExecutionStatus.COMPLETED
        assert "recovered" in result2.output
