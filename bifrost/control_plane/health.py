"""Health check reporting for SmartCP Control Plane."""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from smartcp.bifrost.control_plane.models import ServerHealth, ServerStatus

logger = logging.getLogger(__name__)


class HealthChecker:
    """Handles health check reporting."""

    def __init__(self, start_time: float = 0) -> None:
        """Initialize health checker.

        Args:
            start_time: Server start time
        """
        self._start_time = start_time

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

        if memory_mb > 1024:  # > 1GB
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

    async def report_health(
        self, client: Any, server_id: str, health: ServerHealth
    ) -> None:
        """Report server health to Bifrost.

        Args:
            client: Bifrost client
            server_id: Server ID
            health: Health status
        """
        if not client:
            return

        try:
            mutation = """
                mutation ReportServerHealth($serverId: String!, $health: JSON!) {
                    reportServerHealth(serverId: $serverId, health: $health) {
                        acknowledged
                    }
                }
            """

            await client.mutate(
                mutation,
                variables={
                    "serverId": server_id,
                    "health": health.to_dict(),
                },
            )
            logger.debug(f"Health reported: {health.status.value}")

        except Exception as e:
            logger.warning(f"Health report failed: {e}")

    def update_start_time(self, start_time: float) -> None:
        """Update server start time.

        Args:
            start_time: New start time
        """
        self._start_time = start_time
