"""Progress reporting for SmartCP Control Plane."""

import logging
from datetime import UTC, datetime
from typing import Any, Optional

from smartcp.bifrost.control_plane.models import ProgressUpdate

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks and reports operation progress."""

    def __init__(self) -> None:
        """Initialize progress tracker."""
        self._active_operations: dict[str, ProgressUpdate] = {}

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

        # Remove from active operations
        del self._active_operations[operation_id]

        return progress

    async def report_progress(
        self, client: Any, server_id: str, progress: ProgressUpdate
    ) -> None:
        """Report progress to Bifrost.

        Args:
            client: Bifrost client
            server_id: Server ID
            progress: Progress update to report
        """
        if not client:
            return

        try:
            mutation = """
                mutation ReportProgress($serverId: String!, $progress: JSON!) {
                    reportOperationProgress(serverId: $serverId, progress: $progress) {
                        acknowledged
                    }
                }
            """

            await client.mutate(
                mutation,
                variables={
                    "serverId": server_id,
                    "progress": progress.to_dict(),
                },
            )
            logger.debug(
                f"Progress reported: {progress.operation_id} - "
                f"{progress.progress_percent}%"
            )

        except Exception as e:
            logger.warning(f"Progress report failed: {e}")

    def get_active_operations(self) -> list[ProgressUpdate]:
        """Get all active operations.

        Returns:
            List of active ProgressUpdates
        """
        return list(self._active_operations.values())
