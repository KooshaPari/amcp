"""
Comprehensive tests for streaming module.

Tests core functionality:
- Stream event creation and formatting
- Stream lifecycle management
- Event emission and subscription
- Error handling in streaming
- HTTP/2 SSE conversion
"""

import asyncio
import pytest
import json
import time

from optimization.streaming import (
    StreamEvent,
    StreamEventType,
    StreamMetrics,
    StreamHandler,
)


class TestStreamEvent:
    """Test StreamEvent dataclass."""

    def test_event_creation(self):
        """Test creating a stream event."""
        event = StreamEvent(
            type=StreamEventType.DATA,
            data={"message": "Hello, world!"},
            retry_ms=3000,
        )

        assert event.type == StreamEventType.DATA
        assert event.data == {"message": "Hello, world!"}
        assert event.retry_ms == 3000
        assert event.event_id is not None
        assert event.timestamp > 0

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = StreamEvent(
            type=StreamEventType.PROGRESS,
            data={"progress": 0.5},
        )

        d = event.to_dict()
        assert d["type"] == "stream_progress"
        assert d["data"] == {"progress": 0.5}
        assert d["event_id"] == event.event_id
        assert d["timestamp"] == event.timestamp

    def test_to_sse_format_basic(self):
        """Test basic SSE format conversion."""
        event = StreamEvent(
            type=StreamEventType.DATA,
            data="Simple text data",
        )

        sse = event.to_sse_format()
        lines = sse.split("\n")
        
        assert "id: " in sse
        assert "event: stream_data" in sse
        assert "data: Simple text data" in sse
        assert sse.endswith("\n\n")  # Double newline at end

    def test_to_sse_format_with_retry(self):
        """Test SSE format with retry."""
        event = StreamEvent(
            type=StreamEventType.ERROR,
            data={"error": "Something went wrong"},
            retry_ms=5000,
        )

        sse = event.to_sse_format()
        
        assert "retry: 5000" in sse
        assert "event: stream_error" in sse
        assert "data: {\"error\": \"Something went wrong\"}" in sse

    def test_to_sse_format_multiline_data(self):
        """Test SSE format with multiline data."""
        event = StreamEvent(
            type=StreamEventType.DATA,
            data="Line 1\nLine 2\nLine 3",
        )

        sse = event.to_sse_format()
        
        # Each line should be prefixed with "data: "
        assert "data: Line 1" in sse
        assert "data: Line 2" in sse
        assert "data: Line 3" in sse

    def test_to_sse_format_json_data(self):
        """Test SSE format with JSON data."""
        json_data = {"key": "value", "number": 42, "nested": {"a": 1}}
        event = StreamEvent(
            type=StreamEventType.START,
            data=json_data,
        )

        sse = event.to_sse_format()
        
        # Should serialize JSON
        assert "\"key\": \"value\"" in sse
        assert "\"number\": 42" in sse
        assert "\"nested\": {\"a\": 1}" in sse

    def test_event_types(self):
        """Test all event types."""
        for event_type in StreamEventType:
            event = StreamEvent(type=event_type, data="test")
            assert event.type == event_type
            assert event.type.value in event.to_sse_format()

    def test_event_ordering(self):
        """Test that events maintain timestamp order."""
        events = []
        
        for i in range(5):
            event = StreamEvent(
                type=StreamEventType.DATA,
                data=f"data_{i}",
            )
            events.append(event)
            time.sleep(0.01)  # Small delay
        
        # Check timestamps are increasing
        for i in range(1, len(events)):
            assert events[i].timestamp > events[i-1].timestamp


class TestStreamMetrics:
    """Test StreamMetrics dataclass."""

    def test_metrics_creation(self):
        """Test creating stream metrics."""
        metrics = StreamMetrics(
            stream_id="test_stream_123",
        )

        assert metrics.stream_id == "test_stream_123"
        assert metrics.event_count == 0
        assert metrics.bytes_sent == 0
        assert metrics.start_time > 0
        assert metrics.end_time is None
        assert metrics.error_count == 0
        assert metrics.last_event_at > 0

    def test_duration_calculation(self):
        """Test duration calculation."""
        start = time.time()
        time.sleep(0.1)
        
        metrics = StreamMetrics(
            stream_id="test",
            start_time=start,
        )
        
        duration = metrics.duration
        assert 0.1 <= duration <= 0.2

    def test_duration_with_end_time(self):
        """Test duration with explicit end time."""
        start = time.time()
        time.sleep(0.05)
        end = time.time()
        
        metrics = StreamMetrics(
            stream_id="test",
            start_time=start,
            end_time=end,
        )
        
        duration = metrics.duration
        assert 0.05 <= duration <= 0.06

    def test_events_per_second(self):
        """Test events per second calculation."""
        metrics = StreamMetrics(
            stream_id="test",
            event_count=10,
        )
        
        # Simulate some time passing
        time.sleep(0.1)
        
        eps = metrics.events_per_second
        assert eps > 0
        
        # With 10 events and ~0.1s, should be ~100 eps
        assert 50 < eps < 200

    def test_bytes_per_second(self):
        """Test bytes per second calculation."""
        metrics = StreamMetrics(
            stream_id="test",
            bytes_sent=1024,
        )
        
        time.sleep(0.1)
        
        bps = metrics.bytes_per_second
        assert bps > 0
        
        # With 1024 bytes and ~0.1s, should be ~10240 bps
        assert 5000 < bps < 20000

    def test_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = StreamMetrics(
            stream_id="test_stream",
            event_count=5,
            bytes_sent=500,
            error_count=1,
        )

        d = metrics.to_dict()
        assert d["stream_id"] == "test_stream"
        assert d["event_count"] == 5
        assert d["bytes_sent"] == 500
        assert d["error_count"] == 1
        assert "duration" in d
        assert "events_per_second" in d
        assert "bytes_per_second" in d


class TestStreamHandler:
    """Test StreamHandler base class."""

    async def test_initialization(self):
        """Test handler initialization."""
        handler = TestHandler()
        
        # Should be able to initialize without error
        await handler.initialize()
        
        # Should be able to cleanup without error
        await handler.cleanup()

    async def test_handle_not_implemented(self):
        """Test that handle raises NotImplementedError."""
        handler = TestHandler()
        
        with pytest.raises(NotImplementedError):
            await handler.handle(StreamEvent(type=StreamEventType.DATA, data="test"))

    async def test_concurrent_initialization(self):
        """Test concurrent initialization."""
        handler = TestHandler()
        
        # Should handle concurrent initialization
        await asyncio.gather(
            handler.initialize(),
            handler.initialize(),
            handler.initialize(),
        )

    async def test_concurrent_cleanup(self):
        """Test concurrent cleanup."""
        handler = TestHandler()
        
        await handler.initialize()
        
        # Should handle concurrent cleanup
        await asyncio.gather(
            handler.cleanup(),
            handler.cleanup(),
            handler.cleanup(),
        )


class MockStreamHandler(StreamHandler):
    """Mock stream handler for testing."""
    
    def __init__(self):
        self.events = []
        self.initialized = False
        self.cleaned_up = False
    
    async def initialize(self):
        self.initialized = True
    
    async def cleanup(self):
        self.cleaned_up = True
    
    async def handle(self, event: StreamEvent):
        self.events.append(event)


class TestStreamHandlerImplementation:
    """Test actual stream handler implementation."""

    async def test_event_handling(self):
        """Test handling stream events."""
        handler = MockStreamHandler()
        await handler.initialize()
        
        # Send multiple events
        events = [
            StreamEvent(type=StreamEventType.START, data="start"),
            StreamEvent(type=StreamEventType.DATA, data="data1"),
            StreamEvent(type=StreamEventType.DATA, data="data2"),
            StreamEvent(type=StreamEventType.COMPLETE, data="end"),
        ]
        
        for event in events:
            await handler.handle(event)
        
        # Check all events were received
        assert len(handler.events) == len(events)
        for i, event in enumerate(events):
            assert handler.events[i] == event
        
        await handler.cleanup()
        assert handler.cleaned_up

    async def test_event_order_preservation(self):
        """Test that event order is preserved."""
        handler = MockStreamHandler()
        await handler.initialize()
        
        # Send events with specific ordering
        event_order = [3, 1, 4, 2]
        for i in event_order:
            event = StreamEvent(
                type=StreamEventType.DATA,
                data={"order": i}
            )
            await handler.handle(event)
        
        # Check order is preserved
        for i, expected_order in enumerate(event_order):
            assert handler.events[i].data["order"] == expected_order
        
        await handler.cleanup()

    async def test_error_handling(self):
        """Test error handling in stream handler."""
        handler = MockStreamHandler()
        await handler.initialize()
        
        # Send error event
        error_event = StreamEvent(
            type=StreamEventType.ERROR,
            data={"error": "Test error", "code": 500}
        )
        await handler.handle(error_event)
        
        # Check error event was received
        assert len(handler.events) == 1
        assert handler.events[0].type == StreamEventType.ERROR
        assert handler.events[0].data["error"] == "Test error"
        
        await handler.cleanup()

    async def test_concurrent_event_handling(self):
        """Test concurrent event handling."""
        handler = MockStreamHandler()
        await handler.initialize()
        
        # Send events concurrently
        events = [
            StreamEvent(type=StreamEventType.DATA, data=f"data_{i}")
            for i in range(10)
        ]
        
        tasks = [handler.handle(event) for event in events]
        await asyncio.gather(*tasks)
        
        # Should receive all events
        assert len(handler.events) == 10
        
        # Order might not be preserved due to concurrency
        event_data = {e.data for e in handler.events}
        assert event_data == {f"data_{i}" for i in range(10)}
        
        await handler.cleanup()


class TestStreamHandler:
    """Test generic stream handler functionality."""
    
    def test_handler_instantiation(self):
        """Test that StreamHandler can be subclassed."""
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            StreamHandler()
        
        # Should be able to subclass
        class CustomHandler(StreamHandler):
            async def handle(self, event):
                pass
        
        handler = CustomHandler()
        assert handler is not None


class TestStreamEventEdgeCases:
    """Test edge cases for stream events."""
    
    def test_empty_data(self):
        """Test event with empty data."""
        event = StreamEvent(type=StreamEventType.DATA, data="")
        
        sse = event.to_sse_format()
        assert "data: " in sse
        assert sse.endswith("\n\n")

    def test_none_data(self):
        """Test event with None data."""
        event = StreamEvent(type=StreamEventType.DATA, data=None)
        
        sse = event.to_sse_format()
        assert "data: None" in sse

    def test_large_data(self):
        """Test event with large data."""
        large_data = "x" * 10000  # 10KB
        event = StreamEvent(type=StreamEventType.DATA, data=large_data)
        
        sse = event.to_sse_format()
        assert len(sse) > 10000
        assert "data: " in sse
        assert large_data in sse

    def test_unicode_data(self):
        """Test event with Unicode data."""
        unicode_data = "Hello 🌍 世界"
        event = StreamEvent(type=StreamEventType.DATA, data=unicode_data)
        
        sse = event.to_sse_format()
        assert unicode_data in sse

    def test_special_characters_in_data(self):
        """Test data with special characters."""
        special_data = "Line 1\r\n\t\"'\\"
        event = StreamEvent(type=StreamEventType.DATA, data=special_data)
        
        sse = event.to_sse_format()
        assert special_data in sse


# Helper class for testing
class TestHandler(StreamHandler):
    pass
