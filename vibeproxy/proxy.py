"""Vibeproxy - FastMCP-based MCP Proxy.

User-facing client that aggregates multiple backends:
- SmartCP (local MCP server)
- Cloud backends (remote MCP services)
- Local backends (subprocess servers)
- Remote-local backends (tunneled connections)
- Bifrost + external MCP servers
- SLMs and LLMs

Uses FastMCP's native proxy patterns for tool aggregation.
"""

import logging
from typing import Any

try:
    from fastmcp import FastMCP
    from fastmcp.client import Client as MCPClient
except ImportError:
    FastMCP = None
    MCPClient = None

from .config import BackendConfig, VibeproxyConfig

logger = logging.getLogger(__name__)


class Vibeproxy:
    """FastMCP-based MCP proxy aggregating multiple backends.

    Vibeproxy is the user-facing client that routes MCP requests to
    appropriate backends based on configuration and tool availability.

    Usage:
        config = VibeproxyConfig(backends=[
            BackendConfig(name="smartcp", backend_type=BackendType.SMARTCP,
                url="http://localhost:8000"),
            BackendConfig(name="memory", backend_type=BackendType.LOCAL,
                command="npx", args=["@anthropic/memory-server"]),
        ])
        proxy = Vibeproxy(config)
        await proxy.start()

        # Call tools - routing is automatic
        result = await proxy.call_tool("smartcp_query", {"sql": "SELECT * FROM users"})
    """

    def __init__(self, config: VibeproxyConfig) -> None:
        """Initialize vibeproxy.

        Args:
            config: Proxy configuration
        """
        self._config = config
        self._mcp: FastMCP | None = None
        self._clients: dict[str, Any] = {}  # MCPClient instances per backend
        self._tools: dict[str, str] = {}  # tool_name -> backend_name mapping
        self._started = False

        logger.info(f"Vibeproxy initialized: {config.name}")

    @property
    def is_started(self) -> bool:
        """Check if proxy has been started."""
        return self._started

    @property
    def available_tools(self) -> list[str]:
        """Get list of available tool names."""
        return list(self._tools.keys())

    @property
    def backends(self) -> list[str]:
        """Get list of connected backend names."""
        return list(self._clients.keys())

    async def start(self) -> bool:
        """Start the proxy and connect to all backends.

        Returns:
            True if at least one backend connected successfully
        """
        if self._started:
            logger.warning("Vibeproxy already started")
            return True

        if FastMCP is None:
            logger.error("FastMCP not installed - cannot start proxy")
            return False

        logger.info("Starting vibeproxy...")

        # Create main FastMCP instance
        self._mcp = FastMCP(name=self._config.name)

        # Connect to each enabled backend
        connected_count = 0
        for backend in self._config.get_enabled_backends():
            try:
                success = await self._connect_backend(backend)
                if success:
                    connected_count += 1
            except Exception as e:
                logger.error(f"Failed to connect to backend {backend.name}: {e}")

        self._started = connected_count > 0
        logger.info(
            f"Vibeproxy started: {connected_count}/"
            f"{len(self._config.get_enabled_backends())} backends connected"
        )
        return self._started

    async def stop(self) -> None:
        """Stop the proxy and disconnect all backends."""
        if not self._started:
            return

        logger.info("Stopping vibeproxy...")

        # Disconnect all clients
        for name, client in self._clients.items():
            try:
                if hasattr(client, "close"):
                    await client.close()
            except Exception as e:
                logger.error(f"Error closing client {name}: {e}")

        self._clients.clear()
        self._tools.clear()
        self._mcp = None
        self._started = False
        logger.info("Vibeproxy stopped")

    async def _connect_backend(self, backend: BackendConfig) -> bool:
        """Connect to a single backend.

        Args:
            backend: Backend configuration

        Returns:
            True if connected successfully
        """
        logger.info(f"Connecting to backend: {backend.name} ({backend.backend_type.value})")

        if MCPClient is None:
            logger.error("FastMCP Client not available")
            return False

        try:
            # Create client based on backend type
            mcp_config = backend.to_mcp_config()

            if backend.url:
                # HTTP/SSE connection
                client = MCPClient(backend.url)
            elif backend.command:
                # Subprocess connection
                client = MCPClient(backend.command, *backend.args)
            else:
                logger.error(f"Backend {backend.name} has no connection config")
                return False

            # Connect and discover tools
            await client.connect()
            tools = await client.list_tools()

            # Register tools with optional prefix
            prefix = backend.prefix or (
                f"{backend.name}_" if self._config.enable_tool_prefixing else ""
            )
            for tool in tools:
                tool_name = f"{prefix}{tool.name}" if prefix else tool.name
                self._tools[tool_name] = backend.name
                logger.debug(f"Registered tool: {tool_name} -> {backend.name}")

            self._clients[backend.name] = client
            logger.info(f"Connected to {backend.name}: {len(tools)} tools available")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {backend.name}: {e}")
            return False

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call a tool by name.

        Automatically routes to the correct backend based on tool registration.

        Args:
            name: Tool name (possibly prefixed)
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self._started:
            return {"error": "Vibeproxy not started"}

        # Find backend for this tool
        backend_name = self._tools.get(name)
        if not backend_name:
            # Try without prefix if fallback enabled
            if self._config.enable_fallback_routing and self._config.default_backend:
                backend_name = self._config.default_backend
            else:
                return {"error": f"Unknown tool: {name}"}

        client = self._clients.get(backend_name)
        if not client:
            return {"error": f"Backend not connected: {backend_name}"}

        try:
            # Strip prefix if present to get original tool name
            backend = self._config.get_backend(backend_name)
            original_name = name
            if backend and backend.prefix and name.startswith(backend.prefix):
                original_name = name[len(backend.prefix) :]
            elif self._config.enable_tool_prefixing and name.startswith(f"{backend_name}_"):
                original_name = name[len(f"{backend_name}_") :]

            # Call the tool
            result = await client.call_tool(original_name, arguments or {})
            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Tool call failed: {name} on {backend_name}: {e}")

            # Try fallback if enabled
            if self._config.enable_fallback_routing:
                for alt_backend_name, alt_client in self._clients.items():
                    if alt_backend_name != backend_name:
                        try:
                            result = await alt_client.call_tool(name, arguments or {})
                            return {
                                "success": True,
                                "result": result,
                                "fallback": alt_backend_name,
                            }
                        except Exception:
                            continue

            return {"error": str(e)}

    async def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools from all backends.

        Returns:
            List of tool schemas with backend info
        """
        tools = []
        for tool_name, backend_name in self._tools.items():
            tools.append({
                "name": tool_name,
                "backend": backend_name,
            })
        return tools

    def get_stats(self) -> dict[str, Any]:
        """Get proxy statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "name": self._config.name,
            "started": self._started,
            "backends": {
                name: {
                    "connected": True,
                    "tools": sum(1 for t, b in self._tools.items() if b == name),
                }
                for name in self._clients
            },
            "total_tools": len(self._tools),
            "user_id": self._config.user_id,
            "workspace_id": self._config.workspace_id,
        }

    async def __aenter__(self) -> "Vibeproxy":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
