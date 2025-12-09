"""Concurrent operations performance benchmarks."""

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
async def test_concurrent_phase_transitions(streaming_pipeline):
    """Benchmark: Concurrent phase transitions across multiple streams.

    Measures: latency of managing phase state across concurrent operations.
    """
    stream_count = 20
    stream_ids = []
    handlers = []

    try:
        # Create streams
        for i in range(stream_count):
            sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
            stream_id = await streaming_pipeline.create_stream(sse_handler)
            stream_ids.append(stream_id)
            handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
            handlers.append(handler)

        # Measure concurrent phase transitions
        start_time = time.perf_counter()

        async def phase_sequence(handler):
            await handler.emit_phase_start(OptimizationPhase.INITIALIZATION)
            await handler.emit_phase_complete(OptimizationPhase.INITIALIZATION)
            await handler.emit_phase_start(OptimizationPhase.ANALYSIS)
            await handler.emit_phase_complete(OptimizationPhase.ANALYSIS)
            await handler.emit_phase_start(OptimizationPhase.OPTIMIZATION)
            await handler.emit_phase_complete(OptimizationPhase.OPTIMIZATION)

        await asyncio.gather(*[phase_sequence(handler) for handler in handlers])

        duration = time.perf_counter() - start_time
        phase_transitions = stream_count * 6  # 6 transitions per stream
        transitions_per_sec = phase_transitions / duration

        assert (
            duration < 2.0
        ), f"Phase transitions too slow: {duration:.2f}s"

        print(f"\n=== Concurrent Phase Transitions ===")
        print(f"Streams: {stream_count}")
        print(f"Phase transitions per stream: 6")
        print(f"Total transitions: {phase_transitions}")
        print(f"Duration: {duration:.3f}s")
        print(f"Transitions per second: {transitions_per_sec:.1f}")

    finally:
        for stream_id in stream_ids:
            await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_mixed_operations(streaming_pipeline):
    """Benchmark: Concurrent mixed operations (metrics, progress, data, completion).

    Measures: throughput with realistic mixed operation patterns.
    """
    stream_count = 15
    operations_per_stream = 100
    stream_ids = []
    handlers = []

    try:
        # Create streams
        for i in range(stream_count):
            sse_handler = SSEStreamHandler(queue_size=200, heartbeat_interval=30.0)
            stream_id = await streaming_pipeline.create_stream(sse_handler)
            stream_ids.append(stream_id)
            handler = OptimizationStreamHandler(stream_id, streaming_pipeline)
            handlers.append(handler)

        # Measure mixed operations
        start_time = time.perf_counter()

        async def mixed_operations(handler, idx):
            for i in range(operations_per_stream):
                op_type = i % 4

                if op_type == 0:
                    # Emit metric
                    await handler.emit_metric(
                        OptimizationMetric(
                            type=OptimizationMetricType.COST_REDUCTION,
                            value=float(i % 100),
                            unit="percent",
                        )
                    )
                elif op_type == 1:
                    # Emit progress
                    await handler.emit_progress(i, operations_per_stream)
                elif op_type == 2:
                    # Emit data
                    await handler.emit_data({"data": f"chunk_{i}", "index": i})
                else:
                    # Emit error (less frequent)
                    if i % 10 == 0:
                        await handler.emit_error(f"Test error {i}", "TEST_ERROR")

        await asyncio.gather(
            *[mixed_operations(handler, i) for i, handler in enumerate(handlers)]
        )

        duration = time.perf_counter() - start_time
        total_operations = stream_count * operations_per_stream
        throughput = total_operations / duration

        assert (
            throughput > 2000
        ), f"Mixed operations throughput too low: {throughput:.1f} ops/sec (target: >2000)"

        print(f"\n=== Concurrent Mixed Operations ===")
        print(f"Streams: {stream_count}")
        print(f"Operations per stream: {operations_per_stream}")
        print(f"Total operations: {total_operations}")
        print(f"Duration: {duration:.3f}s")
        print(f"Throughput: {throughput:.1f} operations/sec")
        print(f"Per-stream: {throughput/stream_count:.1f} operations/sec")

    finally:
        for stream_id in stream_ids:
            await streaming_pipeline.close_stream(stream_id)
