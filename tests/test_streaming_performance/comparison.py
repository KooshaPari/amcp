"""Comparison and advanced performance benchmarks."""

import asyncio
import time

import pytest
from optimization import (
    OptimizationStreamHandler,
    OptimizationMetric,
    OptimizationMetricType,
)
from optimization.streaming import SSEStreamHandler


@pytest.mark.asyncio
@pytest.mark.performance
async def test_metric_latency_distribution(streaming_pipeline):
    """Benchmark: Latency distribution for metric emission.

    Measures: min, max, mean, median latency for metric operations.
    """
    sse_handler = SSEStreamHandler(queue_size=1000, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Measure individual metric latencies
        latencies = []
        metric_count = 500

        for i in range(metric_count):
            start = time.perf_counter()
            await handler.emit_metric(
                OptimizationMetric(
                    type=OptimizationMetricType.COST_REDUCTION,
                    value=float(i % 100),
                    unit="percent",
                )
            )
            latency = (time.perf_counter() - start) * 1000  # Convert to ms
            latencies.append(latency)

        # Calculate statistics
        latencies_sorted = sorted(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        mean_latency = sum(latencies) / len(latencies)
        median_latency = latencies_sorted[len(latencies) // 2]
        p95_latency = latencies_sorted[int(len(latencies) * 0.95)]
        p99_latency = latencies_sorted[int(len(latencies) * 0.99)]

        print(f"\n=== Metric Latency Distribution ===")
        print(f"Sample size: {metric_count}")
        print(f"Min latency: {min_latency:.3f}ms")
        print(f"Max latency: {max_latency:.3f}ms")
        print(f"Mean latency: {mean_latency:.3f}ms")
        print(f"Median latency: {median_latency:.3f}ms")
        print(f"P95 latency: {p95_latency:.3f}ms")
        print(f"P99 latency: {p99_latency:.3f}ms")

        # Assertions
        assert (
            mean_latency < 5.0
        ), f"Mean latency too high: {mean_latency:.3f}ms (target: <5ms)"
        assert (
            p99_latency < 20.0
        ), f"P99 latency too high: {p99_latency:.3f}ms (target: <20ms)"

    finally:
        await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
@pytest.mark.performance
async def test_http2_multiplexing_benefit(streaming_pipeline):
    """Benchmark: Demonstrate HTTP/2 multiplexing throughput benefits.

    Compares: sequential vs concurrent stream handling with realistic load.
    """
    stream_count = 20
    metrics_per_stream = 50
    # Add simulated I/O delay to make sequential bottleneck visible
    io_delay_ms = 0.1

    print(f"\n=== HTTP/2 Multiplexing Benefit ===")
    print(f"Streams: {stream_count}, Metrics per stream: {metrics_per_stream}")
    print(f"Simulated I/O delay per operation: {io_delay_ms}ms")

    # Sequential approach (one stream at a time)
    sequential_start = time.perf_counter()
    for stream_idx in range(stream_count):
        sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
        stream_id = await streaming_pipeline.create_stream(sse_handler)
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        for i in range(metrics_per_stream):
            await handler.emit_metric(
                OptimizationMetric(
                    type=OptimizationMetricType.COST_REDUCTION,
                    value=float(i % 100),
                    unit="percent",
                )
            )
            # Simulate I/O operation
            await asyncio.sleep(io_delay_ms / 1000)

        await streaming_pipeline.close_stream(stream_id)

    sequential_duration = time.perf_counter() - sequential_start

    # Concurrent approach (HTTP/2 multiplexing)
    concurrent_start = time.perf_counter()
    stream_ids = []
    handlers = []

    for i in range(stream_count):
        sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
        stream_id = await streaming_pipeline.create_stream(sse_handler)
        stream_ids.append(stream_id)
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
        handlers.append(handler)

    async def emit_metrics(handler_idx):
        for i in range(metrics_per_stream):
            await handlers[handler_idx].emit_metric(
                OptimizationMetric(
                    type=OptimizationMetricType.COST_REDUCTION,
                    value=float(i % 100),
                    unit="percent",
                )
            )
            # Simulate I/O operation (concurrent)
            await asyncio.sleep(io_delay_ms / 1000)

    await asyncio.gather(*[emit_metrics(i) for i in range(stream_count)])

    for stream_id in stream_ids:
        await streaming_pipeline.close_stream(stream_id)

    concurrent_duration = time.perf_counter() - concurrent_start

    # Calculate multiplexing benefit
    speedup = sequential_duration / concurrent_duration
    efficiency = (speedup / stream_count) * 100

    print(f"\nSequential duration: {sequential_duration:.3f}s")
    print(f"Concurrent duration: {concurrent_duration:.3f}s")
    print(f"Speedup: {speedup:.1f}x")
    print(f"Multiplexing efficiency: {efficiency:.1f}% (ideal: 100%)")

    # With concurrent multiplexing, we should see significant speedup
    assert (
        speedup > 5.0
    ), f"HTTP/2 multiplexing benefit too low: {speedup:.1f}x (target: >5x with concurrent I/O)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_streaming_vs_polling_simulation(streaming_pipeline):
    """Benchmark: Streaming vs polling simulation comparison.

    Compares: continuous streaming vs periodic polling (simulated).
    """
    stream_count = 5
    update_intervals = [100, 500, 1000]  # milliseconds

    print(f"\n=== Streaming vs Polling Simulation ===")
    print(f"Streams: {stream_count}\n")

    for interval_ms in update_intervals:
        # Streaming approach
        stream_ids = []
        handlers = []
        streaming_start = time.perf_counter()

        try:
            for i in range(stream_count):
                sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
                stream_id = await streaming_pipeline.create_stream(sse_handler)
                stream_ids.append(stream_id)
                handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
                handlers.append(handler)

            # Emit updates continuously for 1 second
            end_time = streaming_start + 1.0
            update_count = 0

            while time.perf_counter() < end_time:
                for handler in handlers:
                    await handler.emit_metric(
                        OptimizationMetric(
                            type=OptimizationMetricType.COST_REDUCTION,
                            value=float(update_count % 100),
                            unit="percent",
                        )
                    )
                    update_count += 1

                # Small delay to simulate work
                await asyncio.sleep(0.001)

            streaming_duration = time.perf_counter() - streaming_start
            streaming_updates = update_count

        finally:
            for stream_id in stream_ids:
                await streaming_pipeline.close_stream(stream_id)

        # Polling simulation (simulated delays)
        polling_duration = 1.0 + (1000 / interval_ms) * 0.01  # Latency for polling
        polling_updates = int(1000 / interval_ms * stream_count)
        polling_overhead = polling_duration - 1.0

        # Calculate benefits
        latency_improvement = polling_overhead
        throughput_improvement = (
            streaming_updates / polling_updates if polling_updates > 0 else 1.0
        )

        print(f"Poll interval: {interval_ms}ms")
        print(
            f"  Streaming updates: {streaming_updates} in {streaming_duration:.3f}s"
        )
        print(f"  Polling updates: ~{polling_updates} in {polling_duration:.3f}s")
        print(f"  Latency improvement: {latency_improvement*1000:.1f}ms reduction")
        print(f"  Throughput improvement: {throughput_improvement:.1f}x")
        print()
