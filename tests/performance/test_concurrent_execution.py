"""Performance tests for concurrent execution."""

import asyncio
import time

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import ExecutionStatus


class TestConcurrentExecution:
    """Performance tests for concurrent execution."""

    @pytest.fixture
    def runtime(self):
        """Create an agent runtime."""
        return AgentRuntime()

    @pytest.mark.asyncio
    async def test_concurrent_executions(self, runtime):
        """Test concurrent executions from different users."""
        users = [UserContext(user_id=f"user-{i}") for i in range(10)]

        async def execute_for_user(user_ctx):
            return await runtime.execute(
                code=f"print('user: {user_ctx.user_id}')",
                user_ctx=user_ctx,
            )

        start_time = time.time()
        results = await asyncio.gather(*[execute_for_user(u) for u in users])
        elapsed = time.time() - start_time

        # All should succeed
        assert all(r.status == ExecutionStatus.COMPLETED for r in results)

        # Should complete reasonably fast (< 5 seconds for 10 concurrent)
        assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_sequential_vs_concurrent(self, runtime):
        """Compare sequential vs concurrent execution time."""
        users = [UserContext(user_id=f"user-{i}") for i in range(5)]

        # Sequential
        start = time.time()
        for user in users:
            await runtime.execute(code="print('test')", user_ctx=user)
        sequential_time = time.time() - start

        # Concurrent
        start = time.time()
        await asyncio.gather(*[
            runtime.execute(code="print('test')", user_ctx=user)
            for user in users
        ])
        concurrent_time = time.time() - start

        # Concurrent should be faster
        assert concurrent_time < sequential_time

    @pytest.mark.asyncio
    async def test_many_executions(self, runtime):
        """Test many sequential executions."""
        user_ctx = UserContext(user_id="perf-user")

        start_time = time.time()
        for i in range(50):
            result = await runtime.execute(
                code=f"x = {i}; print(x)",
                user_ctx=user_ctx,
            )
            assert result.status == ExecutionStatus.COMPLETED

        elapsed = time.time() - start_time

        # Should complete 50 executions in reasonable time
        assert elapsed < 30.0  # Less than 30 seconds for 50 executions
