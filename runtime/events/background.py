"""Background task support."""

import asyncio
import logging
from typing import Any, Coroutine

from smartcp.runtime.events.bus import NATSEventBus
from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


class BackgroundTask:
    """Awaitable background task handle."""

    def __init__(
        self,
        task_id: str,
        event_bus: NATSEventBus,
        user_ctx: UserContext,
        coro: Coroutine[Any, Any, Any],
    ):
        """Initialize background task.

        Args:
            task_id: Task identifier
            event_bus: Event bus instance
            user_ctx: User context
            coro: Coroutine to execute
        """
        self.task_id = task_id
        self.event_bus = event_bus
        self.user_ctx = user_ctx
        self._coro = coro
        self._task: asyncio.Task | None = None
        self._started = False

    def start(self) -> None:
        """Start the background task."""
        if self._started:
            return

        self._task = asyncio.create_task(self._run())
        self._started = True
        logger.info("Background task started", extra={"task_id": self.task_id})

    async def _run(self) -> Any:
        """Run the background task."""
        try:
            result = await self._coro
            logger.info("Background task completed", extra={"task_id": self.task_id})
            return result
        except Exception as e:
            logger.error("Background task failed", extra={"task_id": self.task_id, "error": str(e)})
            raise

    def __await__(self):
        """Make task awaitable: result = await task"""
        if not self._started:
            self.start()
        return self._task.__await__()

    async def status(self) -> str:
        """Get task status.

        Returns:
            Task status ("pending", "running", "completed", "failed")
        """
        if not self._task:
            return "pending"
        if self._task.done():
            if self._task.exception():
                return "failed"
            return "completed"
        return "running"

    async def result(self) -> Any:
        """Get task result (waits for completion).

        Returns:
            Task result
        """
        if not self._started:
            self.start()
        return await self._task
