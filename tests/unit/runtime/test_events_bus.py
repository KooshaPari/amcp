"""Unit tests for NATSEventBus."""

import pytest

from smartcp.runtime.events.bus import NATSEventBus


class TestNATSEventBus:
    """Unit tests for NATSEventBus."""

    @pytest.fixture
    def bus(self):
        """Create an event bus."""
        return NATSEventBus()

    @pytest.mark.asyncio
    async def test_publish(self, bus):
        """Test publishing events."""
        received = []

        async def handler(data):
            received.append(data)

        await bus.subscribe("test_topic", handler)
        await bus.publish("test_topic", {"message": "hello"})

        # Give handler time to process
        import asyncio
        await asyncio.sleep(0.1)

        assert len(received) == 1
        assert received[0]["message"] == "hello"

    @pytest.mark.asyncio
    async def test_subscribe(self, bus):
        """Test subscribing to topics."""
        call_count = 0

        async def handler(data):
            nonlocal call_count
            call_count += 1

        await bus.subscribe("test_topic", handler)
        await bus.publish("test_topic", {"data": "test"})

        import asyncio
        await asyncio.sleep(0.1)

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_create_task(self, bus):
        """Test creating background tasks."""

        async def task_func():
            return "task_result"

        task_id = "test_task"
        await bus.create_task(task_id, task_func())

        import asyncio
        await asyncio.sleep(0.1)

        status = await bus.get_task_status(task_id)
        assert status["status"] == "completed"
        assert status["result"] == "task_result"

    @pytest.mark.asyncio
    async def test_wait_for_task(self, bus):
        """Test waiting for task completion."""

        async def slow_task():
            import asyncio
            await asyncio.sleep(0.1)
            return "done"

        task_id = "slow_task"
        await bus.create_task(task_id, slow_task())

        result = await bus.wait_for_task(task_id, timeout=1.0)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_task_timeout(self, bus):
        """Test task timeout."""

        async def very_slow_task():
            import asyncio
            await asyncio.sleep(10)

        task_id = "timeout_task"
        await bus.create_task(task_id, very_slow_task())

        with pytest.raises(TimeoutError):
            await bus.wait_for_task(task_id, timeout=0.1)
