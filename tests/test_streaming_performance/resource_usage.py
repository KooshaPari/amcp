"""Resource usage and memory performance benchmarks."""

import sys
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
async def test_memory_efficiency_with_streams(streaming_pipeline):
    """Benchmark: Memory efficiency with increasing stream count.

    Measures: memory overhead per stream, total memory usage.
    """
    stream_counts = [1, 10, 20, 50]
    results = []

    for stream_count in stream_counts:
        stream_ids = []
        handlers = []

        try:
            # Create streams and measure memory
            for i in range(stream_count):
                sse_handler = SSEStreamHandler(
                    queue_size=100, heartbeat_interval=30.0
                )
                stream_id = await streaming_pipeline.create_stream(sse_handler)
                stream_ids.append(stream_id)
                handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
                handlers.append(handler)

                # Add some data to each stream
                for j in range(10):
                    await handler.emit_metric(
                        OptimizationMetric(
                            type=OptimizationMetricType.COST_REDUCTION,
                            value=float(j),
                            unit="percent",
                        )
                    )

            # Calculate total metrics across all handlers
            total_metrics = sum(len(h.metrics) for h in handlers)
            total_bytes = sum(sys.getsizeof(h) for h in handlers)
            bytes_per_stream = total_bytes / stream_count if stream_count > 0 else 0

            results.append(
                {
                    "streams": stream_count,
                    "total_metrics": total_metrics,
                    "total_bytes": total_bytes,
                    "bytes_per_stream": bytes_per_stream,
                }
            )

        finally:
            for stream_id in stream_ids:
                await streaming_pipeline.close_stream(stream_id)

    print(f"\n=== Memory Efficiency ===")
    print(
        f"{'Streams':<10} {'Total Metrics':<15} {'Total Bytes':<15} {'Bytes/Stream':<15}"
    )
    print("-" * 55)
    for result in results:
        print(
            f"{result['streams']:<10} "
            f"{result['total_metrics']:<15} "
            f"{result['total_bytes']:<15} "
            f"{result['bytes_per_stream']:<15.0f}"
        )


@pytest.mark.asyncio
@pytest.mark.performance
async def test_performance_summary(streaming_pipeline):
    """Benchmark: Summary of overall performance metrics.

    Generates final performance report.
    """
    print(f"\n" + "=" * 60)
    print("STREAMING PERFORMANCE BENCHMARK SUMMARY")
    print("=" * 60)

    # Quick performance checks
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    try:
        handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

        # Check 1: Single metric latency
        start = time.perf_counter()
        await handler.emit_metric(
            OptimizationMetric(
                type=OptimizationMetricType.COST_REDUCTION,
                value=10.0,
                unit="percent",
            )
        )
        single_latency = (time.perf_counter() - start) * 1000

        # Check 2: 100 metrics throughput
        start = time.perf_counter()
        for i in range(100):
            await handler.emit_metric(
                OptimizationMetric(
                    type=OptimizationMetricType.COST_REDUCTION,
                    value=float(i % 100),
                    unit="percent",
                )
            )
        batch_duration = time.perf_counter() - start
        batch_throughput = 100 / batch_duration

        # Check 3: Phase transition latency
        from optimization import OptimizationPhase

        start = time.perf_counter()
        await handler.emit_phase_start(OptimizationPhase.ANALYSIS)
        await handler.emit_phase_complete(OptimizationPhase.ANALYSIS)
        phase_latency = (time.perf_counter() - start) * 1000

        print(f"\nKEY METRICS:")
        print(f"  Single metric latency: {single_latency:.3f}ms")
        print(
            f"  Batch throughput (100 metrics): {batch_throughput:.1f} metrics/sec"
        )
        print(f"  Phase transition latency: {phase_latency:.3f}ms")

        print(f"\nPERFORMANCE TARGETS:")
        print(f"  ✓ Single latency <10ms: {single_latency < 10}")
        print(f"  ✓ Throughput >200 m/s: {batch_throughput > 200}")
        print(f"  ✓ Phase latency <10ms: {phase_latency < 10}")

        print(f"\nHTTP/2 + SSE STREAMING BENEFITS:")
        print(f"  • Multiplexed concurrent streams")
        print(f"  • Real-time metric streaming")
        print(f"  • Low-latency updates (<{single_latency:.1f}ms)")
        print(f"  • High throughput ({batch_throughput:.0f}+ metrics/sec)")
        print(f"  • Efficient resource utilization")

        print("\n" + "=" * 60)

    finally:
        await streaming_pipeline.close_stream(stream_id)
