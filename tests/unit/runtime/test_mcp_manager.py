"""Unit tests for MCPServerManager."""

import pytest

from smartcp.runtime.mcp.manager import MCPServerManager
from smartcp.runtime.types import UserContext


class TestMCPServerManager:
    """Unit tests for MCPServerManager."""

    @pytest.fixture
    def manager(self):
        """Create an MCP server manager."""
        return MCPServerManager()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.mark.asyncio
    async def test_search_registry(self, manager):
        """Test searching MCP registry."""
        results = await manager.search_registry("database", limit=10)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_install_package(self, manager, user_ctx):
        """Test installing an MCP package."""
        result = await manager.install_package("mcp-postgres", None, user_ctx)
        assert result["status"] == "installed"
        assert result["package"] == "mcp-postgres"

    @pytest.mark.asyncio
    async def test_create_server(self, manager, user_ctx):
        """Test creating a server."""
        config = {
            "id": "test-server",
            "name": "Test Server",
            "command": "mcp-server",
        }

        server = await manager.create_server(config, user_ctx)
        assert server["id"] == "test-server"
        assert server["status"] == "running"

    @pytest.mark.asyncio
    async def test_list_servers(self, manager, user_ctx):
        """Test listing servers."""
        config = {"id": "server1", "name": "Server 1"}
        await manager.create_server(config, user_ctx)

        servers = await manager.list_servers(user_ctx)
        assert len(servers) >= 1

    @pytest.mark.asyncio
    async def test_restart_server(self, manager, user_ctx):
        """Test restarting a server."""
        config = {"id": "server1"}
        await manager.create_server(config, user_ctx)

        restarted = await manager.restart_server("server1", user_ctx)
        assert restarted is True

    @pytest.mark.asyncio
    async def test_stop_server(self, manager, user_ctx):
        """Test stopping a server."""
        config = {"id": "server1"}
        await manager.create_server(config, user_ctx)

        stopped = await manager.stop_server("server1", user_ctx)
        assert stopped is True

        server = await manager.list_servers(user_ctx)
        server1 = next((s for s in server if s["id"] == "server1"), None)
        assert server1["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_delete_server(self, manager, user_ctx):
        """Test deleting a server."""
        config = {"id": "server1"}
        await manager.create_server(config, user_ctx)

        deleted = await manager.delete_server("server1", user_ctx)
        assert deleted is True

        servers = await manager.list_servers(user_ctx)
        assert not any(s["id"] == "server1" for s in servers)
