"""Unit tests for MCPAPI."""

import pytest

from smartcp.runtime.mcp.api import MCPAPI, MCPServersAPI
from smartcp.runtime.mcp.manager import MCPServerManager
from smartcp.runtime.types import UserContext


class TestMCPAPI:
    """Unit tests for MCPAPI."""

    @pytest.fixture
    def manager(self):
        """Create an MCP server manager."""
        return MCPServerManager()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def mcp_api(self, manager, user_ctx):
        """Create an MCP API."""
        return MCPAPI(manager, user_ctx)

    @pytest.mark.asyncio
    async def test_search(self, mcp_api):
        """Test searching MCP registry."""
        results = await mcp_api.search("database", limit=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_install(self, mcp_api):
        """Test installing a package."""
        result = await mcp_api.install("mcp-postgres")
        assert result["status"] == "installed"

    @pytest.mark.asyncio
    async def test_list_installed(self, mcp_api):
        """Test listing installed packages."""
        packages = await mcp_api.list_installed()
        assert isinstance(packages, list)


class TestMCPServersAPI:
    """Unit tests for MCPServersAPI."""

    @pytest.fixture
    def manager(self):
        """Create an MCP server manager."""
        return MCPServerManager()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def servers_api(self, manager, user_ctx):
        """Create a servers API."""
        return MCPServersAPI(manager, user_ctx)

    @pytest.mark.asyncio
    async def test_list(self, servers_api):
        """Test listing servers."""
        servers = await servers_api.list()
        assert isinstance(servers, list)

    @pytest.mark.asyncio
    async def test_create(self, servers_api):
        """Test creating a server."""
        config = {"id": "test-server", "name": "Test"}
        server = await servers_api.create(config)
        assert server["id"] == "test-server"

    @pytest.mark.asyncio
    async def test_restart(self, servers_api):
        """Test restarting a server."""
        config = {"id": "server1"}
        await servers_api.create(config)

        restarted = await servers_api.restart("server1")
        assert restarted is True

    @pytest.mark.asyncio
    async def test_stop(self, servers_api):
        """Test stopping a server."""
        config = {"id": "server1"}
        await servers_api.create(config)

        stopped = await servers_api.stop("server1")
        assert stopped is True

    @pytest.mark.asyncio
    async def test_delete(self, servers_api):
        """Test deleting a server."""
        config = {"id": "server1"}
        await servers_api.create(config)

        deleted = await servers_api.delete("server1")
        assert deleted is True
