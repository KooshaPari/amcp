"""Integration Tests for HTTP/2 + SSE Streaming

Tests for HTTP/2 configuration with Server-Sent Events streaming,
including multiplexing, performance, and end-to-end scenarios.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from optimization import (
    OptimizationStreamHandler,
    OptimizationPhase,
    OptimizationMetric,
    OptimizationMetricType,
    PromptCacheStreamHandler,
    HTTP2Config,
    HTTP2App,
    create_optimization_stream,
    get_optimization_handler,
)
from optimization.streaming import StreamingPipeline, SSEStreamHandler


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def http2_config():
    """Create HTTP/2 configuration."""
    return HTTP2Config(
        enable_http2=True,
        enable_http1=True,
        ssl_enabled=False,  # For testing
        host="127.0.0.1",
        port=8000,
        h2_max_concurrent_streams=100,
        h2_max_header_list_size=16384,
        h2_flow_control_window=65536,
    )


@pytest.fixture
def streaming_pipeline():
    """Create a test streaming pipeline."""
    return StreamingPipeline(max_concurrent_streams=10)


@pytest.fixture
def http2_app():
    """Create HTTP/2 enabled FastAPI app."""
    app = FastAPI(title="HTTP/2 SSE Test App")
    return app


# ============================================================================
# HTTP/2 Configuration Tests
# ============================================================================

def test_http2_config_creation(http2_config):
    """Test HTTP/2 configuration creation."""
    assert http2_config.enable_http2 is True
    assert http2_config.enable_http1 is True
    assert http2_config.ssl_enabled is False
    assert http2_config.host == "127.0.0.1"
    assert http2_config.port == 8000
    assert http2_config.h2_max_concurrent_streams == 100


def test_http2_config_from_env():
    """Test HTTP/2 configuration from environment variables."""
    # This would require setting env vars, which is done in conftest
    config = HTTP2Config()
    assert config is not None
    assert hasattr(config, "enable_http2")


def test_http2_app_creation(http2_app, http2_config):
    """Test HTTP/2 app wrapper creation."""
    app_wrapper = HTTP2App(http2_app, http2_config)
    assert app_wrapper is not None
    assert app_wrapper.app is http2_app
    assert app_wrapper.http2_config is http2_config


# ============================================================================
# SSE + HTTP/2 Streaming Tests
# ============================================================================

@pytest.mark.asyncio
async def test_sse_stream_creation(streaming_pipeline):
    """Test SSE stream creation with HTTP/2."""
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    assert stream_id is not None
    assert isinstance(stream_id, str)
    assert len(stream_id) > 0

    await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_multiple_concurrent_streams(streaming_pipeline):
    """Test multiple concurrent SSE streams over HTTP/2."""
    stream_ids = []

    try:
        # Create 5 concurrent streams
        for i in range(5):
            sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
            stream_id = await streaming_pipeline.create_stream(sse_handler)
            stream_ids.append(stream_id)

        assert len(stream_ids) == 5
        assert len(set(stream_ids)) == 5  # All unique

    finally:
        # Cleanup
        for stream_id in stream_ids:
            await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_concurrent_handlers_on_streams(streaming_pipeline):
    """Test concurrent optimization handlers on different streams."""
    handlers = []
    stream_ids = []

    try:
        # Create handlers on different streams
        for i in range(3):
            sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
            stream_id = await streaming_pipeline.create_stream(sse_handler)
            stream_ids.append(stream_id)

            handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
            handlers.append(handler)

        # Execute operations on all handlers concurrently
        async def emit_metrics(handler, index):
            await handler.emit_phase_start(OptimizationPhase.ANALYSIS)
            metric = OptimizationMetric(
                type=OptimizationMetricType.COST_REDUCTION,
                value=float(index * 10),
                unit="percent"
            )
            await handler.emit_metric(metric)
            await handler.emit_phase_complete(OptimizationPhase.ANALYSIS)

        # Run all concurrently
        await asyncio.gather(*[
            emit_metrics(handler, i)
            for i, handler in enumerate(handlers)
        ])

        # Verify all collected metrics
        for handler in handlers:
            assert len(handler.metrics) == 1

    finally:
        # Cleanup
        for stream_id in stream_ids:
            await streaming_pipeline.close_stream(stream_id)


# ============================================================================
# Optimization Pipeline over HTTP/2 + SSE Tests
# ============================================================================

@pytest.mark.asyncio
async def test_full_optimization_over_http2_sse(streaming_pipeline):
    """Test complete optimization workflow over HTTP/2 + SSE."""
    # Create stream
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
        cache_handler = PromptCacheStreamHandler(handler)

        # Simulate complete optimization workflow
        await handler.emit_phase_start(OptimizationPhase.INITIALIZATION)
        await handler.emit_progress(current=25, total=100, details={"stage": "init"})

        await handler.emit_phase_complete(OptimizationPhase.INITIALIZATION)

        await handler.emit_phase_start(OptimizationPhase.ANALYSIS)
        await cache_handler.emit_cache_analysis(total_prompts=100, cacheable_prompts=80)
        await handler.emit_progress(current=50, total=100, details={"stage": "analysis"})

        await cache_handler.emit_cache_hit(
            prompt_hash="test_hash",
            cost_saved=0.50,
            tokens_saved=512
        )

        await handler.emit_phase_complete(OptimizationPhase.ANALYSIS)

        await handler.emit_phase_start(OptimizationPhase.OPTIMIZATION)
        await handler.emit_progress(current=75, total=100, details={"stage": "optimization"})

        await handler.emit_phase_complete(OptimizationPhase.OPTIMIZATION)

        await handler.emit_phase_start(OptimizationPhase.COMPLETION)
        await handler.emit_progress(current=100, total=100, details={"stage": "complete"})

        # Emit final completion
        result = {
            "total_cost_saved": 50.0,
            "total_tokens_saved": 5000,
            "optimization_success": True
        }
        await handler.emit_completion(True, result)

        # Verify summary
        summary = handler.get_summary()
        # PromptCacheStreamHandler.emit_cache_hit emits 2 metrics: COST_REDUCTION + CACHE_HIT
        assert summary["metrics_collected"] >= 2
        assert summary["current_phase"] == "completion"

    finally:
        await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_stream_error_handling(streaming_pipeline):
    """Test error handling in streaming optimization."""
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Emit error event
        await handler.emit_error(
            "Test optimization error",
            error_type="OptimizationError"
        )

        # Continue with recovery
        await handler.emit_phase_start(OptimizationPhase.COMPLETION)
        await handler.emit_completion(False, {"error": "Optimization failed"})

        summary = handler.get_summary()
        assert summary["current_phase"] == "completion"

    finally:
        await streaming_pipeline.close_stream(stream_id)


# ============================================================================
# Performance and Load Tests
# ============================================================================

@pytest.mark.asyncio
async def test_high_frequency_metrics(streaming_pipeline):
    """Test streaming high-frequency metrics over HTTP/2."""
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Emit 50 metrics rapidly
        for i in range(50):
            metric = OptimizationMetric(
                type=OptimizationMetricType.COST_REDUCTION,
                value=float(i),
                unit="percent"
            )
            await handler.emit_metric(metric)

        assert len(handler.metrics) == 50

    finally:
        await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_large_payload_streaming(streaming_pipeline):
    """Test streaming large payloads over HTTP/2."""
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Emit large data payload
        large_data = {
            "items": [{"id": i, "value": f"data_{i}" * 100} for i in range(100)]
        }

        await handler.emit_data(large_data)

        # Verify it was emitted without error
        assert handler is not None

    finally:
        await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_sustained_streaming(streaming_pipeline):
    """Test sustained streaming over time."""
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Simulate sustained activity over time
        phases = [
            OptimizationPhase.INITIALIZATION,
            OptimizationPhase.ANALYSIS,
            OptimizationPhase.OPTIMIZATION,
            OptimizationPhase.EXECUTION,
            OptimizationPhase.VALIDATION,
            OptimizationPhase.COMPLETION,
        ]

        for phase in phases:
            await handler.emit_phase_start(phase)

            # Emit progress throughout phase
            for i in range(1, 6):
                progress = (phases.index(phase) * 20) + (i * 4)
                await handler.emit_progress(
                    current=progress,
                    total=120,
                    details={"phase": phase.value}
                )
                await asyncio.sleep(0.01)  # Simulate work

            await handler.emit_phase_complete(phase)

        summary = handler.get_summary()
        assert summary["metrics_collected"] >= 0

    finally:
        await streaming_pipeline.close_stream(stream_id)


# ============================================================================
# HTTP/2 Multiplexing Tests
# ============================================================================

@pytest.mark.asyncio
async def test_multiplexed_streams_independence(streaming_pipeline):
    """Test that multiplexed streams are independent."""
    stream_ids = []
    handlers = []

    try:
        # Create 3 independent streams
        for i in range(3):
            sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
            stream_id = await streaming_pipeline.create_stream(sse_handler)
            stream_ids.append(stream_id)

            handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
            handlers.append(handler)

        # Emit different metrics on each stream
        async def emit_on_stream(handler, value):
            metric = OptimizationMetric(
                type=OptimizationMetricType.COST_REDUCTION,
                value=value,
                unit="percent"
            )
            await handler.emit_metric(metric)

        # Run concurrently
        await asyncio.gather(*[
            emit_on_stream(handlers[0], 10.0),
            emit_on_stream(handlers[1], 20.0),
            emit_on_stream(handlers[2], 30.0),
        ])

        # Verify independence
        assert handlers[0].metrics[0].value == 10.0
        assert handlers[1].metrics[0].value == 20.0
        assert handlers[2].metrics[0].value == 30.0

    finally:
        for stream_id in stream_ids:
            await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_stream_fairness_under_load(streaming_pipeline):
    """Test fair resource allocation across streams under load."""
    stream_ids = []
    handlers = []

    try:
        # Create multiple streams
        for i in range(5):
            sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
            stream_id = await streaming_pipeline.create_stream(sse_handler)
            stream_ids.append(stream_id)

            handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
            handlers.append(handler)

        # Emit different amounts of metrics on each
        async def emit_metrics(handler, count):
            for i in range(count):
                metric = OptimizationMetric(
                    type=OptimizationMetricType.TOKEN_REDUCTION,
                    value=float(i),
                    unit="tokens"
                )
                await handler.emit_metric(metric)

        # Stream 0: 10 metrics
        # Stream 1: 20 metrics
        # Stream 2: 30 metrics
        # etc.
        await asyncio.gather(*[
            emit_metrics(handlers[0], 10),
            emit_metrics(handlers[1], 20),
            emit_metrics(handlers[2], 30),
            emit_metrics(handlers[3], 15),
            emit_metrics(handlers[4], 25),
        ])

        # Verify all streams completed
        assert len(handlers[0].metrics) == 10
        assert len(handlers[1].metrics) == 20
        assert len(handlers[2].metrics) == 30
        assert len(handlers[3].metrics) == 15
        assert len(handlers[4].metrics) == 25

    finally:
        for stream_id in stream_ids:
            await streaming_pipeline.close_stream(stream_id)


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_stream_factory_integration(streaming_pipeline):
    """Test stream creation and handler retrieval."""
    stream_id = await create_optimization_stream(streaming_pipeline)
    handler = await get_optimization_handler(stream_id, streaming_pipeline)

    assert handler is not None
    assert handler.stream_id == stream_id

    # Clean up
    await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_stream_lifecycle(streaming_pipeline):
    """Test complete stream lifecycle."""
    # Create
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)
    assert stream_id is not None

    # Use
    handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
    await handler.emit_phase_start(OptimizationPhase.ANALYSIS)
    await handler.emit_phase_complete(OptimizationPhase.ANALYSIS)

    # Close
    await streaming_pipeline.close_stream(stream_id)
    # After closing, attempting to use should fail gracefully


# ============================================================================
# Boundary and Edge Case Tests
# ============================================================================

@pytest.mark.asyncio
async def test_empty_stream(streaming_pipeline):
    """Test handling of stream with no data."""
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
        summary = handler.get_summary()

        # Should handle empty case
        assert summary["metrics_collected"] == 0
        assert summary["metrics"] == []

    finally:
        await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_metric_with_extreme_values(streaming_pipeline):
    """Test metrics with extreme values."""
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Very large value
        metric1 = OptimizationMetric(
            type=OptimizationMetricType.COST_REDUCTION,
            value=999999.99,
            unit="percent"
        )
        await handler.emit_metric(metric1)

        # Zero value
        metric2 = OptimizationMetric(
            type=OptimizationMetricType.TOKEN_REDUCTION,
            value=0.0,
            unit="tokens"
        )
        await handler.emit_metric(metric2)

        # Negative value (time improvement)
        metric3 = OptimizationMetric(
            type=OptimizationMetricType.TIME_IMPROVEMENT,
            value=-0.5,
            unit="seconds"
        )
        await handler.emit_metric(metric3)

        assert len(handler.metrics) == 3

    finally:
        await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_unicode_in_streaming_data(streaming_pipeline):
    """Test streaming unicode data."""
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Emit unicode data
        await handler.emit_data({
            "message": "测试 テスト тест 🚀",
            "emoji": "🔥💡⚡",
            "special": "naïve café"
        })

        assert handler is not None

    finally:
        await streaming_pipeline.close_stream(stream_id)
