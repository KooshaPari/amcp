"""SmartCP Control Plane Orchestrator."""

import asyncio
import logging
import time
from typing import Any

from smartcp.bifrost.control_plane.capabilities import CapabilityManager
from smartcp.bifrost.control_plane.client import BifrostClient
from smartcp.bifrost.control_plane.health import HealthChecker
from smartcp.bifrost.control_plane.models import (
    CapabilityType,
    ControlPlaneConfig,
    ProgressUpdate,
    ServerCapability,
    ServerHealth,
)
from smartcp.bifrost.control_plane.progress import ProgressTracker

logger = logging.getLogger(__name__)


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
        self._client = BifrostClient(self._config)
        self._running = False
        self._start_time: float = 0

        # Initialize managers
        self._capability_manager = CapabilityManager()
        self._health_checker = HealthChecker()
        self._progress_tracker = ProgressTracker()

        # Background tasks
        self._heartbeat_task: asyncio.Task | None = None
        self._health_check_task: asyncio.Task | None = None

        logger.info("SmartCPControlPlane initialized")

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
        self._health_checker.update_start_time(self._start_time)

        # Connect to Bifrost
        try:
            await self._client.connect()
        except Exception as e:
            logger.error(f"Failed to connect to Bifrost: {e}")
            # Continue without connection - will retry

        # Register capabilities
        await self._capability_manager.register_with_bifrost(
            self._client._client, self._config.server_id
        )

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
        await self._client.disconnect()

        logger.info("SmartCP control plane stopped")

    async def __aenter__(self) -> "SmartCPControlPlane":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()

    async def _heartbeat_loop(self) -> None:
        """Background heartbeat to Bifrost."""
        while self._running:
            try:
                await asyncio.sleep(self._config.heartbeat_interval)

                if not self._running:
                    break

                await self._client.send_heartbeat()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def _health_check_loop(self) -> None:
        """Background health check reporting."""
        while self._running:
            try:
                await asyncio.sleep(self._config.health_check_interval)

                if not self._running:
                    break

                health = await self._health_checker.get_health()
                await self._health_checker.report_health(
                    self._client._client, self._config.server_id, health
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def get_health(self) -> ServerHealth:
        """Get current server health.

        Returns:
            ServerHealth status
        """
        return await self._health_checker.get_health()

    @property
    def capabilities(self) -> list[ServerCapability]:
        """Get server capabilities."""
        return self._capability_manager.capabilities

    def add_capability(self, capability: ServerCapability) -> None:
        """Add a capability.

        Args:
            capability: Capability to add
        """
        self._capability_manager.add_capability(capability)

    def remove_capability(self, name: CapabilityType) -> bool:
        """Remove a capability.

        Args:
            name: Capability name to remove

        Returns:
            True if removed
        """
        return self._capability_manager.remove_capability(name)

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
        progress = await self._progress_tracker.start_operation(
            operation_id, operation_type, message, metadata
        )
        await self._progress_tracker.report_progress(
            self._client._client, self._config.server_id, progress
        )
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
        progress = await self._progress_tracker.update_progress(
            operation_id, progress_percent, message, status, metadata
        )
        if progress:
            await self._progress_tracker.report_progress(
                self._client._client, self._config.server_id, progress
            )
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
        progress = await self._progress_tracker.complete_operation(
            operation_id, message, success, metadata
        )
        if progress:
            await self._progress_tracker.report_progress(
                self._client._client, self._config.server_id, progress
            )
        return progress

    def get_active_operations(self) -> list[ProgressUpdate]:
        """Get all active operations.

        Returns:
            List of active ProgressUpdates
        """
        return self._progress_tracker.get_active_operations()

    # Configuration Sync

    async def sync_configuration(self) -> dict[str, Any]:
        """Sync configuration with Bifrost.

        Returns:
            Synced configuration
        """
        return await self._client.sync_configuration()

    async def push_configuration(self, config: dict[str, Any]) -> bool:
        """Push configuration to Bifrost.

        Args:
            config: Configuration to push

        Returns:
            True if successful
        """
        return await self._client.push_configuration(config)


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
