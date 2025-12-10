"""Performance tests for scope operations."""

import asyncio
import time

import pytest

from smartcp.runtime.scope.manager import ScopeManager
from smartcp.runtime.scope.types import ScopeLevel
from smartcp.runtime.types import UserContext


class TestScopePerformance:
    """Performance tests for scope operations."""

    @pytest.fixture
    def manager(self):
        """Create a scope manager."""
        return ScopeManager(storage_backend="memory")

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="perf-user")

    @pytest.mark.asyncio
    async def test_many_set_operations(self, manager, user_ctx):
        """Test performance of many set operations."""
        start_time = time.time()

        for i in range(1000):
            await manager.set(ScopeLevel.SESSION, f"key{i}", f"value{i}", user_ctx)

        elapsed = time.time() - start_time

        # Should complete 1000 sets in reasonable time (< 1 second for memory)
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_many_get_operations(self, manager, user_ctx):
        """Test performance of many get operations."""
        # Set up data
        for i in range(100):
            await manager.set(ScopeLevel.SESSION, f"key{i}", f"value{i}", user_ctx)

        start_time = time.time()

        for i in range(1000):
            await manager.get(ScopeLevel.SESSION, f"key{i % 100}", user_ctx)

        elapsed = time.time() - start_time

        # Should complete 1000 gets quickly (< 0.5 seconds for memory)
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_concurrent_scope_operations(self, manager):
        """Test concurrent scope operations."""
        users = [UserContext(user_id=f"user-{i}") for i in range(10)]

        async def operations(user_ctx):
            for i in range(10):
                await manager.set(ScopeLevel.SESSION, f"key{i}", f"value{i}", user_ctx)
                await manager.get(ScopeLevel.SESSION, f"key{i}", user_ctx)

        start_time = time.time()
        await asyncio.gather(*[operations(u) for u in users])
        elapsed = time.time() - start_time

        # Should handle concurrent operations efficiently
        assert elapsed < 2.0
