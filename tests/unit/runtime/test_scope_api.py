"""Unit tests for ScopeAPI."""

import pytest

from smartcp.runtime.scope.api import ScopeAPI, ScopeLevelAccessor
from smartcp.runtime.scope.manager import ScopeManager
from smartcp.runtime.scope.types import ScopeLevel
from smartcp.runtime.types import UserContext


class TestScopeLevelAccessor:
    """Unit tests for ScopeLevelAccessor."""

    @pytest.fixture
    def manager(self):
        """Create a scope manager."""
        return ScopeManager(storage_backend="memory")

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def accessor(self, manager, user_ctx):
        """Create a scope level accessor."""
        return ScopeLevelAccessor(ScopeLevel.SESSION, manager, user_ctx)

    @pytest.mark.asyncio
    async def test_get(self, accessor):
        """Test getting values."""
        await accessor.set("key1", "value1")
        value = await accessor.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_set(self, accessor):
        """Test setting values."""
        await accessor.set("key1", "value1")
        value = await accessor.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_delete(self, accessor):
        """Test deleting values."""
        await accessor.set("key1", "value1")
        deleted = await accessor.delete("key1")
        assert deleted is True

        value = await accessor.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_keys(self, accessor):
        """Test listing keys."""
        await accessor.set("key1", "value1")
        await accessor.set("key2", "value2")

        keys = await accessor.keys()
        assert set(keys) == {"key1", "key2"}


class TestScopeAPI:
    """Unit tests for ScopeAPI."""

    @pytest.fixture
    def manager(self):
        """Create a scope manager."""
        return ScopeManager(storage_backend="memory")

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def scope_api(self, manager, user_ctx):
        """Create a scope API."""
        return ScopeAPI(manager, user_ctx)

    @pytest.mark.asyncio
    async def test_level_accessors(self, scope_api):
        """Test all level accessors exist."""
        assert hasattr(scope_api, "block")
        assert hasattr(scope_api, "iteration")
        assert hasattr(scope_api, "tool_call")
        assert hasattr(scope_api, "prompt_chain")
        assert hasattr(scope_api, "session")
        assert hasattr(scope_api, "phase")
        assert hasattr(scope_api, "project")
        assert hasattr(scope_api, "workspace")
        assert hasattr(scope_api, "organization")
        assert hasattr(scope_api, "global_")
        assert hasattr(scope_api, "permanent")

    @pytest.mark.asyncio
    async def test_session_accessor(self, scope_api):
        """Test session level accessor."""
        await scope_api.session.set("key1", "value1")
        value = await scope_api.session.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_promote(self, scope_api):
        """Test promoting values."""
        await scope_api.session.set("key1", "value1")

        promoted = await scope_api.promote("key1", "session", "permanent")
        assert promoted is True

        assert await scope_api.permanent.get("key1") == "value1"
        assert await scope_api.session.get("key1") is None

    @pytest.mark.asyncio
    async def test_demote(self, scope_api):
        """Test demoting values."""
        await scope_api.permanent.set("key1", "value1")

        demoted = await scope_api.demote("key1", "permanent", "session")
        assert demoted is True

        assert await scope_api.session.get("key1") == "value1"
        assert await scope_api.permanent.get("key1") is None
