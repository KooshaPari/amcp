"""
Tests for HTTP/2 + SSE Streaming Module

Tests streaming events, handlers, pipeline management, and FastAPI integration.
"""

import asyncio
import pytest
import json
from optimization.streaming import (
    StreamEvent,
    StreamEventType,
    StreamMetrics,
    SSEStreamHandler,
    StreamingPipeline,
    StreamingOptimizer,
)


@pytest.mark.asyncio
class TestStreamEvent:
    """Test StreamEvent functionality."""

    def test_event_creation(self):
        """Test creating a stream event."""
        event = StreamEvent(
            type=StreamEventType.DATA,
            data={"message": "test"},
        )

        assert event.type == StreamEventType.DATA
        assert event.data == {"message": "test"}
        assert event.event_id is not None
        assert event.timestamp > 0

    def test_event_to_sse_format(self):
        """Test converting event to SSE format."""
        event = StreamEvent(
            type=StreamEventType.DATA,
            data={"message": "hello"},
            event_id="123",
        )

        sse_format = event.to_sse_format()

        assert "id: 123" in sse_format
        assert "event: stream_data" in sse_format
        assert "data:" in sse_format
        assert "hello" in sse_format

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = StreamEvent(
            type=StreamEventType.COMPLETE,
            data={"status": "done"},
        )

        event_dict = event.to_dict()

        assert event_dict["type"] == "stream_complete"
        assert event_dict["data"] == {"status": "done"}
        assert "event_id" in event_dict
        assert "timestamp" in event_dict

    def test_multiline_data_formatting(self):
        """Test SSE formatting with multiline data."""
        event = StreamEvent(
            type=StreamEventType.DATA,
            data="line1\nline2\nline3",
        )

        sse_format = event.to_sse_format()

        assert "data: line1" in sse_format
        assert "data: line2" in sse_format
        assert "data: line3" in sse_format


@pytest.mark.asyncio
class TestStreamMetrics:
    """Test StreamMetrics functionality."""

    def test_metrics_creation(self):
        """Test creating stream metrics."""
        metrics = StreamMetrics(stream_id="test-stream")

        assert metrics.stream_id == "test-stream"
        assert metrics.event_count == 0
        assert metrics.bytes_sent == 0
        assert metrics.error_count == 0
        assert metrics.duration >= 0

    def test_metrics_duration_calculation(self):
        """Test duration calculation."""
        metrics = StreamMetrics(stream_id="test-stream")
        metrics.end_time = metrics.start_time + 10.0

        assert metrics.duration == 10.0

    def test_metrics_throughput_calculation(self):
        """Test throughput calculations."""
        import time

        metrics = StreamMetrics(stream_id="test-stream")
        metrics.event_count = 100
        metrics.bytes_sent = 10000
        metrics.end_time = metrics.start_time + 10.0

        assert metrics.events_per_second == 10.0
        assert metrics.bytes_per_second == 1000.0

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = StreamMetrics(stream_id="test-stream")
        metrics.event_count = 50
        metrics.bytes_sent = 5000

        metrics_dict = metrics.to_dict()

        assert metrics_dict["stream_id"] == "test-stream"
        assert metrics_dict["event_count"] == 50
        assert metrics_dict["bytes_sent"] == 5000
        assert "duration" in metrics_dict
        assert "events_per_second" in metrics_dict


@pytest.mark.asyncio
class TestSSEStreamHandler:
    """Test SSEStreamHandler functionality."""

    async def test_handler_initialization(self):
        """Test initializing SSE handler."""
        handler = SSEStreamHandler()

        await handler.initialize()

        assert handler.metrics is not None
        assert handler.heartbeat_task is not None
        assert handler.queue.maxsize == 100

    async def test_handle_event(self):
        """Test handling a streaming event."""
        handler = SSEStreamHandler()
        await handler.initialize()

        event = StreamEvent(
            type=StreamEventType.DATA,
            data={"test": "data"},
        )

        await handler.handle(event)

        assert handler.metrics.event_count == 1
        assert handler.metrics.bytes_sent > 0

    async def test_queue_backpressure(self):
        """Test queue backpressure handling."""
        handler = SSEStreamHandler(queue_size=2)
        await handler.initialize()

        # Fill queue
        event1 = StreamEvent(type=StreamEventType.DATA, data="1")
        event2 = StreamEvent(type=StreamEventType.DATA, data="2")
        event3 = StreamEvent(type=StreamEventType.DATA, data="3")

        await handler.handle(event1)
        await handler.handle(event2)

        # This should be dropped due to backpressure
        initial_errors = handler.metrics.error_count
        await handler.handle(event3)

        assert handler.metrics.error_count > initial_errors

    async def test_stream_generation(self):
        """Test streaming event generation."""
        handler = SSEStreamHandler()
        await handler.initialize()

        # Create background task to emit events
        async def emit_events():
            event = StreamEvent(type=StreamEventType.DATA, data="test")
            await handler.handle(event)
            await asyncio.sleep(0.1)

        emit_task = asyncio.create_task(emit_events())

        # Collect events from stream
        events = []
        count = 0
        async for event_text in handler.stream():
            events.append(event_text)
            count += 1
            if count >= 1:
                break

        emit_task.cancel()
        try:
            await emit_task
        except asyncio.CancelledError:
            pass

        assert len(events) > 0
        assert "event: stream_data" in events[0]

    async def test_handler_cleanup(self):
        """Test handler cleanup."""
        handler = SSEStreamHandler()
        await handler.initialize()

        await handler.cleanup()

        assert handler.heartbeat_task.cancelled() or handler.heartbeat_task.done()
        assert handler.metrics.end_time is not None


@pytest.mark.asyncio
class TestStreamingPipeline:
    """Test StreamingPipeline functionality."""

    async def test_pipeline_creation(self):
        """Test creating streaming pipeline."""
        pipeline = StreamingPipeline(max_concurrent_streams=10)

        assert pipeline.max_concurrent_streams == 10
        assert len(pipeline.streams) == 0

    async def test_create_stream(self):
        """Test creating a stream."""
        pipeline = StreamingPipeline()
        handler = SSEStreamHandler()

        stream_id = await pipeline.create_stream(handler)

        assert stream_id is not None
        assert stream_id in pipeline.streams
        assert pipeline.get_stream_count() == 1

    async def test_close_stream(self):
        """Test closing a stream."""
        pipeline = StreamingPipeline()
        handler = SSEStreamHandler()
        stream_id = await pipeline.create_stream(handler)

        await pipeline.close_stream(stream_id)

        assert stream_id not in pipeline.streams
        assert pipeline.get_stream_count() == 0

    async def test_emit_event(self):
        """Test emitting event to stream."""
        pipeline = StreamingPipeline()
        handler = SSEStreamHandler()
        stream_id = await pipeline.create_stream(handler)

        event = StreamEvent(type=StreamEventType.DATA, data="test")
        success = await pipeline.emit_event(stream_id, event)

        assert success is True
        assert handler.metrics.event_count == 1

    async def test_emit_to_nonexistent_stream(self):
        """Test emitting to non-existent stream."""
        pipeline = StreamingPipeline()
        event = StreamEvent(type=StreamEventType.DATA, data="test")

        success = await pipeline.emit_event("nonexistent", event)

        assert success is False

    async def test_get_metrics(self):
        """Test getting stream metrics."""
        pipeline = StreamingPipeline()
        handler = SSEStreamHandler()
        stream_id = await pipeline.create_stream(handler)

        metrics = pipeline.get_metrics(stream_id)

        # Metrics stream_id comes from handler, which is different from pipeline stream_id
        assert "stream_id" in metrics
        assert "event_count" in metrics
        assert metrics["event_count"] == 0

    async def test_max_concurrent_streams(self):
        """Test concurrent stream limit."""
        pipeline = StreamingPipeline(max_concurrent_streams=2)

        handler1 = SSEStreamHandler()
        stream_id1 = await pipeline.create_stream(handler1)

        handler2 = SSEStreamHandler()
        stream_id2 = await pipeline.create_stream(handler2)

        # Third stream should block or fail
        handler3 = SSEStreamHandler()
        task = asyncio.create_task(pipeline.create_stream(handler3))

        # Give it a moment
        await asyncio.sleep(0.1)

        # Should still be pending
        assert not task.done()

        # Close one stream
        await pipeline.close_stream(stream_id1)

        # Now third stream should complete
        await asyncio.wait_for(task, timeout=1.0)
        assert task.done()


@pytest.mark.asyncio
class TestStreamingOptimizer:
    """Test StreamingOptimizer functionality."""

    def test_optimizer_creation(self):
        """Test creating optimizer."""
        optimizer = StreamingOptimizer(
            batch_size=5,
            batch_timeout=2.0,
            compress_threshold=500,
        )

        assert optimizer.batch_size == 5
        assert optimizer.batch_timeout == 2.0
        assert optimizer.compress_threshold == 500

    async def test_batch_stream_events(self):
        """Test batching stream events."""
        optimizer = StreamingOptimizer(batch_size=3)

        async def event_generator():
            for i in range(5):
                yield StreamEvent(type=StreamEventType.DATA, data=f"event-{i}")

        batches = []
        async for batch in optimizer.batch_stream_events(event_generator()):
            batches.append(batch)

        assert len(batches) == 2  # 3 + 2
        assert len(batches[0]) == 3
        assert len(batches[1]) == 2

    async def test_compress_event_small_data(self):
        """Test compression doesn't compress small data."""
        optimizer = StreamingOptimizer(compress_threshold=1000)

        event = StreamEvent(
            type=StreamEventType.DATA,
            data={"message": "small"},
        )

        compressed = await optimizer.compress_event(event)

        # Should not be compressed
        assert compressed.type == StreamEventType.DATA
        assert "message" in str(compressed.data)
        assert "compressed" not in str(compressed.data)

    async def test_compress_event_large_data(self):
        """Test compression of large data."""
        optimizer = StreamingOptimizer(compress_threshold=100)

        large_data = {"message": "x" * 200}
        event = StreamEvent(
            type=StreamEventType.DATA,
            data=large_data,
        )

        compressed = await optimizer.compress_event(event)

        # Should be compressed
        assert "compressed" in compressed.data
        assert "original_size" in compressed.data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
