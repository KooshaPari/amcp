"""Single stream performance benchmarks."""

import asyncio
import time

import pytest
from optimization import (
    OptimizationStreamHandler,
    OptimizationPhase,
    OptimizationMetric,
    OptimizationMetricType,
)
from optimization.streaming import SSEStreamHandler


@pytest.mark.asyncio
@pytest.mark.performance
async def test_single_stream_throughput(streaming_pipeline):
    """Benchmark: Single stream metric emission throughput.

    Measures: metrics per second, total duration, metric latency.
    """
    sse_handler = SSEStreamHandler(queue_size=1000, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Emit 1000 metrics and measure throughput
        metric_count = 1000
        start_time = time.perf_counter()

        for i in range(metric_count):
            metric = OptimizationMetric(
                type=OptimizationMetricType.COST_REDUCTION,
                value=float(i % 100),
                unit="percent",
            )
            await handler.emit_metric(metric)

        duration = time.perf_counter() - start_time
        throughput = metric_count / duration
        avg_latency_ms = (duration / metric_count) * 1000

        # Assertions - metrics should be fast
        assert len(handler.metrics) == metric_count
        assert (
            duration < 5.0
        ), f"Single stream throughput too slow: {duration:.2f}s for {metric_count} metrics"
        assert (
            throughput > 200
        ), f"Throughput too low: {throughput:.1f} metrics/sec (target: >200)"

        # Performance benchmark data
        print(f"\n=== Single Stream Throughput ===")
        print(f"Metrics emitted: {metric_count}")
        print(f"Total duration: {duration:.3f}s")
        print(f"Throughput: {throughput:.1f} metrics/sec")
        print(f"Average latency: {avg_latency_ms:.2f}ms per metric")

    finally:
        await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
@pytest.mark.performance
async def test_large_metric_payload_throughput(streaming_pipeline):
    """Benchmark: Throughput with large metric payloads.

    Measures: payload size impact on throughput, total data transferred.
    """
    sse_handler = SSEStreamHandler(queue_size=1000, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Emit metrics with large data payloads
        metric_count = 100
        payload_size_kb = 10  # 10 KB per metric

        start_time = time.perf_counter()

        for i in range(metric_count):
            large_payload = {
                "data": "x" * (payload_size_kb * 1024),
                "index": i,
                "nested": {"level1": {"level2": {"level3": f"value_{i}"}}},
            }
            await handler.emit_data(large_payload)

        duration = time.perf_counter() - start_time
        total_data_mb = (metric_count * payload_size_kb) / 1024
        throughput_mbps = total_data_mb / duration

        assert (
            duration < 3.0
        ), f"Large payload throughput too slow: {duration:.2f}s"
        assert (
            throughput_mbps > 10
        ), f"Throughput too low: {throughput_mbps:.1f} MB/s (target: >10)"

        print(f"\n=== Large Payload Throughput ===")
        print(f"Payloads emitted: {metric_count}")
        print(f"Payload size: {payload_size_kb} KB each")
        print(f"Total data: {total_data_mb:.1f} MB")
        print(f"Duration: {duration:.3f}s")
        print(f"Throughput: {throughput_mbps:.2f} MB/s")

    finally:
        await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
@pytest.mark.performance
async def test_full_optimization_pipeline_duration(streaming_pipeline):
    """Benchmark: Complete optimization pipeline latency.

    Measures: end-to-end duration of full optimization workflow.
    """
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        start_time = time.perf_counter()

        # Full pipeline execution
        await handler.emit_phase_start(OptimizationPhase.INITIALIZATION)
        await asyncio.sleep(0.01)
        await handler.emit_phase_complete(OptimizationPhase.INITIALIZATION)

        await handler.emit_phase_start(OptimizationPhase.ANALYSIS)
        for i in range(10):
            await handler.emit_metric(
                OptimizationMetric(
                    type=OptimizationMetricType.COST_REDUCTION,
                    value=float(i),
                    unit="percent",
                )
            )
        await handler.emit_phase_complete(OptimizationPhase.ANALYSIS)

        await handler.emit_phase_start(OptimizationPhase.OPTIMIZATION)
        for i in range(10):
            await handler.emit_progress(i, 10, {"stage": "optimizing"})
        await handler.emit_phase_complete(OptimizationPhase.OPTIMIZATION)

        await handler.emit_phase_start(OptimizationPhase.COMPLETION)
        await handler.emit_completion(True, {"success": True})

        duration = time.perf_counter() - start_time

        assert (
            duration < 1.0
        ), f"Pipeline too slow: {duration:.2f}s (target: <1s)"

        print(f"\n=== Full Pipeline Duration ===")
        print(f"Total duration: {duration:.3f}s")
        print(f"Metrics collected: {len(handler.metrics)}")
        print(f"Target: <1.0s, Actual: {duration:.3f}s")

    finally:
        await streaming_pipeline.close_stream(stream_id)
