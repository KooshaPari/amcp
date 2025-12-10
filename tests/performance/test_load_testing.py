"""Load testing for runtime system."""

import asyncio
import statistics
import time

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import ExecutionStatus


class TestLoadTesting:
    """Load tests for runtime system."""

    @pytest.fixture
    def runtime(self):
        """Create an agent runtime."""
        return AgentRuntime()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_high_concurrency(self, runtime):
        """Test high concurrent load."""
        num_users = 50
        users = [UserContext(user_id=f"load-user-{i}") for i in range(num_users)]

        async def user_execution(user_ctx):
            return await runtime.execute(
                code="x = 1; print(x)",
                user_ctx=user_ctx,
            )

        start_time = time.time()
        results = await asyncio.gather(*[user_execution(u) for u in users])
        elapsed = time.time() - start_time

        # All should succeed
        success_count = sum(1 for r in results if r.status == ExecutionStatus.COMPLETED)
        assert success_count == num_users

        # Should complete in reasonable time
        assert elapsed < 10.0  # 50 concurrent executions in < 10 seconds

        # Calculate throughput
        throughput = num_users / elapsed
        print(f"Throughput: {throughput:.2f} executions/second")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_load(self, runtime):
        """Test sustained load over time."""
        user_ctx = UserContext(user_id="sustained-user")

        execution_times = []
        start_time = time.time()
        duration = 5.0  # Run for 5 seconds

        while time.time() - start_time < duration:
            exec_start = time.time()
            result = await runtime.execute(
                code="x = 1; print(x)",
                user_ctx=user_ctx,
            )
            exec_time = time.time() - exec_start
            execution_times.append(exec_time)

            assert result.status == ExecutionStatus.COMPLETED

        # Calculate statistics
        if execution_times:
            avg_time = statistics.mean(execution_times)
            p95_time = statistics.quantiles(execution_times, n=20)[18] if len(execution_times) > 1 else avg_time

            print(f"Executions: {len(execution_times)}")
            print(f"Average time: {avg_time:.3f}s")
            print(f"P95 time: {p95_time:.3f}s")

            # Average should be reasonable
            assert avg_time < 1.0  # Average < 1 second

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_memory_under_load(self, runtime):
        """Test memory usage under load."""
        import sys

        users = [UserContext(user_id=f"mem-user-{i}") for i in range(100)]

        # Execute for all users
        await asyncio.gather(*[
            runtime.execute(code="x = 1", user_ctx=user)
            for user in users
        ])

        # Check session cache size
        cache_size = len(runtime._session_cache)
        assert cache_size <= 100  # Should be bounded

        # Check memory usage (rough estimate)
        import gc
        gc.collect()

        # Session cache should not grow unbounded
        assert sys.getsizeof(runtime._session_cache) < 10 * 1024 * 1024  # < 10MB
