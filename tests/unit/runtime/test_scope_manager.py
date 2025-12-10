"""Unit tests for ScopeManager."""

import pytest

from smartcp.runtime.scope.manager import ScopeManager
from smartcp.runtime.scope.types import ScopeLevel
from smartcp.runtime.types import UserContext


class TestScopeManager:
    """Unit tests for ScopeManager."""

    @pytest.fixture
    def manager(self):
        """Create a scope manager with memory storage."""
        return ScopeManager(storage_backend="memory")

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user", workspace_id="ws-123")

    @pytest.mark.asyncio
    async def test_set_and_get(self, manager, user_ctx):
        """Test setting and getting values."""
        await manager.set(ScopeLevel.SESSION, "key1", "value1", user_ctx)

        value = await manager.get(ScopeLevel.SESSION, "key1", user_ctx)
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_default(self, manager, user_ctx):
        """Test getting with default value."""
        value = await manager.get(ScopeLevel.SESSION, "nonexistent", user_ctx, default="default")
        assert value == "default"

    @pytest.mark.asyncio
    async def test_delete(self, manager, user_ctx):
        """Test deleting values."""
        await manager.set(ScopeLevel.SESSION, "key1", "value1", user_ctx)

        deleted = await manager.delete(ScopeLevel.SESSION, "key1", user_ctx)
        assert deleted is True

        value = await manager.get(ScopeLevel.SESSION, "key1", user_ctx)
        assert value is None

    @pytest.mark.asyncio
    async def test_keys(self, manager, user_ctx):
        """Test listing keys."""
        await manager.set(ScopeLevel.SESSION, "key1", "value1", user_ctx)
        await manager.set(ScopeLevel.SESSION, "key2", "value2", user_ctx)
        await manager.set(ScopeLevel.SESSION, "key3", "value3", user_ctx)

        keys = await manager.keys(ScopeLevel.SESSION, user_ctx)
        assert set(keys) == {"key1", "key2", "key3"}

    @pytest.mark.asyncio
    async def test_promote(self, manager, user_ctx):
        """Test promoting value to higher scope."""
        await manager.set(ScopeLevel.SESSION, "key1", "value1", user_ctx)

        promoted = await manager.promote("key1", ScopeLevel.SESSION, ScopeLevel.PERMANENT, user_ctx)
        assert promoted is True

        # Should be in permanent, not session
        assert await manager.get(ScopeLevel.PERMANENT, "key1", user_ctx) == "value1"
        assert await manager.get(ScopeLevel.SESSION, "key1", user_ctx) is None

    @pytest.mark.asyncio
    async def test_demote(self, manager, user_ctx):
        """Test demoting value to lower scope."""
        await manager.set(ScopeLevel.PERMANENT, "key1", "value1", user_ctx)

        demoted = await manager.demote("key1", ScopeLevel.PERMANENT, ScopeLevel.SESSION, user_ctx)
        assert demoted is True

        # Should be in session, not permanent
        assert await manager.get(ScopeLevel.SESSION, "key1", user_ctx) == "value1"
        assert await manager.get(ScopeLevel.PERMANENT, "key1", user_ctx) is None

    @pytest.mark.asyncio
    async def test_scope_isolation(self, manager):
        """Test that different scope levels are isolated."""
        user1 = UserContext(user_id="user1")
        user2 = UserContext(user_id="user2")

        await manager.set(ScopeLevel.SESSION, "key1", "user1_value", user1)
        await manager.set(ScopeLevel.SESSION, "key1", "user2_value", user2)

        assert await manager.get(ScopeLevel.SESSION, "key1", user1) == "user1_value"
        assert await manager.get(ScopeLevel.SESSION, "key1", user2) == "user2_value"

    @pytest.mark.asyncio
    async def test_level_isolation(self, manager, user_ctx):
        """Test that different levels are isolated."""
        await manager.set(ScopeLevel.SESSION, "key1", "session_value", user_ctx)
        await manager.set(ScopeLevel.PERMANENT, "key1", "permanent_value", user_ctx)

        assert await manager.get(ScopeLevel.SESSION, "key1", user_ctx) == "session_value"
        assert await manager.get(ScopeLevel.PERMANENT, "key1", user_ctx) == "permanent_value"
