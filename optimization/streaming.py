"""
HTTP/2 + SSE Streaming Implementation

Provides Server-Sent Events (SSE) streaming for long-running operations with:
- HTTP/2 multiplexing support for concurrent streams
- Queue-based event processing with backpressure handling
- Metrics collection for streaming performance monitoring
- Async event handlers with proper resource cleanup
- Integration with FastAPI StreamingResponse

HTTP/2 Benefits:
- Binary framing for efficiency
- Multiplexing (multiple streams on single connection)
- Server push capabilities
- Header compression (HPACK)

SSE Benefits:
- Automatic reconnection support
- Simple text-based protocol
- Built-in event IDs and types
- Low overhead (works over HTTP)

Reference: 2025 LLM Cost Optimization Research
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable, Optional

logger = logging.getLogger(__name__)


class StreamEventType(str, Enum):
    """Types of streaming events."""
    START = "stream_start"
    DATA = "stream_data"
    PROGRESS = "stream_progress"
    ERROR = "stream_error"
    COMPLETE = "stream_complete"
    HEARTBEAT = "stream_heartbeat"


@dataclass
class StreamEvent:
    """Represents a single streaming event."""
    type: StreamEventType
    data: Any
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    retry_ms: Optional[int] = None

    def to_sse_format(self) -> str:
        """Convert event to SSE text format."""
        lines = []

        if self.event_id:
            lines.append(f"id: {self.event_id}")

        lines.append(f"event: {self.type.value}")

        if self.retry_ms:
            lines.append(f"retry: {self.retry_ms}")

        # Serialize data as JSON
        if isinstance(self.data, str):
            data_str = self.data
        else:
            data_str = json.dumps(self.data)

        # SSE format: prepend "data: " to each line
        for line in data_str.split("\n"):
            if line:
                lines.append(f"data: {line}")

        # Add empty line to signal end of event
        lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "type": self.type.value,
            "data": self.data,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
        }


@dataclass
class StreamMetrics:
    """Metrics for streaming performance."""
    stream_id: str
    event_count: int = 0
    bytes_sent: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    error_count: int = 0
    last_event_at: float = field(default_factory=time.time)

    @property
    def duration(self) -> float:
        """Total stream duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def events_per_second(self) -> float:
        """Average events per second."""
        duration = self.duration
        return self.event_count / duration if duration > 0 else 0.0

    @property
    def bytes_per_second(self) -> float:
        """Average bytes per second."""
        duration = self.duration
        return self.bytes_sent / duration if duration > 0 else 0.0

    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            "stream_id": self.stream_id,
            "event_count": self.event_count,
            "bytes_sent": self.bytes_sent,
            "duration": self.duration,
            "events_per_second": self.events_per_second,
            "bytes_per_second": self.bytes_per_second,
            "error_count": self.error_count,
        }


class StreamHandler:
    """Base class for streaming event handlers."""

    async def initialize(self) -> None:
        """Initialize the handler (setup connections, etc)."""
        pass

    async def cleanup(self) -> None:
        """Cleanup resources (close connections, etc)."""
        pass

    async def handle(self, event: StreamEvent) -> None:
        """Process a streaming event."""
        raise NotImplementedError


class SSEStreamHandler(StreamHandler):
    """Handler for Server-Sent Events streaming."""

    def __init__(self, queue_size: int = 100, heartbeat_interval: float = 30.0):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.metrics: Optional[StreamMetrics] = None

    async def initialize(self) -> None:
        """Initialize SSE handler."""
        stream_id = str(uuid.uuid4())
        self.metrics = StreamMetrics(stream_id=stream_id)
        self.heartbeat_task = asyncio.create_task(self._send_heartbeats())

    async def cleanup(self) -> None:
        """Cleanup SSE handler."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.metrics:
            self.metrics.end_time = time.time()
            logger.info(
                f"SSE stream {self.metrics.stream_id} completed",
                extra=self.metrics.to_dict()
            )

    async def handle(self, event: StreamEvent) -> None:
        """Queue a streaming event."""
        try:
            self.queue.put_nowait(event)
            if self.metrics:
                self.metrics.event_count += 1
                self.metrics.bytes_sent += len(event.to_sse_format())
                self.metrics.last_event_at = time.time()
        except asyncio.QueueFull:
            # Drop event if queue is full (backpressure)
            logger.warning(f"SSE queue full, dropping event {event.event_id}")
            if self.metrics:
                self.metrics.error_count += 1

    async def stream(self) -> AsyncIterator[str]:
        """Yield SSE formatted events as they are queued."""
        try:
            while True:
                try:
                    event = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=self.heartbeat_interval + 5.0
                    )
                    yield event.to_sse_format()
                except asyncio.TimeoutError:
                    # Timeout waiting for event, send heartbeat
                    if self.metrics:
                        yield StreamEvent(
                            type=StreamEventType.HEARTBEAT,
                            data={"stream_id": self.metrics.stream_id}
                        ).to_sse_format()
        except asyncio.CancelledError:
            # Stream cancelled, cleanup
            await self.cleanup()
            raise

    async def _send_heartbeats(self) -> None:
        """Send periodic heartbeat events."""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                if self.metrics:
                    await self.handle(
                        StreamEvent(
                            type=StreamEventType.HEARTBEAT,
                            data={"stream_id": self.metrics.stream_id}
                        )
                    )
        except asyncio.CancelledError:
            pass


class StreamingPipeline:
    """Manages multiple concurrent streams with flow control."""

    def __init__(self, max_concurrent_streams: int = 100):
        self.max_concurrent_streams = max_concurrent_streams
        self.streams: dict[str, StreamHandler] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent_streams)
        self.metrics: dict[str, StreamMetrics] = {}

    async def create_stream(self, stream_handler: StreamHandler) -> str:
        """Create a new stream and return its ID."""
        stream_id = str(uuid.uuid4())
        await self.semaphore.acquire()

        try:
            await stream_handler.initialize()
            self.streams[stream_id] = stream_handler

            if isinstance(stream_handler, SSEStreamHandler):
                self.metrics[stream_id] = stream_handler.metrics

            logger.info(f"Created stream {stream_id}")
            return stream_id
        except Exception as e:
            self.semaphore.release()
            logger.error(f"Failed to create stream: {e}")
            raise

    async def close_stream(self, stream_id: str) -> None:
        """Close a stream and release resources."""
        if stream_id not in self.streams:
            return

        handler = self.streams.pop(stream_id)
        await handler.cleanup()
        self.semaphore.release()

        logger.info(f"Closed stream {stream_id}")

    async def emit_event(
        self,
        stream_id: str,
        event: StreamEvent
    ) -> bool:
        """Emit an event to a specific stream."""
        if stream_id not in self.streams:
            return False

        handler = self.streams[stream_id]
        await handler.handle(event)
        return True

    def get_metrics(self, stream_id: Optional[str] = None) -> dict:
        """Get metrics for streams."""
        if stream_id:
            return self.metrics.get(stream_id, {}).to_dict() if stream_id in self.metrics else {}

        # Return metrics for all streams
        return {
            sid: metrics.to_dict()
            for sid, metrics in self.metrics.items()
        }

    def get_stream_count(self) -> int:
        """Get number of active streams."""
        return len(self.streams)


class StreamingOptimizer:
    """Optimizes streaming for batching and compression."""

    def __init__(
        self,
        batch_size: int = 10,
        batch_timeout: float = 1.0,
        compress_threshold: int = 1024
    ):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.compress_threshold = compress_threshold

    async def batch_stream_events(
        self,
        event_stream: AsyncIterator[StreamEvent]
    ) -> AsyncIterator[list[StreamEvent]]:
        """Batch streaming events for more efficient transmission."""
        batch = []
        batch_start = time.time()

        async for event in event_stream:
            batch.append(event)

            # Emit batch if it's full or timeout exceeded
            if len(batch) >= self.batch_size:
                yield batch
                batch = []
                batch_start = time.time()
            elif time.time() - batch_start > self.batch_timeout and batch:
                yield batch
                batch = []
                batch_start = time.time()

        # Emit remaining events
        if batch:
            yield batch

    async def compress_event(self, event: StreamEvent) -> StreamEvent:
        """Compress event data if it exceeds threshold."""
        import gzip
        import base64

        if isinstance(event.data, dict):
            json_str = json.dumps(event.data)
        else:
            json_str = str(event.data)

        if len(json_str) > self.compress_threshold:
            # Compress data
            compressed = gzip.compress(json_str.encode())
            compressed_b64 = base64.b64encode(compressed).decode()

            return StreamEvent(
                type=event.type,
                data={"compressed": compressed_b64, "original_size": len(json_str)},
                event_id=event.event_id,
                timestamp=event.timestamp,
            )

        return event


# Global streaming pipeline instance
_streaming_pipeline: Optional[StreamingPipeline] = None


def get_streaming_pipeline(
    max_concurrent_streams: int = 100,
) -> StreamingPipeline:
    """Get or create global streaming pipeline."""
    global _streaming_pipeline
    if _streaming_pipeline is None:
        _streaming_pipeline = StreamingPipeline(max_concurrent_streams)
    return _streaming_pipeline
