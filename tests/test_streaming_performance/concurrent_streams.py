"""Concurrent stream performance benchmarks."""

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
async def test_concurrent_streams_throughput(streaming_pipeline):
    """Benchmark: Concurrent stream handling throughput.

    Measures: total throughput with multiple concurrent streams,
    latency with concurrent load.
    """
    stream_count = 10
    metrics_per_stream = 100

    stream_ids = []
    handlers = []

    try:
        # Create concurrent streams
        start_time = time.perf_counter()

        for i in range(stream_count):
            sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
            stream_id = await streaming_pipeline.create_stream(sse_handler)
            stream_ids.append(stream_id)
            handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
            handlers.append(handler)

        # Emit metrics concurrently
        async def emit_metrics(handler_idx, handler):
            for i in range(metrics_per_stream):
                await handlers[handler_idx].emit_metric(
                    OptimizationMetric(
                        type=OptimizationMetricType.COST_REDUCTION,
                        value=float(i % 100),
                        unit="percent",
                    )
                )

        await asyncio.gather(
            *[emit_metrics(i, handler) for i, handler in enumerate(handlers)]
        )

        duration = time.perf_counter() - start_time
        total_metrics = stream_count * metrics_per_stream
        throughput = total_metrics / duration

        # Verify metrics
        for handler in handlers:
            assert len(handler.metrics) == metrics_per_stream

        assert (
            throughput > 1000
        ), f"Concurrent throughput too low: {throughput:.1f} metrics/sec (target: >1000)"

        print(f"\n=== Concurrent Streams Throughput ===")
        print(f"Concurrent streams: {stream_count}")
        print(f"Metrics per stream: {metrics_per_stream}")
        print(f"Total metrics: {total_metrics}")
        print(f"Duration: {duration:.3f}s")
        print(f"Throughput: {throughput:.1f} metrics/sec")
        print(f"Per-stream throughput: {throughput/stream_count:.1f} metrics/sec")

    finally:
        for stream_id in stream_ids:
            await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
@pytest.mark.performance
async def test_stream_scalability(streaming_pipeline):
    """Benchmark: Stream scalability as concurrent count increases.

    Measures: how throughput degrades with increasing stream count.
    Tests scalability from 1 to 50 concurrent streams.
    """
    stream_counts = [1, 5, 10, 20, 50]
    metrics_per_stream = 50
    results = []

    for stream_count in stream_counts:
        stream_ids = []
        handlers = []

        try:
            # Create streams
            for i in range(stream_count):
                sse_handler = SSEStreamHandler(
                    queue_size=100, heartbeat_interval=30.0
                )
                stream_id = await streaming_pipeline.create_stream(sse_handler)
                stream_ids.append(stream_id)
                handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
                handlers.append(handler)

            # Measure throughput
            start_time = time.perf_counter()

            async def emit_metrics(handler_idx):
                for i in range(metrics_per_stream):
                    await handlers[handler_idx].emit_metric(
                        OptimizationMetric(
                            type=OptimizationMetricType.COST_REDUCTION,
                            value=float(i % 100),
                            unit="percent",
                        )
                    )

            await asyncio.gather(
                *[emit_metrics(i) for i in range(stream_count)]
            )

            duration = time.perf_counter() - start_time
            total_metrics = stream_count * metrics_per_stream
            throughput = total_metrics / duration

            results.append(
                {
                    "streams": stream_count,
                    "duration": duration,
                    "throughput": throughput,
                    "per_stream": throughput / stream_count,
                }
            )

        finally:
            for stream_id in stream_ids:
                await streaming_pipeline.close_stream(stream_id)

    print(f"\n=== Stream Scalability ===")
    print(
        f"{'Streams':<10} {'Duration(s)':<12} {'Total(m/s)':<15} {'Per-Stream(m/s)':<15}"
    )
    print("-" * 52)
    for result in results:
        print(
            f"{result['streams']:<10} "
            f"{result['duration']:<12.3f} "
            f"{result['throughput']:<15.1f} "
            f"{result['per_stream']:<15.1f}"
        )

    # Verify scalability - throughput should remain reasonable
    final_throughput = results[-1]["throughput"]
    initial_throughput = results[0]["throughput"]
    degradation = (1 - final_throughput / initial_throughput) * 100

    assert (
        degradation < 50
    ), f"Throughput degradation too high: {degradation:.1f}% (target: <50%)"
    print(f"\nThroughput degradation (1→50 streams): {degradation:.1f}%")
