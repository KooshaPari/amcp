"""NATS event bus for pub/sub and background tasks."""

import asyncio
import logging
import uuid
from typing import Any, Callable

from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


class NATSEventBus:
    """NATS-based event bus for pub/sub and background tasks.

    Placeholder implementation - Phase 4 will implement full NATS integration.
    """

    def __init__(self, nats_url: str | None = None):
        """Initialize NATS event bus.

        Args:
            nats_url: NATS server URL (optional, uses default if not provided)
        """
        self.nats_url = nats_url or "nats://localhost:4222"
        self._subscribers: dict[str, list[Callable]] = {}
        self._tasks: dict[str, Any] = {}
        logger.info(f"NATSEventBus initialized (URL: {self.nats_url})")

    async def publish(self, topic: str, data: Any) -> None:
        """Publish event to topic.

        Args:
            topic: Topic name
            data: Event data
        """
        logger.info(f"Publishing to topic {topic}: {data}")
        # Placeholder - Phase 4 will implement NATS publish
        if topic in self._subscribers:
            for handler in self._subscribers[topic]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Subscriber error: {e}")

    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to topic.

        Args:
            topic: Topic name
            handler: Async handler function
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)
        logger.info(f"Subscribed to topic: {topic}")

    async def create_task(self, task_id: str, coro: Any) -> None:
        """Create a background task.

        Args:
            task_id: Task identifier
            coro: Coroutine to execute
        """
        self._tasks[task_id] = {
            "id": task_id,
            "status": "running",
            "coro": coro,
        }
        asyncio.create_task(self._run_task(task_id, coro))

    async def _run_task(self, task_id: str, coro: Any) -> None:
        """Run a background task."""
        try:
            result = await coro
            self._tasks[task_id]["status"] = "completed"
            self._tasks[task_id]["result"] = result
        except Exception as e:
            self._tasks[task_id]["status"] = "failed"
            self._tasks[task_id]["error"] = str(e)
            logger.error(f"Task {task_id} failed: {e}")

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Get task status.

        Args:
            task_id: Task identifier

        Returns:
            Task status information
        """
        return self._tasks.get(task_id, {"status": "not_found"})

    async def wait_for_task(self, task_id: str, timeout: float = 300.0) -> Any:
        """Wait for task completion.

        Args:
            task_id: Task identifier
            timeout: Timeout in seconds

        Returns:
            Task result
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            task = self._tasks.get(task_id)
            if task and task["status"] in ("completed", "failed"):
                if task["status"] == "failed":
                    raise RuntimeError(task.get("error", "Task failed"))
                return task.get("result")

            await asyncio.sleep(0.1)

        raise TimeoutError(f"Task {task_id} timed out")
