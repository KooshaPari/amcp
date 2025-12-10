"""Unit tests for scope storage backends."""

import pytest

from smartcp.runtime.scope.storage import InMemoryStorage, create_storage
from smartcp.runtime.scope.types import ScopeLevel
from smartcp.runtime.types import UserContext


class TestInMemoryStorage:
    """Unit tests for InMemoryStorage."""

    @pytest.fixture
    def storage(self):
        """Create in-memory storage."""
        return InMemoryStorage()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user", workspace_id="ws-123")

    @pytest.mark.asyncio
    async def test_set_and_get(self, storage, user_ctx):
        """Test setting and getting values."""
        await storage.set(ScopeLevel.SESSION, "key1", "value1", user_ctx)

        value = await storage.get(ScopeLevel.SESSION, "key1", user_ctx)
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_default(self, storage, user_ctx):
        """Test getting with default."""
        value = await storage.get(ScopeLevel.SESSION, "nonexistent", user_ctx, default="default")
        assert value == "default"

    @pytest.mark.asyncio
    async def test_delete(self, storage, user_ctx):
        """Test deleting values."""
        await storage.set(ScopeLevel.SESSION, "key1", "value1", user_ctx)

        deleted = await storage.delete(ScopeLevel.SESSION, "key1", user_ctx)
        assert deleted is True

        value = await storage.get(ScopeLevel.SESSION, "key1", user_ctx)
        assert value is None

    @pytest.mark.asyncio
    async def test_keys(self, storage, user_ctx):
        """Test listing keys."""
        await storage.set(ScopeLevel.SESSION, "key1", "value1", user_ctx)
        await storage.set(ScopeLevel.SESSION, "key2", "value2", user_ctx)

        keys = await storage.keys(ScopeLevel.SESSION, user_ctx)
        assert set(keys) == {"key1", "key2"}

    @pytest.mark.asyncio
    async def test_user_isolation(self, storage):
        """Test that different users are isolated."""
        user1 = UserContext(user_id="user1")
        user2 = UserContext(user_id="user2")

        await storage.set(ScopeLevel.SESSION, "key1", "user1_value", user1)
        await storage.set(ScopeLevel.SESSION, "key1", "user2_value", user2)

        assert await storage.get(ScopeLevel.SESSION, "key1", user1) == "user1_value"
        assert await storage.get(ScopeLevel.SESSION, "key1", user2) == "user2_value"

    @pytest.mark.asyncio
    async def test_level_isolation(self, storage, user_ctx):
        """Test that different levels are isolated."""
        await storage.set(ScopeLevel.SESSION, "key1", "session", user_ctx)
        await storage.set(ScopeLevel.PERMANENT, "key1", "permanent", user_ctx)

        assert await storage.get(ScopeLevel.SESSION, "key1", user_ctx) == "session"
        assert await storage.get(ScopeLevel.PERMANENT, "key1", user_ctx) == "permanent"


class TestCreateStorage:
    """Tests for create_storage factory."""

    def test_create_memory(self):
        """Test creating memory storage."""
        storage = create_storage("memory")
        assert isinstance(storage, InMemoryStorage)

    def test_create_invalid(self):
        """Test creating invalid storage backend."""
        with pytest.raises(ValueError, match="Unknown storage backend"):
            create_storage("invalid")
