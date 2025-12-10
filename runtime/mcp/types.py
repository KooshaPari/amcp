"""MCP management types."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""

    server_id: str
    """Server identifier."""
    name: str
    """Server name."""
    status: str
    """Server status (running, stopped, error)."""
    config: dict[str, Any]
    """Server configuration."""
    tools: list[str] = field(default_factory=list)
    """List of tools provided by server."""


@dataclass
class MCPServerConfig:
    """Configuration for creating an MCP server."""

    name: str
    """Server name."""
    package: Optional[str] = None
    """MCP package name (if installing from registry)."""
    command: Optional[str] = None
    """Command to run server (if custom)."""
    env: dict[str, str] = field(default_factory=dict)
    """Environment variables."""
    args: list[str] = field(default_factory=list)
    """Command arguments."""
