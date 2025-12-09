"""Configuration models for Vibeproxy.

This module contains all configuration dataclasses and enums used by Vibeproxy.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BackendType(str, Enum):
    """Types of MCP backends vibeproxy can route to."""

    SMARTCP = "smartcp"  # Local SmartCP server
    CLOUD = "cloud"  # Cloud-hosted MCP services
    LOCAL = "local"  # Local subprocess servers
    REMOTE_LOCAL = "remote_local"  # Tunneled remote-to-local
    EXTERNAL = "external"  # External MCP servers (Bifrost, etc.)
    LLM = "llm"  # Large language model backends
    SLM = "slm"  # Small language model backends


@dataclass
class BackendConfig:
    """Configuration for a single backend."""

    name: str
    backend_type: BackendType
    enabled: bool = True

    # Connection settings (mutually exclusive based on type)
    url: str | None = None  # For cloud/external/remote
    command: str | None = None  # For local subprocess
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)

    # Routing
    prefix: str | None = None  # Tool prefix (e.g., "smartcp_")
    priority: int = 0  # Higher = preferred when multiple backends have same tool

    # Timeouts
    connect_timeout: float = 30.0
    request_timeout: float = 60.0

    def to_mcp_config(self) -> dict[str, Any]:
        """Convert to FastMCP mcpServers format."""
        if self.url:
            return {"url": self.url}
        elif self.command:
            config: dict[str, Any] = {"command": self.command}
            if self.args:
                config["args"] = self.args
            if self.env:
                config["env"] = self.env
            return config
        return {}


@dataclass
class VibeproxyConfig:
    """Main vibeproxy configuration."""

    name: str = "vibeproxy"
    version: str = "1.0.0"

    # Backends
    backends: list[BackendConfig] = field(default_factory=list)

    # Default routing behavior
    default_backend: str | None = None  # Backend name for unmatched tools

    # User context
    user_id: str | None = None
    workspace_id: str | None = None

    # Feature flags
    enable_tool_prefixing: bool = True  # Prefix tools with backend name
    enable_fallback_routing: bool = True  # Try next backend on failure
    enable_parallel_discovery: bool = True  # Discover tools from all backends in parallel

    def get_enabled_backends(self) -> list[BackendConfig]:
        """Get list of enabled backends."""
        return [b for b in self.backends if b.enabled]

    def get_backend(self, name: str) -> BackendConfig | None:
        """Get backend by name."""
        for b in self.backends:
            if b.name == name:
                return b
        return None
