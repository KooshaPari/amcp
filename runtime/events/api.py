"""Events and agents API for agent namespace."""

import logging
import uuid
from typing import Any, Callable

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
    ):
        """Initialize background task.

        Args:
            task_id: Task identifier
            event_bus: Event bus
            user_ctx: User context
        """
        self._task_id = task_id
        self._event_bus = event_bus
        self._user_ctx = user_ctx

    def __await__(self):
        """Wait for task completion."""
        return self._wait().__await__()

    async def _wait(self) -> Any:
        """Wait for task result."""
        return await self._event_bus.wait_for_task(self._task_id)

    async def status(self) -> dict[str, Any]:
        """Get task status without waiting."""
        return await self._event_bus.get_task_status(self._task_id)


def create_background_task_api(
    event_bus: NATSEventBus,
    user_ctx: UserContext,
) -> Callable:
    """Create bg() function for background tasks.

    Args:
        event_bus: Event bus
        user_ctx: User context

    Returns:
        bg() function
    """
    async def bg(coro: Any) -> BackgroundTask:
        """Create a background task.

        Args:
            coro: Coroutine to run in background

        Returns:
            BackgroundTask handle
        """
        task_id = str(uuid.uuid4())
        await event_bus.create_task(task_id, coro)
        return BackgroundTask(task_id, event_bus, user_ctx)

    return bg


class EventsAPI:
    """Events API for pub/sub."""

    def __init__(
        self,
        event_bus: NATSEventBus,
        user_ctx: UserContext,
    ):
        """Initialize events API.

        Args:
            event_bus: Event bus
            user_ctx: User context
        """
        self._event_bus = event_bus
        self._user_ctx = user_ctx

    async def publish(self, topic: str, data: Any) -> None:
        """Publish event to topic."""
        await self._event_bus.publish(topic, data)

    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to topic."""
        await self._event_bus.subscribe(topic, handler)


class AgentsAPI:
    """Agents API for inter-agent communication."""

    def __init__(
        self,
        event_bus: NATSEventBus,
        user_ctx: UserContext,
    ):
        """Initialize agents API.

        Args:
            event_bus: Event bus
            user_ctx: User context
        """
        self._event_bus = event_bus
        self._user_ctx = user_ctx

    async def spawn(self, agent_type: str, config: dict[str, Any]) -> dict[str, Any]:
        """Spawn a new agent.

        Args:
            agent_type: Type of agent to spawn
            config: Agent configuration

        Returns:
            Agent information
        """
        agent_id = str(uuid.uuid4())
        logger.info(f"Spawning agent: {agent_type} (ID: {agent_id})")
        # Placeholder - Phase 4 will implement agent spawning
        return {
            "status": "spawned",
            "agent_id": agent_id,
            "agent_type": agent_type,
        }

    async def send(self, agent_id: str, message: Any) -> dict[str, Any]:
        """Send message to agent.

        Args:
            agent_id: Agent identifier
            message: Message to send

        Returns:
            Send result
        """
        topic = f"agents.{agent_id}.messages"
        await self._event_bus.publish(topic, message)
        return {
            "status": "sent",
            "agent_id": agent_id,
        }
