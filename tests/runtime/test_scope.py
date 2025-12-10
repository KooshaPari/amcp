"""Tests for scope management."""

import pytest

from smartcp.runtime.scope import ScopeAPI, ScopeManager
from smartcp.runtime.scope.types import ScopeLevel
from smartcp.runtime.types import UserContext


@pytest.fixture
def scope_manager():
    """Create scope manager with in-memory storage."""
    return ScopeManager(storage_backend="memory")


@pytest.fixture
def user_ctx():
    """Create test user context."""
    return UserContext(user_id="test-user", workspace_id="test-ws")


@pytest.fixture
def scope_api(scope_manager, user_ctx):
    """Create scope API."""
    return ScopeAPI(scope_manager, user_ctx)


@pytest.mark.asyncio
async def test_scope_set_get(scope_api):
    """Test setting and getting values from scope."""
    await scope_api.session.set("key1", "value1")
    value = await scope_api.session.get("key1")
    assert value == "value1"


@pytest.mark.asyncio
async def test_scope_multiple_levels(scope_api):
    """Test different scope levels."""
    await scope_api.block.set("block_key", "block_value")
    await scope_api.session.set("session_key", "session_value")
    await scope_api.permanent.set("permanent_key", "permanent_value")

    assert await scope_api.block.get("block_key") == "block_value"
    assert await scope_api.session.get("session_key") == "session_value"
    assert await scope_api.permanent.get("permanent_key") == "permanent_value"


@pytest.mark.asyncio
async def test_scope_delete(scope_api):
    """Test deleting values from scope."""
    await scope_api.session.set("key", "value")
    assert await scope_api.session.get("key") == "value"

    deleted = await scope_api.session.delete("key")
    assert deleted is True
    assert await scope_api.session.get("key") is None


@pytest.mark.asyncio
async def test_scope_keys(scope_api):
    """Test listing keys in scope."""
    await scope_api.session.set("key1", "value1")
    await scope_api.session.set("key2", "value2")

    keys = await scope_api.session.keys()
    assert "key1" in keys
    assert "key2" in keys


@pytest.mark.asyncio
async def test_scope_promote(scope_api):
    """Test promoting values to higher scope."""
    await scope_api.session.set("important", "data")
    success = await scope_api.promote("important", "session", "permanent")
    assert success is True

    # Should be accessible from permanent scope
    value = await scope_api.permanent.get("important")
    assert value == "data"


@pytest.mark.asyncio
async def test_scope_demote(scope_api):
    """Test demoting values to lower scope."""
    await scope_api.permanent.set("temp", "data")
    success = await scope_api.demote("temp", "permanent", "session")
    assert success is True

    value = await scope_api.session.get("temp")
    assert value == "data"


@pytest.mark.asyncio
async def test_scope_hierarchy_search(scope_manager, user_ctx):
    """Test that get searches upward through hierarchy."""
    # Set value at permanent level
    await scope_manager.set(ScopeLevel.PERMANENT, "config", "permanent_value", user_ctx)

    # Get from session level should find permanent value
    value = await scope_manager.get(ScopeLevel.SESSION, "config", user_ctx)
    assert value == "permanent_value"


@pytest.mark.asyncio
async def test_scope_isolation(scope_manager):
    """Test that scopes are isolated per user."""
    user1 = UserContext(user_id="user1")
    user2 = UserContext(user_id="user2")

    await scope_manager.set(ScopeLevel.SESSION, "key", "user1_value", user1)
    await scope_manager.set(ScopeLevel.SESSION, "key", "user2_value", user2)

    assert await scope_manager.get(ScopeLevel.SESSION, "key", user1) == "user1_value"
    assert await scope_manager.get(ScopeLevel.SESSION, "key", user2) == "user2_value"
