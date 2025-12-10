"""Component tests for ScopeManager + ScopeAPI integration."""

import pytest

from smartcp.runtime.scope.api import ScopeAPI
from smartcp.runtime.scope.manager import ScopeManager
from smartcp.runtime.types import UserContext


class TestScopeManagerAPIIntegration:
    """Component tests for ScopeManager and ScopeAPI."""

    @pytest.fixture
    def manager(self):
        """Create a scope manager."""
        return ScopeManager(storage_backend="memory")

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user", workspace_id="ws-123")

    @pytest.fixture
    def scope_api(self, manager, user_ctx):
        """Create a scope API."""
        return ScopeAPI(manager, user_ctx)

    @pytest.mark.asyncio
    async def test_scope_api_operations(self, scope_api):
        """Test scope API operations."""
        # Set value via API
        await scope_api.session.set("key1", "value1")

        # Get value via API
        value = await scope_api.session.get("key1")
        assert value == "value1"

        # Delete via API
        deleted = await scope_api.session.delete("key1")
        assert deleted is True

    @pytest.mark.asyncio
    async def test_promote_demote(self, scope_api):
        """Test promote/demote operations."""
        # Set in session
        await scope_api.session.set("key1", "value1")

        # Promote to permanent
        promoted = await scope_api.promote("key1", "session", "permanent")
        assert promoted is True

        assert await scope_api.permanent.get("key1") == "value1"
        assert await scope_api.session.get("key1") is None

        # Demote back to session
        demoted = await scope_api.demote("key1", "permanent", "session")
        assert demoted is True

        assert await scope_api.session.get("key1") == "value1"
        assert await scope_api.permanent.get("key1") is None

    @pytest.mark.asyncio
    async def test_all_levels(self, scope_api):
        """Test all scope levels."""
        levels = [
            scope_api.block,
            scope_api.iteration,
            scope_api.tool_call,
            scope_api.prompt_chain,
            scope_api.session,
            scope_api.phase,
            scope_api.project,
            scope_api.workspace,
            scope_api.organization,
            scope_api.global_,
            scope_api.permanent,
        ]

        for i, level in enumerate(levels):
            await level.set(f"key{i}", f"value{i}")
            value = await level.get(f"key{i}")
            assert value == f"value{i}"
