"""
Background task management with bg/await pattern.

Implements shell-like background execution with task lifecycle management,
suspend/resume (Ctrl+Z equivalent), and result retrieval.
"""

import asyncio
import logging
import uuid
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Background task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


@dataclass
class BackgroundTask:
    """Background task with lifecycle tracking."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    coroutine: Optional[Callable] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[Exception] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    asyncio_task: Optional[asyncio.Task] = None

    def duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()


class BackgroundTaskManager:
    """Manage background task lifecycle with bg/await pattern."""

    def __init__(self):
        self.tasks: dict[str, BackgroundTask] = {}
        self.active_tasks: set[asyncio.Task] = set()  # Strong refs to prevent GC
        self.lock = asyncio.Lock()

    async def create_task(
        self, coro: Callable, task_id: Optional[str] = None
    ) -> str:
        """Create background task (returns immediately)."""
        tid = task_id or str(uuid.uuid4())
        task = BackgroundTask(task_id=tid, coroutine=coro)

        async with self.lock:
            self.tasks[tid] = task

        logger.info(f"Background task created: {tid}")
        return tid

    async def run_task(self, task_id: str) -> None:
        """Start execution of background task."""
        async with self.lock:
            if task_id not in self.tasks:
                raise ValueError(f"Task not found: {task_id}")

            task = self.tasks[task_id]
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

        try:
            # Create asyncio task with strong reference
            asyncio_task = asyncio.create_task(task.coroutine())

            async with self.lock:
                task.asyncio_task = asyncio_task
                self.active_tasks.add(asyncio_task)  # Prevent GC

            # Add callback to clean up on completion
            asyncio_task.add_done_callback(
                lambda t: asyncio.create_task(self._on_task_done(task_id))
            )

            logger.info(f"Task started: {task_id}")

        except Exception as e:
            async with self.lock:
                task.status = TaskStatus.FAILED
                task.error = e
                task.completed_at = datetime.now()
            logger.error(f"Error starting task {task_id}: {e}")

    async def _on_task_done(self, task_id: str) -> None:
        """Handle task completion."""
        async with self.lock:
            if task_id not in self.tasks:
                return

            task = self.tasks[task_id]
            asyncio_task = task.asyncio_task

            if asyncio_task is None:
                return

            try:
                task.result = asyncio_task.result()
                task.status = TaskStatus.COMPLETED
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
            except Exception as e:
                task.error = e
                task.status = TaskStatus.FAILED
            finally:
                task.completed_at = datetime.now()
                self.active_tasks.discard(asyncio_task)

            logger.info(f"Task completed: {task_id}, status={task.status.value}")

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status."""
        async with self.lock:
            task = self.tasks.get(task_id)
            return task.status if task else None

    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get task result (await if not ready)."""
        async with self.lock:
            task = self.tasks.get(task_id)
            if task is None:
                return None

            asyncio_task = task.asyncio_task

        # If task is running, wait for completion
        if asyncio_task and not asyncio_task.done():
            try:
                return await asyncio.wait_for(asyncio_task, timeout=None)
            except Exception as e:
                logger.error(f"Error waiting for task {task_id}: {e}")
                return None

        return task.result if task else None

    async def suspend_task(self, task_id: str) -> bool:
        """Suspend (pause) background task."""
        async with self.lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]
            if task.status != TaskStatus.RUNNING:
                return False

            task.status = TaskStatus.SUSPENDED
            # Note: Task continues running but marked as suspended
            logger.info(f"Task suspended: {task_id}")
            return True

    async def resume_task(self, task_id: str) -> bool:
        """Resume (unpause) suspended task."""
        async with self.lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]
            if task.status != TaskStatus.SUSPENDED:
                return False

            task.status = TaskStatus.RUNNING
            logger.info(f"Task resumed: {task_id}")
            return True

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel background task."""
        async with self.lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]
            if task.asyncio_task and not task.asyncio_task.done():
                task.asyncio_task.cancel()
                task.status = TaskStatus.CANCELLED
                logger.info(f"Task cancelled: {task_id}")
                return True

        return False

    async def list_tasks(
        self, status_filter: Optional[TaskStatus] = None
    ) -> dict[str, dict[str, Any]]:
        """List all tasks with optional status filter."""
        async with self.lock:
            result = {}
            for tid, task in self.tasks.items():
                if status_filter and task.status != status_filter:
                    continue

                result[tid] = {
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat()
                    if task.started_at
                    else None,
                    "duration": task.duration(),
                    "has_result": task.result is not None,
                    "has_error": task.error is not None,
                }
            return result

    async def cleanup(self) -> None:
        """Cleanup all tasks on shutdown."""
        async with self.lock:
            # Cancel all running tasks
            for task_id, task in self.tasks.items():
                if task.asyncio_task and not task.asyncio_task.done():
                    task.asyncio_task.cancel()

            self.active_tasks.clear()
            logger.info("Background task cleanup complete")
