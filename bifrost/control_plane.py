"""SmartCP Control Plane Integration for Bifrost.

Provides integration with Bifrost's control plane for:
- Capability negotiation
- MCP progress reporting
- Server health and status
- Configuration sync
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


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
    last_check: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
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
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
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


class SmartCPControlPlane:
    """SmartCP Control Plane integration.

    Features:
    - Capability negotiation with Bifrost
    - Server health reporting
    - MCP progress updates
    - Configuration sync
    """

    def __init__(self, config: ControlPlaneConfig | None = None) -> None:
        """Initialize control plane.

        Args:
            config: Control plane configuration
        """
        self._config = config or ControlPlaneConfig()
        self._client: Any = None  # BifrostClient when connected
        self._running = False
        self._start_time: float = 0
        self._capabilities: list[ServerCapability] = []
        self._heartbeat_task: asyncio.Task | None = None
        self._health_check_task: asyncio.Task | None = None
        self._active_operations: dict[str, ProgressUpdate] = {}

        # Initialize default capabilities
        self._init_default_capabilities()

        logger.info("SmartCPControlPlane initialized")

    def _init_default_capabilities(self) -> None:
        """Initialize default SmartCP capabilities."""
        self._capabilities = [
            ServerCapability(
                name=CapabilityType.CODE_EXECUTION,
                version="1.0.0",
                enabled=True,
                config={"language": "python", "sandbox": True},
                limits={"max_execution_time": 300, "max_memory_mb": 512},
            ),
            ServerCapability(
                name=CapabilityType.MEMORY_STORAGE,
                version="1.0.0",
                enabled=True,
                config={"types": ["working", "persistent", "context"]},
                limits={"max_keys_per_user": 1000, "max_value_size_kb": 1024},
            ),
            ServerCapability(
                name=CapabilityType.STATE_MANAGEMENT,
                version="1.0.0",
                enabled=True,
                config={"user_isolated": True},
                limits={"max_keys": 10000},
            ),
            ServerCapability(
                name=CapabilityType.VARIABLE_NAMESPACE,
                version="1.0.0",
                enabled=True,
                config={"user_isolated": True, "persistent": False},
                limits={"max_variables": 500},
            ),
            ServerCapability(
                name=CapabilityType.SANDBOX_ISOLATION,
                version="1.0.0",
                enabled=True,
                config={"isolation_level": "process"},
                limits={},
            ),
            ServerCapability(
                name=CapabilityType.TTL_SUPPORT,
                version="1.0.0",
                enabled=True,
                config={"default_ttl_seconds": 3600},
                limits={"max_ttl_seconds": 86400 * 30},
            ),
        ]

    async def start(self) -> None:
        """Start control plane integration.

        Connects to Bifrost and starts background tasks.
        """
        if self._running:
            logger.warning("Control plane already running")
            return

        if not self._config.enabled:
            logger.info("Control plane disabled")
            return

        logger.info("Starting SmartCP control plane")
        self._start_time = time.time()
        self._running = True

        # Connect to Bifrost
        try:
            await self._connect_to_bifrost()
        except Exception as e:
            logger.error(f"Failed to connect to Bifrost: {e}")
            # Continue without connection - will retry

        # Register capabilities
        await self._register_capabilities()

        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info("SmartCP control plane started")

    async def stop(self) -> None:
        """Stop control plane integration."""
        if not self._running:
            return

        logger.info("Stopping SmartCP control plane")
        self._running = False

        # Cancel background tasks
        for task in [self._heartbeat_task, self._health_check_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._heartbeat_task = None
        self._health_check_task = None

        # Disconnect from Bifrost
        await self._disconnect_from_bifrost()

        logger.info("SmartCP control plane stopped")

    async def __aenter__(self) -> "SmartCPControlPlane":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()

    async def _connect_to_bifrost(self) -> None:
        """Connect to Bifrost gateway."""
        try:
            from smartcp.infrastructure.bifrost import BifrostClient

            self._client = BifrostClient(
                url=self._config.bifrost_url,
                api_key=self._config.api_key,
            )
            await self._client.connect()
            logger.info(f"Connected to Bifrost: {self._config.bifrost_url}")

        except ImportError:
            logger.warning("BifrostClient not available")
            self._client = None
        except Exception as e:
            logger.error(f"Bifrost connection error: {e}")
            self._client = None

    async def _disconnect_from_bifrost(self) -> None:
        """Disconnect from Bifrost gateway."""
        if self._client:
            try:
                await self._client.disconnect()
            except Exception as e:
                logger.error(f"Bifrost disconnect error: {e}")
            finally:
                self._client = None

    async def _register_capabilities(self) -> None:
        """Register server capabilities with Bifrost."""
        if not self._client:
            logger.debug("No Bifrost client, skipping capability registration")
            return

        try:
            capabilities_data = [cap.to_dict() for cap in self._capabilities]

            mutation = """
                mutation RegisterCapabilities($serverId: String!, $capabilities: JSON!) {
                    registerServerCapabilities(serverId: $serverId, capabilities: $capabilities) {
                        success
                        message
                    }
                }
            """

            result = await self._client.mutate(
                mutation,
                variables={
                    "serverId": self._config.server_id,
                    "capabilities": capabilities_data,
                },
            )

            registration = result.get("registerServerCapabilities", {})
            if registration.get("success"):
                logger.info(
                    f"Registered {len(self._capabilities)} capabilities with Bifrost"
                )
            else:
                logger.warning(
                    f"Capability registration failed: {registration.get('message')}"
                )

        except Exception as e:
            logger.error(f"Failed to register capabilities: {e}")

    async def _heartbeat_loop(self) -> None:
        """Background heartbeat to Bifrost."""
        while self._running:
            try:
                await asyncio.sleep(self._config.heartbeat_interval)

                if not self._running:
                    break

                await self._send_heartbeat()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def _send_heartbeat(self) -> None:
        """Send heartbeat to Bifrost."""
        if not self._client:
            return

        try:
            mutation = """
                mutation ServerHeartbeat($serverId: String!, $timestamp: String!) {
                    serverHeartbeat(serverId: $serverId, timestamp: $timestamp) {
                        acknowledged
                    }
                }
            """

            await self._client.mutate(
                mutation,
                variables={
                    "serverId": self._config.server_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            logger.debug("Heartbeat sent")

        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

    async def _health_check_loop(self) -> None:
        """Background health check reporting."""
        while self._running:
            try:
                await asyncio.sleep(self._config.health_check_interval)

                if not self._running:
                    break

                health = await self.get_health()
                await self._report_health(health)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _report_health(self, health: ServerHealth) -> None:
        """Report server health to Bifrost."""
        if not self._client:
            return

        try:
            mutation = """
                mutation ReportServerHealth($serverId: String!, $health: JSON!) {
                    reportServerHealth(serverId: $serverId, health: $health) {
                        acknowledged
                    }
                }
            """

            await self._client.mutate(
                mutation,
                variables={
                    "serverId": self._config.server_id,
                    "health": health.to_dict(),
                },
            )
            logger.debug(f"Health reported: {health.status.value}")

        except Exception as e:
            logger.warning(f"Health report failed: {e}")

    async def get_health(self) -> ServerHealth:
        """Get current server health.

        Returns:
            ServerHealth status
        """
        import psutil

        # Calculate uptime
        uptime = time.time() - self._start_time if self._start_time > 0 else 0

        # Get memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)

        # Determine status
        errors = []
        status = ServerStatus.HEALTHY

        if not self._running:
            status = ServerStatus.STOPPED
        elif memory_mb > 1024:  # > 1GB
            status = ServerStatus.DEGRADED
            errors.append("High memory usage")

        return ServerHealth(
            status=status,
            uptime_seconds=uptime,
            memory_usage_mb=memory_mb,
            active_sessions=0,  # TODO: Get from session manager
            tools_registered=17,  # SmartCP has 17 tools
            errors=errors,
        )

    @property
    def capabilities(self) -> list[ServerCapability]:
        """Get server capabilities."""
        return self._capabilities.copy()

    def add_capability(self, capability: ServerCapability) -> None:
        """Add a capability.

        Args:
            capability: Capability to add
        """
        # Check if already exists
        for i, existing in enumerate(self._capabilities):
            if existing.name == capability.name:
                self._capabilities[i] = capability
                logger.info(f"Updated capability: {capability.name.value}")
                return

        self._capabilities.append(capability)
        logger.info(f"Added capability: {capability.name.value}")

    def remove_capability(self, name: CapabilityType) -> bool:
        """Remove a capability.

        Args:
            name: Capability name to remove

        Returns:
            True if removed
        """
        for i, cap in enumerate(self._capabilities):
            if cap.name == name:
                self._capabilities.pop(i)
                logger.info(f"Removed capability: {name.value}")
                return True
        return False

    # Progress Reporting

    async def start_operation(
        self,
        operation_id: str,
        operation_type: str,
        message: str = "Starting...",
        metadata: dict[str, Any] | None = None,
    ) -> ProgressUpdate:
        """Start tracking a long-running operation.

        Args:
            operation_id: Unique operation ID
            operation_type: Type of operation (e.g., "code_execution")
            message: Initial status message
            metadata: Optional metadata

        Returns:
            ProgressUpdate for the operation
        """
        now = datetime.now(UTC).isoformat()
        progress = ProgressUpdate(
            operation_id=operation_id,
            operation_type=operation_type,
            progress_percent=0.0,
            status="started",
            message=message,
            started_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        self._active_operations[operation_id] = progress
        await self._report_progress(progress)

        return progress

    async def update_progress(
        self,
        operation_id: str,
        progress_percent: float,
        message: str | None = None,
        status: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProgressUpdate | None:
        """Update operation progress.

        Args:
            operation_id: Operation ID
            progress_percent: Progress (0-100)
            message: Optional status message
            status: Optional status update
            metadata: Optional metadata update

        Returns:
            Updated ProgressUpdate or None if not found
        """
        progress = self._active_operations.get(operation_id)
        if not progress:
            logger.warning(f"Operation not found: {operation_id}")
            return None

        progress.progress_percent = min(max(progress_percent, 0), 100)
        progress.updated_at = datetime.now(UTC).isoformat()

        if message:
            progress.message = message
        if status:
            progress.status = status
        if metadata:
            progress.metadata.update(metadata)

        await self._report_progress(progress)
        return progress

    async def complete_operation(
        self,
        operation_id: str,
        message: str = "Completed",
        success: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> ProgressUpdate | None:
        """Mark operation as completed.

        Args:
            operation_id: Operation ID
            message: Completion message
            success: Whether operation succeeded
            metadata: Optional final metadata

        Returns:
            Final ProgressUpdate or None if not found
        """
        progress = self._active_operations.get(operation_id)
        if not progress:
            logger.warning(f"Operation not found: {operation_id}")
            return None

        progress.progress_percent = 100.0
        progress.status = "completed" if success else "failed"
        progress.message = message
        progress.updated_at = datetime.now(UTC).isoformat()

        if metadata:
            progress.metadata.update(metadata)

        await self._report_progress(progress)

        # Remove from active operations
        del self._active_operations[operation_id]

        return progress

    async def _report_progress(self, progress: ProgressUpdate) -> None:
        """Report progress to Bifrost.

        Args:
            progress: Progress update to report
        """
        if not self._client:
            return

        try:
            mutation = """
                mutation ReportProgress($serverId: String!, $progress: JSON!) {
                    reportOperationProgress(serverId: $serverId, progress: $progress) {
                        acknowledged
                    }
                }
            """

            await self._client.mutate(
                mutation,
                variables={
                    "serverId": self._config.server_id,
                    "progress": progress.to_dict(),
                },
            )
            logger.debug(
                f"Progress reported: {progress.operation_id} - {progress.progress_percent}%"
            )

        except Exception as e:
            logger.warning(f"Progress report failed: {e}")

    def get_active_operations(self) -> list[ProgressUpdate]:
        """Get all active operations.

        Returns:
            List of active ProgressUpdates
        """
        return list(self._active_operations.values())

    # Configuration Sync

    async def sync_configuration(self) -> dict[str, Any]:
        """Sync configuration with Bifrost.

        Returns:
            Synced configuration
        """
        if not self._client:
            return {}

        try:
            query = """
                query GetServerConfig($serverId: String!) {
                    serverConfiguration(serverId: $serverId) {
                        config
                        version
                        updatedAt
                    }
                }
            """

            result = await self._client.query(
                query,
                variables={"serverId": self._config.server_id},
            )

            config_data = result.get("serverConfiguration", {})
            logger.info(
                f"Configuration synced: version {config_data.get('version', 'unknown')}"
            )
            return config_data.get("config", {})

        except Exception as e:
            logger.error(f"Configuration sync failed: {e}")
            return {}

    async def push_configuration(self, config: dict[str, Any]) -> bool:
        """Push configuration to Bifrost.

        Args:
            config: Configuration to push

        Returns:
            True if successful
        """
        if not self._client:
            return False

        try:
            mutation = """
                mutation UpdateServerConfig($serverId: String!, $config: JSON!) {
                    updateServerConfiguration(serverId: $serverId, config: $config) {
                        success
                        version
                    }
                }
            """

            result = await self._client.mutate(
                mutation,
                variables={
                    "serverId": self._config.server_id,
                    "config": config,
                },
            )

            update_result = result.get("updateServerConfiguration", {})
            if update_result.get("success"):
                logger.info(
                    f"Configuration pushed: version {update_result.get('version')}"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Configuration push failed: {e}")
            return False


# Global control plane instance (lazy initialized)
_control_plane: SmartCPControlPlane | None = None


def get_control_plane(
    config: ControlPlaneConfig | None = None,
) -> SmartCPControlPlane:
    """Get or create the global control plane.

    Args:
        config: Optional configuration

    Returns:
        SmartCPControlPlane instance
    """
    global _control_plane

    if _control_plane is None:
        _control_plane = SmartCPControlPlane(config)

    return _control_plane


async def init_control_plane(
    config: ControlPlaneConfig | None = None,
) -> SmartCPControlPlane:
    """Initialize and start the global control plane.

    Args:
        config: Optional configuration

    Returns:
        Started SmartCPControlPlane
    """
    control_plane = get_control_plane(config)
    await control_plane.start()
    return control_plane


async def close_control_plane() -> None:
    """Close the global control plane."""
    global _control_plane

    if _control_plane is not None:
        await _control_plane.stop()
        _control_plane = None
