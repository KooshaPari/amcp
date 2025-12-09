"""Data models for SmartCP Control Plane."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ServerStatus(str, Enum):
    """SmartCP server status."""

    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPING = "stopping"
    STOPPED = "stopped"


class CapabilityType(str, Enum):
    """SmartCP capability types."""

    CODE_EXECUTION = "code_execution"
    MEMORY_STORAGE = "memory_storage"
    STATE_MANAGEMENT = "state_management"
    VARIABLE_NAMESPACE = "variable_namespace"
    SANDBOX_ISOLATION = "sandbox_isolation"
    TTL_SUPPORT = "ttl_support"


@dataclass
class ServerCapability:
    """Capability definition for SmartCP server."""

    name: CapabilityType
    version: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)
    limits: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name.value,
            "version": self.version,
            "enabled": self.enabled,
            "config": self.config,
            "limits": self.limits,
        }


@dataclass
class ServerHealth:
    """SmartCP server health status."""

    status: ServerStatus
    uptime_seconds: float
    memory_usage_mb: float
    active_sessions: int
    tools_registered: int
    last_check: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "uptime_seconds": self.uptime_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "active_sessions": self.active_sessions,
            "tools_registered": self.tools_registered,
            "last_check": self.last_check,
            "errors": self.errors,
        }


@dataclass
class ProgressUpdate:
    """MCP progress update for long-running operations."""

    operation_id: str
    operation_type: str
    progress_percent: float
    status: str
    message: str
    started_at: str
    updated_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "progress_percent": self.progress_percent,
            "status": self.status,
            "message": self.message,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


@dataclass
class ControlPlaneConfig:
    """Configuration for control plane integration."""

    enabled: bool = True
    bifrost_url: str = "ws://localhost:4000/graphql"
    api_key: str = ""
    heartbeat_interval: float = 30.0
    health_check_interval: float = 60.0
    capability_sync_interval: float = 300.0
    server_id: str = "smartcp-default"
    server_version: str = "1.0.0"
