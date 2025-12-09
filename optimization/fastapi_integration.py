"""
FastAPI Integration for Streaming

Provides FastAPI routes and utilities for integrating SSE streaming
with the main application.
"""

import asyncio
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from .streaming import (
    get_streaming_pipeline,
    SSEStreamHandler,
    StreamEvent,
    StreamEventType,
)

logger = logging.getLogger(__name__)


class StreamStartRequest(BaseModel):
    """Request to start a streaming operation."""
    operation: str
    params: Optional[dict] = None


def create_streaming_router() -> APIRouter:
    """Create FastAPI router for streaming operations."""
    router = APIRouter(prefix="/v1/stream", tags=["streaming"])

    @router.post("/start")
    async def start_stream(request: StreamStartRequest) -> dict:
        """
        Start a new streaming operation.

        Args:
            request: StreamStartRequest with operation type

        Returns:
            Dictionary with stream_id and subscribe URL
        """
        try:
            pipeline = get_streaming_pipeline()
            handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
            stream_id = await pipeline.create_stream(handler)

            logger.info(f"Started {request.operation} stream: {stream_id}")

            return {
                "stream_id": stream_id,
                "operation": request.operation,
                "subscribe_url": f"/v1/stream/{stream_id}",
            }
        except Exception as e:
            logger.error(f"Failed to start stream: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{stream_id}")
    async def subscribe_stream(stream_id: str) -> StreamingResponse:
        """
        Subscribe to a streaming operation via SSE.

        Args:
            stream_id: Stream ID from /start

        Returns:
            StreamingResponse with SSE events
        """
        pipeline = get_streaming_pipeline()
        handler = pipeline.streams.get(stream_id)

        if not handler:
            raise HTTPException(status_code=404, detail=f"Stream not found: {stream_id}")

        if not isinstance(handler, SSEStreamHandler):
            raise HTTPException(status_code=400, detail="Stream not SSE enabled")

        async def event_generator():
            """Generate SSE formatted events."""
            try:
                async for event_text in handler.stream():
                    yield event_text
            except asyncio.CancelledError:
                await pipeline.close_stream(stream_id)
                logger.info(f"Stream {stream_id} cancelled")
            except Exception as e:
                logger.error(f"Stream error: {e}")
                await pipeline.close_stream(stream_id)
                raise

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            }
        )

    @router.post("/{stream_id}/event")
    async def emit_event(stream_id: str, event: dict) -> dict:
        """
        Emit an event to a stream.

        Args:
            stream_id: Stream ID
            event: Event with 'type' and 'data'

        Returns:
            Confirmation
        """
        try:
            pipeline = get_streaming_pipeline()
            stream_event = StreamEvent(
                type=StreamEventType(event.get("type", "stream_data")),
                data=event.get("data"),
            )

            success = await pipeline.emit_event(stream_id, stream_event)
            if not success:
                raise HTTPException(status_code=404, detail=f"Stream not found: {stream_id}")

            return {
                "success": True,
                "stream_id": stream_id,
                "event_id": stream_event.event_id,
            }
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/{stream_id}/close")
    async def close_stream(stream_id: str) -> dict:
        """
        Close a streaming operation.

        Args:
            stream_id: Stream ID

        Returns:
            Metrics from closed stream
        """
        try:
            pipeline = get_streaming_pipeline()
            metrics = pipeline.get_metrics(stream_id)
            await pipeline.close_stream(stream_id)

            logger.info(f"Closed stream {stream_id}")

            return {
                "success": True,
                "stream_id": stream_id,
                "metrics": metrics,
            }
        except Exception as e:
            logger.error(f"Failed to close stream: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{stream_id}/metrics")
    async def get_metrics(stream_id: str) -> dict:
        """
        Get metrics for a stream.

        Args:
            stream_id: Stream ID or 'all'

        Returns:
            Metrics dictionary
        """
        try:
            pipeline = get_streaming_pipeline()

            if stream_id == "all":
                return {"streams": pipeline.get_metrics()}

            metrics = pipeline.get_metrics(stream_id)
            if not metrics:
                raise HTTPException(status_code=404, detail=f"Stream not found: {stream_id}")

            return metrics
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/health/status")
    async def stream_health() -> dict:
        """
        Get streaming system health.

        Returns:
            Health status
        """
        pipeline = get_streaming_pipeline()
        return {
            "status": "healthy",
            "active_streams": pipeline.get_stream_count(),
            "max_streams": pipeline.max_concurrent_streams,
        }

    return router
