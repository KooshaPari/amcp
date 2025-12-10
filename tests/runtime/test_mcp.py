"""Tests for MCP management."""

import pytest

from smartcp.runtime.mcp import MCPServerManager, MCPAPI
from smartcp.runtime.types import UserContext


@pytest.fixture
def mcp_manager():
    """Create MCP server manager."""
    return MCPServerManager()


@pytest.fixture
def user_ctx():
    """Create test user context."""
    return UserContext(user_id="test-user")


@pytest.fixture
def mcp_api(mcp_manager, user_ctx):
    """Create MCP API."""
    return MCPAPI(mcp_manager, user_ctx)


@pytest.mark.asyncio
async def test_search_registry(mcp_api):
    """Test searching MCP registry."""
    results = await mcp_api.search("database")
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_create_server(mcp_api):
    """Test creating an MCP server."""
    config = {"name": "test-server", "id": "server-1"}
    server = await mcp_api.servers.create(config)

    assert server["id"] == "server-1"
    assert server["status"] == "running"


@pytest.mark.asyncio
async def test_list_servers(mcp_api):
    """Test listing servers."""
    config = {"name": "test-server", "id": "server-1"}
    await mcp_api.servers.create(config)

    servers = await mcp_api.servers.list()
    assert len(servers) >= 1
    assert any(s["id"] == "server-1" for s in servers)


@pytest.mark.asyncio
async def test_stop_server(mcp_api):
    """Test stopping a server."""
    config = {"name": "test-server", "id": "server-1"}
    await mcp_api.servers.create(config)

    success = await mcp_api.servers.stop("server-1")
    assert success is True

    servers = await mcp_api.servers.list()
    server = next(s for s in servers if s["id"] == "server-1")
    assert server["status"] == "stopped"


@pytest.mark.asyncio
async def test_restart_server(mcp_api):
    """Test restarting a server."""
    config = {"name": "test-server", "id": "server-1"}
    await mcp_api.servers.create(config)
    await mcp_api.servers.stop("server-1")

    success = await mcp_api.servers.restart("server-1")
    assert success is True

    servers = await mcp_api.servers.list()
    server = next(s for s in servers if s["id"] == "server-1")
    assert server["status"] == "running"


@pytest.mark.asyncio
async def test_delete_server(mcp_api):
    """Test deleting a server."""
    config = {"name": "test-server", "id": "server-1"}
    await mcp_api.servers.create(config)

    success = await mcp_api.servers.delete("server-1")
    assert success is True

    servers = await mcp_api.servers.list()
    assert not any(s["id"] == "server-1" for s in servers)


@pytest.mark.asyncio
async def test_install_package(mcp_api):
    """Test installing a package."""
    result = await mcp_api.install("test-package", "1.0.0")
    assert result["status"] == "installed"
    assert result["package"] == "test-package"
