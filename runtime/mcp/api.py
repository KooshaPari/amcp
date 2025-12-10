"""MCP management API for agent namespace."""

import logging
from typing import Any

from smartcp.runtime.mcp.manager import MCPServerManager
from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


class MCPServersAPI:
    """MCP server management API."""

    def __init__(
        self,
        manager: MCPServerManager,
        user_ctx: UserContext,
    ):
        """Initialize MCP servers API.

        Args:
            manager: MCP server manager
            user_ctx: User context
        """
        self._manager = manager
        self._user_ctx = user_ctx

    async def list(self) -> list[dict[str, Any]]:
        """List running MCP servers."""
        return await self._manager.list_servers(self._user_ctx)

    async def create(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create and start a new MCP server."""
        return await self._manager.create_server(config, self._user_ctx)

    async def restart(self, server_id: str) -> bool:
        """Restart an MCP server."""
        return await self._manager.restart_server(server_id, self._user_ctx)

    async def stop(self, server_id: str) -> bool:
        """Stop an MCP server."""
        return await self._manager.stop_server(server_id, self._user_ctx)

    async def delete(self, server_id: str) -> bool:
        """Delete an MCP server."""
        return await self._manager.delete_server(server_id, self._user_ctx)


class MCPAPI:
    """MCP management API injected into agent namespace."""

    def __init__(
        self,
        manager: MCPServerManager,
        user_ctx: UserContext,
    ):
        """Initialize MCP API.

        Args:
            manager: MCP server manager
            user_ctx: User context
        """
        self._manager = manager
        self._user_ctx = user_ctx
        self.servers = MCPServersAPI(manager, user_ctx)

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search MCP registry for packages."""
        return await self._manager.search_registry(query, limit)

    async def install(self, package: str, version: str | None = None) -> dict[str, Any]:
        """Install an MCP package from registry."""
        return await self._manager.install_package(package, version, self._user_ctx)

    async def uninstall(self, package: str) -> bool:
        """Uninstall an MCP package."""
        # Placeholder - Phase 3 will implement
        logger.warning(f"Uninstall not yet implemented: {package}")
        return False

    async def list_installed(self) -> list[dict[str, Any]]:
        """List installed MCP packages."""
        # Placeholder - Phase 3 will implement
        return []
