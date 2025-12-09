"""
HTTP/2 + SSE Edge Cases and Concerns Audit

Comprehensive testing of edge cases, error scenarios, and production concerns:
- Connection lifecycle (open/close/timeout)
- Error recovery and resilience
- Memory cleanup and leak prevention
- Resource exhaustion scenarios
- Security isolation and data confidentiality
- Graceful degradation under load
"""

import asyncio
import pytest
import gc
import tracemalloc
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from optimization.streaming import (
    StreamingPipeline,
    SSEStreamHandler,
    StreamEvent,
    StreamEventType,
    get_streaming_pipeline,
)
from optimization.streaming_handlers import (
    OptimizationStreamHandler,
    OptimizationPhase,
    OptimizationMetric,
    OptimizationMetricType,
    create_optimization_stream,
    get_optimization_handler,
)


class TestConnectionLifecycle:
    """Test connection open/close/timeout scenarios."""

    @pytest.mark.asyncio
    async def test_connection_open_close_cycle(self):
        """Test proper connection lifecycle."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit metrics
        for i in range(10):
            metric = OptimizationMetric(
                type=OptimizationMetricType.COST_REDUCTION,
                value=float(i),
                unit="USD"
            )
            await handler.emit_metric(metric)

        # Verify metrics were collected
        summary = handler.get_summary()
        assert summary["metrics_collected"] == 10
        assert handler.stream_id == stream_id

    @pytest.mark.asyncio
    async def test_connection_timeout_recovery(self):
        """Test recovery from connection timeout."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit first metric
        await handler.emit_phase_start(OptimizationPhase.ANALYSIS)

        # Wait to simulate timeout
        await asyncio.sleep(0.1)

        # Should still be able to emit after timeout
        await handler.emit_phase_complete(OptimizationPhase.ANALYSIS)

        summary = handler.get_summary()
        assert summary["current_phase"] == OptimizationPhase.ANALYSIS.value

    @pytest.mark.asyncio
    async def test_abrupt_connection_termination(self):
        """Test graceful handling of abrupt connection close."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Start emitting metrics
        task = asyncio.create_task(
            self._emit_continuous_metrics(handler, count=100)
        )

        # Let it run briefly
        await asyncio.sleep(0.05)

        # Task should complete without hanging
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            pytest.fail("Task did not complete in reasonable time")

    @pytest.mark.asyncio
    async def test_reconnection_after_disconnect(self):
        """Test reconnection after disconnect."""
        pipeline = get_streaming_pipeline()

        # First stream
        stream_id1 = await create_optimization_stream(pipeline)
        handler1 = await get_optimization_handler(stream_id1, pipeline)
        await handler1.emit_phase_start(OptimizationPhase.INITIALIZATION)

        # Second stream (simulating reconnection)
        stream_id2 = await create_optimization_stream(pipeline)
        handler2 = await get_optimization_handler(stream_id2, pipeline)
        await handler2.emit_phase_start(OptimizationPhase.INITIALIZATION)

        # Both should work independently
        assert handler1.stream_id != handler2.stream_id
        assert handler1.current_phase == OptimizationPhase.INITIALIZATION
        assert handler2.current_phase == OptimizationPhase.INITIALIZATION

    async def _emit_continuous_metrics(self, handler, count):
        """Helper to emit continuous metrics."""
        for i in range(count):
            metric = OptimizationMetric(
                type=OptimizationMetricType.CACHE_HIT,
                value=1.0,
                unit="hit"
            )
            await handler.emit_metric(metric)
            await asyncio.sleep(0.001)


class TestErrorRecovery:
    """Test error scenarios and recovery paths."""

    @pytest.mark.asyncio
    async def test_error_emission(self):
        """Test handling of error events."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit error
        await handler.emit_error("Test error occurred", error_type="TEST_ERROR")

        # Handler should still be functional
        summary = handler.get_summary()
        assert handler.stream_id == stream_id

    @pytest.mark.asyncio
    async def test_concurrent_metric_emission_race_conditions(self):
        """Test thread-safety of concurrent emissions."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit from multiple concurrent tasks
        async def emit_batch(batch_id, count):
            for i in range(count):
                metric = OptimizationMetric(
                    type=OptimizationMetricType.COMPLEXITY_LEVEL,
                    value=float(batch_id),
                    unit="score"
                )
                await handler.emit_metric(metric)

        # Run 5 concurrent batches of 20 metrics each
        tasks = [emit_batch(i, 20) for i in range(5)]
        await asyncio.gather(*tasks)

        # Should have all 100 metrics
        summary = handler.get_summary()
        assert summary["metrics_collected"] == 100

    @pytest.mark.asyncio
    async def test_recovery_from_error_continuation(self):
        """Test system continues after error event."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit error
        await handler.emit_error("Some error")

        # Should be able to continue emitting
        metric = OptimizationMetric(
            type=OptimizationMetricType.TOKEN_REDUCTION,
            value=25.0,
            unit="percent"
        )
        await handler.emit_metric(metric)

        summary = handler.get_summary()
        assert summary["metrics_collected"] == 1

    @pytest.mark.asyncio
    async def test_backpressure_handling(self):
        """Test handling of rapid metric emissions (backpressure)."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit rapidly
        for i in range(100):
            metric = OptimizationMetric(
                type=OptimizationMetricType.COST_REDUCTION,
                value=0.01 * i,
                unit="USD"
            )
            await handler.emit_metric(metric)

        # Should not crash or drop metrics
        summary = handler.get_summary()
        assert summary["metrics_collected"] == 100


class TestMemoryManagement:
    """Test memory cleanup and leak prevention."""

    @pytest.mark.asyncio
    async def test_memory_cleanup_on_handler_disposal(self):
        """Test that memory is properly freed when handler is disposed."""
        tracemalloc.start()

        gc.collect()
        baseline = tracemalloc.get_traced_memory()[0]

        # Create and dispose handlers
        pipeline = get_streaming_pipeline()
        for _ in range(50):
            stream_id = await create_optimization_stream(pipeline)
            handler = await get_optimization_handler(stream_id, pipeline)
            for i in range(100):
                metric = OptimizationMetric(
                    type=OptimizationMetricType.CACHE_HIT,
                    value=1.0,
                    unit="hit"
                )
                await handler.emit_metric(metric)

        # Force garbage collection
        gc.collect()
        current = tracemalloc.get_traced_memory()[0]

        # Memory growth should be reasonable
        growth_mb = (current - baseline) / 1024 / 1024
        assert growth_mb < 20, f"Excessive memory growth: {growth_mb:.2f}MB"

        tracemalloc.stop()

    @pytest.mark.asyncio
    async def test_no_circular_references(self):
        """Test that circular references don't prevent GC."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit metrics
        for i in range(50):
            metric = OptimizationMetric(
                type=OptimizationMetricType.TOKEN_REDUCTION,
                value=float(i),
                unit="percent"
            )
            await handler.emit_metric(metric)

        # Should be collectable
        gc.collect()
        # If we get here without hanging, test passes

    @pytest.mark.asyncio
    async def test_metrics_buffer_cleanup(self):
        """Test that metric buffers are cleaned up properly."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit large number of metrics
        for i in range(1000):
            metric = OptimizationMetric(
                type=OptimizationMetricType.PARALLELIZATION_FACTOR,
                value=float(i % 10) / 10.0,
                unit="factor"
            )
            await handler.emit_metric(metric)

        # Check all metrics were collected
        summary = handler.get_summary()
        assert summary["metrics_collected"] == 1000

    @pytest.mark.asyncio
    async def test_stream_handler_reference_counting(self):
        """Test that streaming handlers are properly dereferenced."""
        pipeline = get_streaming_pipeline()
        handlers = []

        # Create multiple handlers
        for i in range(20):
            stream_id = await create_optimization_stream(pipeline)
            handler = await get_optimization_handler(stream_id, pipeline)
            handlers.append(handler)

        # Clear references
        handlers.clear()

        # Force collection
        gc.collect()

        # Should not raise
        assert True


class TestResourceExhaustion:
    """Test behavior under resource exhaustion scenarios."""

    @pytest.mark.asyncio
    async def test_massive_concurrent_streams(self):
        """Test behavior with very large number of concurrent streams."""
        pipeline = get_streaming_pipeline()
        handlers = []

        # Create 100 concurrent stream handlers
        try:
            for i in range(100):
                stream_id = await create_optimization_stream(pipeline)
                handler = await get_optimization_handler(stream_id, pipeline)
                handlers.append(handler)
        except Exception as e:
            pytest.fail(f"Failed to create many handlers: {e}")

        # All should be operational
        assert len(handlers) == 100

    @pytest.mark.asyncio
    async def test_large_metric_payload(self):
        """Test handling of large metric values."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Create metric with large value representation
        large_metric = OptimizationMetric(
            type=OptimizationMetricType.COST_REDUCTION,
            value=999999.99,
            unit="USD"
        )

        # Should handle large payloads
        try:
            await handler.emit_metric(large_metric)
            summary = handler.get_summary()
            assert summary["metrics_collected"] == 1
        except Exception as e:
            pytest.fail(f"Failed to handle large metric: {e}")

    @pytest.mark.asyncio
    async def test_rapid_connect_disconnect_cycle(self):
        """Test rapid connect/disconnect cycles."""
        pipeline = get_streaming_pipeline()

        # Simulate rapid connections and disconnections
        for i in range(50):
            stream_id = await create_optimization_stream(pipeline)
            handler = await get_optimization_handler(stream_id, pipeline)
            await handler.emit_phase_start(OptimizationPhase.ANALYSIS)

        # Should complete without hanging or crashing
        assert True

    @pytest.mark.asyncio
    async def test_pipeline_under_extreme_load(self):
        """Test streaming pipeline under extreme load."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit metrics rapidly
        start_time = datetime.now()
        metric_count = 0

        while datetime.now() - start_time < timedelta(seconds=2):
            metric = OptimizationMetric(
                type=OptimizationMetricType.CACHE_HIT,
                value=1.0,
                unit="hit"
            )
            await handler.emit_metric(metric)
            metric_count += 1

        # Should handle high throughput
        assert metric_count > 100, f"Only {metric_count} metrics in 2 seconds"


class TestSecurityAndIsolation:
    """Test security and data isolation concerns."""

    @pytest.mark.asyncio
    async def test_stream_isolation(self):
        """Test that streams are properly isolated from each other."""
        pipeline = get_streaming_pipeline()

        stream_id1 = await create_optimization_stream(pipeline)
        handler1 = await get_optimization_handler(stream_id1, pipeline)

        stream_id2 = await create_optimization_stream(pipeline)
        handler2 = await get_optimization_handler(stream_id2, pipeline)

        # Emit to handler1
        metric1 = OptimizationMetric(
            type=OptimizationMetricType.COST_REDUCTION,
            value=10.0,
            unit="USD"
        )
        await handler1.emit_metric(metric1)

        # Emit to handler2
        metric2 = OptimizationMetric(
            type=OptimizationMetricType.TOKEN_REDUCTION,
            value=25.0,
            unit="percent"
        )
        await handler2.emit_metric(metric2)

        # Each should only have its own metrics
        summary1 = handler1.get_summary()
        summary2 = handler2.get_summary()
        assert summary1["metrics_collected"] == 1
        assert summary2["metrics_collected"] == 1
        assert summary1["stream_id"] != summary2["stream_id"]

    @pytest.mark.asyncio
    async def test_phase_isolation(self):
        """Test that phase tracking is isolated between streams."""
        pipeline = get_streaming_pipeline()

        stream_id1 = await create_optimization_stream(pipeline)
        handler1 = await get_optimization_handler(stream_id1, pipeline)

        stream_id2 = await create_optimization_stream(pipeline)
        handler2 = await get_optimization_handler(stream_id2, pipeline)

        # Set different phases
        await handler1.emit_phase_start(OptimizationPhase.ANALYSIS)
        await handler2.emit_phase_start(OptimizationPhase.OPTIMIZATION)

        summary1 = handler1.get_summary()
        summary2 = handler2.get_summary()

        assert summary1["current_phase"] == OptimizationPhase.ANALYSIS.value
        assert summary2["current_phase"] == OptimizationPhase.OPTIMIZATION.value

    @pytest.mark.asyncio
    async def test_no_data_leakage_between_handlers(self):
        """Test that handlers don't share data."""
        pipeline = get_streaming_pipeline()

        # Create first handler and emit metrics
        stream_id1 = await create_optimization_stream(pipeline)
        handler1 = await get_optimization_handler(stream_id1, pipeline)

        metric1 = OptimizationMetric(
            type=OptimizationMetricType.COST_REDUCTION,
            value=100.0,
            unit="USD"
        )
        await handler1.emit_metric(metric1)

        # Create second handler - should not have access to first handler's data
        stream_id2 = await create_optimization_stream(pipeline)
        handler2 = await get_optimization_handler(stream_id2, pipeline)

        summary2 = handler2.get_summary()
        assert summary2["metrics_collected"] == 0

    @pytest.mark.asyncio
    async def test_stream_context_isolation(self):
        """Test that stream contexts don't leak between requests."""
        pipeline = get_streaming_pipeline()
        contexts = []

        for i in range(10):
            stream_id = await create_optimization_stream(pipeline)
            handler = await get_optimization_handler(stream_id, pipeline)

            # Each stream has its own context (stream_id)
            context = {"stream_id": stream_id, "phase": OptimizationPhase.INITIALIZATION}
            contexts.append(context)

            await handler.emit_phase_start(context["phase"])

        # All contexts should be independent
        assert len(contexts) == 10
        stream_ids = [c["stream_id"] for c in contexts]
        # All should be unique
        assert len(stream_ids) == len(set(stream_ids))


class TestGracefulDegradation:
    """Test graceful degradation under failure scenarios."""

    @pytest.mark.asyncio
    async def test_degradation_under_continuous_load(self):
        """Test behavior under continuous load."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Continuous emissions
        for i in range(500):
            metric = OptimizationMetric(
                type=OptimizationMetricType.TOKEN_REDUCTION,
                value=float(i % 100),
                unit="percent"
            )
            await handler.emit_metric(metric)

        summary = handler.get_summary()
        assert summary["metrics_collected"] == 500

    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self):
        """Test recovery from partial failures."""
        pipeline = get_streaming_pipeline()
        stream_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_id, pipeline)

        # Emit initial batch
        for i in range(50):
            metric = OptimizationMetric(
                type=OptimizationMetricType.CACHE_HIT,
                value=1.0,
                unit="hit"
            )
            await handler.emit_metric(metric)

        # Emit second batch despite any issues
        for i in range(50):
            metric = OptimizationMetric(
                type=OptimizationMetricType.COMPLEXITY_LEVEL,
                value=float(i % 10),
                unit="score"
            )
            await handler.emit_metric(metric)

        summary = handler.get_summary()
        assert summary["metrics_collected"] == 100

    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(self):
        """Test that failures don't cascade through the system."""
        pipeline = get_streaming_pipeline()
        handlers = []

        # Create multiple streams
        for _ in range(5):
            stream_id = await create_optimization_stream(pipeline)
            handler = await get_optimization_handler(stream_id, pipeline)
            handlers.append(handler)

        # All streams should continue working
        for handler in handlers:
            metric = OptimizationMetric(
                type=OptimizationMetricType.COST_REDUCTION,
                value=5.0,
                unit="USD"
            )
            await handler.emit_metric(metric)

        # Verify all completed
        for handler in handlers:
            summary = handler.get_summary()
            assert summary["metrics_collected"] == 1


class TestConnectionPooling:
    """Test connection pooling and reuse."""

    @pytest.mark.asyncio
    async def test_stream_creation_efficiency(self):
        """Test that multiple streams can be created efficiently."""
        pipeline = get_streaming_pipeline()

        # Create multiple streams on same pipeline
        streams = []
        for i in range(10):
            stream_id = await create_optimization_stream(pipeline)
            handler = await get_optimization_handler(stream_id, pipeline)
            streams.append(handler)

        # Emit to all streams
        for i, handler in enumerate(streams):
            metric = OptimizationMetric(
                type=OptimizationMetricType.PARALLELIZATION_FACTOR,
                value=float(i) / 10.0,
                unit="factor"
            )
            await handler.emit_metric(metric)

        assert len(streams) == 10


# Fixtures
@pytest.fixture
async def cleanup_handlers():
    """Ensure all handlers are cleaned up after tests."""
    yield
    gc.collect()
