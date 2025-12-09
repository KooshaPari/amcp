"""
Shared fixtures and utilities for production load tests.

This module provides:
- LoadTestMetrics class for collecting and analyzing test metrics
- Shared fixtures for streaming pipeline and handlers
- Common helper functions for load testing
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional

import pytest

from optimization.streaming import get_streaming_pipeline
from optimization.streaming_handlers import (
    create_optimization_stream,
    get_optimization_handler,
    OptimizationMetric,
    OptimizationMetricType,
)


class LoadTestMetrics:
    """Collect and analyze load test metrics."""

    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.total_metrics_emitted = 0
        self.total_metrics_received = 0
        self.errors = 0
        self.latencies: list[float] = []
        self.stream_count = 0

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    @property
    def throughput(self) -> float:
        """Metrics per second."""
        if self.duration > 0:
            return self.total_metrics_emitted / self.duration
        return 0

    @property
    def p99_latency(self) -> float:
        """99th percentile latency in ms."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[idx] * 1000

    @property
    def p95_latency(self) -> float:
        """95th percentile latency in ms."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[idx] * 1000

    @property
    def p50_latency(self) -> float:
        """Median latency in ms."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        idx = len(sorted_latencies) // 2
        return sorted_latencies[idx] * 1000

    @property
    def error_rate(self) -> float:
        """Error rate as percentage."""
        if self.total_metrics_emitted == 0:
            return 0
        return (self.errors / self.total_metrics_emitted) * 100

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        return 100 - self.error_rate

    def summary(self) -> str:
        """Generate formatted summary of test results."""
        per_stream_throughput = (
            self.throughput / self.stream_count if self.stream_count > 0 else 0
        )

        return f"""
╔══════════════════════════════════════════════════════════╗
║ PRODUCTION LOAD TEST RESULTS                             ║
╚══════════════════════════════════════════════════════════╝

Test Duration: {self.duration:.2f}s
Concurrent Streams: {self.stream_count}

THROUGHPUT:
  Total Metrics Emitted: {self.total_metrics_emitted:,}
  Throughput: {self.throughput:,.0f} metrics/sec
  Per-Stream: {per_stream_throughput:,.0f} metrics/sec

LATENCY (ms):
  P50: {self.p50_latency:.3f}
  P95: {self.p95_latency:.3f}
  P99: {self.p99_latency:.3f}

RELIABILITY:
  Success Rate: {self.success_rate:.2f}%
  Error Rate: {self.error_rate:.2f}%
  Total Errors: {self.errors}

════════════════════════════════════════════════════════════
"""


@pytest.fixture
def streaming_pipeline():
    """Provide streaming pipeline for tests."""
    return get_streaming_pipeline()


async def emit_metrics_for_stream(
    stream_id: int,
    metrics_count: int,
    metrics: LoadTestMetrics,
    pipeline,
    metric_type: OptimizationMetricType = OptimizationMetricType.COST_REDUCTION,
    delay: float = 0.0,
) -> None:
    """Emit metrics from a single stream.

    Args:
        stream_id: Identifier for this stream
        metrics_count: Number of metrics to emit
        metrics: Metrics collector to update
        pipeline: Streaming pipeline instance
        metric_type: Type of optimization metric to emit
        delay: Optional delay between emissions in seconds
    """
    try:
        stream_handler_id = await create_optimization_stream(pipeline)
        handler = await get_optimization_handler(stream_handler_id, pipeline)

        for i in range(metrics_count):
            try:
                emit_start = time.perf_counter()
                metric = OptimizationMetric(
                    type=metric_type,
                    value=float(i % 100),
                    unit="USD" if metric_type == OptimizationMetricType.COST_REDUCTION else "percent",
                )
                await handler.emit_metric(metric)
                emit_duration = time.perf_counter() - emit_start

                metrics.total_metrics_emitted += 1
                metrics.latencies.append(emit_duration)

                if delay > 0:
                    await asyncio.sleep(delay)
            except Exception:
                metrics.errors += 1
    except Exception:
        metrics.errors += metrics_count


async def run_concurrent_load_test(
    stream_count: int,
    metrics_per_stream: int,
    pipeline,
    metric_type: OptimizationMetricType = OptimizationMetricType.COST_REDUCTION,
) -> LoadTestMetrics:
    """Run a load test with concurrent streams.

    Args:
        stream_count: Number of concurrent streams to create
        metrics_per_stream: Number of metrics each stream should emit
        pipeline: Streaming pipeline instance
        metric_type: Type of optimization metric to emit

    Returns:
        LoadTestMetrics with test results
    """
    metrics = LoadTestMetrics()
    metrics.stream_count = stream_count
    metrics.start_time = datetime.now()

    tasks = [
        emit_metrics_for_stream(i, metrics_per_stream, metrics, pipeline, metric_type)
        for i in range(stream_count)
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

    metrics.end_time = datetime.now()
    return metrics


async def run_sustained_load_test(
    stream_count: int,
    duration_seconds: int,
    pipeline,
    metric_type: OptimizationMetricType = OptimizationMetricType.CACHE_HIT,
    emission_delay: float = 0.001,
) -> LoadTestMetrics:
    """Run a sustained load test for a specific duration.

    Args:
        stream_count: Number of concurrent streams
        duration_seconds: Test duration in seconds
        pipeline: Streaming pipeline instance
        metric_type: Type of optimization metric to emit
        emission_delay: Delay between metric emissions in seconds

    Returns:
        LoadTestMetrics with test results
    """
    metrics = LoadTestMetrics()
    metrics.stream_count = stream_count
    metrics.start_time = datetime.now()

    async def sustained_stream():
        """Emit metrics continuously for duration."""
        try:
            stream_id = await create_optimization_stream(pipeline)
            handler = await get_optimization_handler(stream_id, pipeline)

            while datetime.now() - metrics.start_time < timedelta(seconds=duration_seconds):
                try:
                    emit_start = time.perf_counter()
                    metric = OptimizationMetric(type=metric_type, value=1.0, unit="hit")
                    await handler.emit_metric(metric)
                    emit_duration = time.perf_counter() - emit_start

                    metrics.total_metrics_emitted += 1
                    metrics.latencies.append(emit_duration)

                    await asyncio.sleep(emission_delay)
                except Exception:
                    metrics.errors += 1
        except Exception:
            pass

    tasks = [sustained_stream() for _ in range(stream_count)]
    await asyncio.gather(*tasks, return_exceptions=True)

    metrics.end_time = datetime.now()
    return metrics
