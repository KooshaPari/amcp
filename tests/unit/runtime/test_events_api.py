"""Unit tests for EventsAPI and AgentsAPI."""

import pytest

from smartcp.runtime.events.api import AgentsAPI, BackgroundTask, EventsAPI, create_background_task_api
from smartcp.runtime.events.bus import NATSEventBus
from smartcp.runtime.types import UserContext


class TestEventsAPI:
    """Unit tests for EventsAPI."""

    @pytest.fixture
    def bus(self):
        """Create an event bus."""
        return NATSEventBus()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def events_api(self, bus, user_ctx):
        """Create an events API."""
        return EventsAPI(bus, user_ctx)

    @pytest.mark.asyncio
    async def test_publish(self, events_api):
        """Test publishing events."""
        received = []

        async def handler(data):
            received.append(data)

        await events_api.subscribe("test_topic", handler)
        await events_api.publish("test_topic", {"message": "hello"})

        import asyncio
        await asyncio.sleep(0.1)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_subscribe(self, events_api):
        """Test subscribing to events."""
        call_count = 0

        async def handler(data):
            nonlocal call_count
            call_count += 1

        await events_api.subscribe("topic", handler)
        await events_api.publish("topic", {})

        import asyncio
        await asyncio.sleep(0.1)

        assert call_count == 1


class TestAgentsAPI:
    """Unit tests for AgentsAPI."""

    @pytest.fixture
    def bus(self):
        """Create an event bus."""
        return NATSEventBus()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def agents_api(self, bus, user_ctx):
        """Create an agents API."""
        return AgentsAPI(bus, user_ctx)

    @pytest.mark.asyncio
    async def test_spawn(self, agents_api):
        """Test spawning an agent."""
        result = await agents_api.spawn("worker", {"config": "value"})
        assert result["status"] == "spawned"
        assert "agent_id" in result

    @pytest.mark.asyncio
    async def test_send(self, agents_api):
        """Test sending message to agent."""
        result = await agents_api.send("agent-123", {"message": "hello"})
        assert result["status"] == "sent"


class TestBackgroundTaskAPI:
    """Unit tests for background task API."""

    @pytest.fixture
    def bus(self):
        """Create an event bus."""
        return NATSEventBus()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def bg(self, bus, user_ctx):
        """Create bg() function."""
        return create_background_task_api(bus, user_ctx)

    @pytest.mark.asyncio
    async def test_bg_function(self, bg):
        """Test bg() function creates background task."""

        async def task():
            import asyncio
            await asyncio.sleep(0.1)
            return "result"

        task_handle = await bg(task())

        assert isinstance(task_handle, BackgroundTask)

        result = await task_handle
        assert result == "result"

    @pytest.mark.asyncio
    async def test_task_status(self, bg):
        """Test checking task status."""

        async def task():
            import asyncio
            await asyncio.sleep(0.1)
            return "done"

        task_handle = await bg(task())

        status = await task_handle.status()
        assert status["status"] in ("running", "completed")
