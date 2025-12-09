"""SmartCP Vibeproxy - FastMCP-based MCP Proxy.

Vibeproxy is the user-facing client that aggregates multiple MCP backends:
- SmartCP (local MCP server)
- Cloud backends (remote MCP services)
- Local backends (subprocess servers)
- Remote-local backends (tunneled connections)
- Bifrost + external MCP servers
- SLMs and LLMs

Uses FastMCP's native proxy patterns for tool aggregation and routing.

Example:
    from smartcp.vibeproxy import Vibeproxy, VibeproxyConfig, create_smartcp_backend

    config = VibeproxyConfig(backends=[
        create_smartcp_backend(url="http://localhost:8000"),
    ])

    async with Vibeproxy(config) as proxy:
        result = await proxy.call_tool("query", {"sql": "SELECT * FROM users"})
"""

from .config import BackendConfig, BackendType, VibeproxyConfig
from .proxy import Vibeproxy
from .factory import (
    create_cloud_backend,
    create_local_backend,
    create_smartcp_backend,
    create_vibeproxy,
)
from .backends import (
    BackendHealth,
    BackendRouter,
    RoutingRule,
    RoutingStrategy,
    check_all_backends_health,
    check_backend_health,
    discover_backends,
    get_default_backends,
    get_development_backends,
    get_production_backends,
)

__all__ = [
    # Core proxy
    "Vibeproxy",
    "VibeproxyConfig",
    # Backend configuration
    "BackendConfig",
    "BackendType",
    # Factory functions
    "create_vibeproxy",
    "create_smartcp_backend",
    "create_local_backend",
    "create_cloud_backend",
    # Routing
    "BackendRouter",
    "RoutingStrategy",
    "RoutingRule",
    # Backend presets
    "get_default_backends",
    "get_development_backends",
    "get_production_backends",
    # Discovery and health
    "discover_backends",
    "check_backend_health",
    "check_all_backends_health",
    "BackendHealth",
]
