"""
Load test metrics and bottleneck identification.

Tests:
- Latency degradation analysis
- Throughput vs load curves
- Performance profiling under load
"""

import pytest

from optimization.streaming_handlers import OptimizationMetricType
from .conftest import LoadTestMetrics, run_concurrent_load_test


class TestBottleneckIdentification:
    """Identify system bottlenecks under load."""

    @pytest.mark.asyncio
    async def test_latency_degradation_curve(self, streaming_pipeline):
        """Plot latency degradation with increasing load."""
        print("\n\nLatency vs Load Analysis:\n")
        print("Streams | Throughput (m/s) | P50 (ms) | P99 (ms) | Success %")
        print("─" * 60)

        for stream_count in [10, 50, 100, 150]:
            metrics = await run_concurrent_load_test(
                stream_count=stream_count,
                metrics_per_stream=50,
                pipeline=streaming_pipeline,
            )

            print(
                f"{stream_count:7} | {metrics.throughput:15,.0f} | "
                f"{metrics.p50_latency:8.3f} | {metrics.p99_latency:8.3f} | "
                f"{metrics.success_rate:8.2f}%"
            )

    @pytest.mark.asyncio
    async def test_throughput_scaling(self, streaming_pipeline):
        """Test how throughput scales with concurrent streams."""
        print("\n\nThroughput Scaling Analysis:\n")
        print("Streams | Throughput (m/s) | Per-Stream (m/s) | Efficiency %")
        print("─" * 65)

        baseline_throughput_per_stream = None

        for stream_count in [10, 25, 50, 100, 200]:
            metrics = await run_concurrent_load_test(
                stream_count=stream_count,
                metrics_per_stream=100,
                pipeline=streaming_pipeline,
            )

            per_stream = metrics.throughput / stream_count
            if baseline_throughput_per_stream is None:
                baseline_throughput_per_stream = per_stream
                efficiency = 100.0
            else:
                efficiency = (per_stream / baseline_throughput_per_stream) * 100

            print(
                f"{stream_count:7} | {metrics.throughput:15,.0f} | "
                f"{per_stream:15,.2f} | {efficiency:11.2f}%"
            )

    @pytest.mark.asyncio
    async def test_error_rate_under_load(self, streaming_pipeline):
        """Analyze error rates as load increases."""
        print("\n\nError Rate Analysis:\n")
        print("Streams | Errors | Error Rate % | Success Rate %")
        print("─" * 55)

        for stream_count in [50, 100, 150, 200, 250]:
            metrics = await run_concurrent_load_test(
                stream_count=stream_count,
                metrics_per_stream=50,
                pipeline=streaming_pipeline,
            )

            print(
                f"{stream_count:7} | {metrics.errors:6} | "
                f"{metrics.error_rate:11.2f}% | {metrics.success_rate:13.2f}%"
            )

            # Assert error rate stays below threshold
            assert metrics.error_rate < 15, f"Error rate too high: {metrics.error_rate:.2f}%"


class TestPerformanceMetrics:
    """Detailed performance metric analysis."""

    @pytest.mark.asyncio
    async def test_latency_percentiles(self, streaming_pipeline):
        """Analyze latency distribution across percentiles."""
        metrics = await run_concurrent_load_test(
            stream_count=100,
            metrics_per_stream=100,
            pipeline=streaming_pipeline,
        )

        print("\n\nLatency Distribution:\n")
        print(f"P50 (median): {metrics.p50_latency:.3f} ms")
        print(f"P95:          {metrics.p95_latency:.3f} ms")
        print(f"P99:          {metrics.p99_latency:.3f} ms")

        if metrics.latencies:
            sorted_latencies = sorted(metrics.latencies)
            p90_idx = int(len(sorted_latencies) * 0.90)
            p75_idx = int(len(sorted_latencies) * 0.75)
            p25_idx = int(len(sorted_latencies) * 0.25)

            print(f"P90:          {sorted_latencies[p90_idx] * 1000:.3f} ms")
            print(f"P75:          {sorted_latencies[p75_idx] * 1000:.3f} ms")
            print(f"P25:          {sorted_latencies[p25_idx] * 1000:.3f} ms")
            print(f"Min:          {sorted_latencies[0] * 1000:.3f} ms")
            print(f"Max:          {sorted_latencies[-1] * 1000:.3f} ms")

        # Verify reasonable latency distribution
        assert metrics.p99_latency < metrics.p50_latency * 10, "Latency tail too long"

    @pytest.mark.asyncio
    async def test_throughput_consistency(self, streaming_pipeline):
        """Test throughput consistency across multiple runs."""
        print("\n\nThroughput Consistency Analysis:\n")
        print("Run | Throughput (m/s) | Duration (s) | Success %")
        print("─" * 60)

        throughputs = []

        for run_num in range(5):
            metrics = await run_concurrent_load_test(
                stream_count=50,
                metrics_per_stream=100,
                pipeline=streaming_pipeline,
            )

            throughputs.append(metrics.throughput)

            print(
                f"{run_num + 1:3} | {metrics.throughput:15,.0f} | "
                f"{metrics.duration:11.2f} | {metrics.success_rate:8.2f}%"
            )

        # Calculate coefficient of variation
        if throughputs:
            mean_throughput = sum(throughputs) / len(throughputs)
            variance = sum((t - mean_throughput) ** 2 for t in throughputs) / len(throughputs)
            std_dev = variance**0.5
            cv = (std_dev / mean_throughput) * 100 if mean_throughput > 0 else 0

            print(f"\nMean Throughput: {mean_throughput:,.0f} m/s")
            print(f"Std Dev: {std_dev:,.2f}")
            print(f"Coefficient of Variation: {cv:.2f}%")

            # Throughput should be consistent (CV < 20%)
            assert cv < 20, f"Throughput too inconsistent: CV={cv:.2f}%"

    @pytest.mark.asyncio
    async def test_metric_type_performance(self, streaming_pipeline):
        """Compare performance across different metric types."""
        from .conftest import emit_metrics_for_stream

        print("\n\nMetric Type Performance Comparison:\n")
        print("Metric Type              | Throughput (m/s) | P99 (ms) | Success %")
        print("─" * 75)

        metric_types = [
            OptimizationMetricType.COST_REDUCTION,
            OptimizationMetricType.CACHE_HIT,
            OptimizationMetricType.TOKEN_REDUCTION,
            OptimizationMetricType.COMPLEXITY_LEVEL,
            OptimizationMetricType.PARALLELIZATION_FACTOR,
        ]

        for metric_type in metric_types:
            metrics = await run_concurrent_load_test(
                stream_count=50,
                metrics_per_stream=100,
                pipeline=streaming_pipeline,
                metric_type=metric_type,
            )

            metric_name = metric_type.value.replace("_", " ").title()
            print(
                f"{metric_name:24} | {metrics.throughput:15,.0f} | "
                f"{metrics.p99_latency:8.3f} | {metrics.success_rate:8.2f}%"
            )


class TestLoadThresholds:
    """Identify load thresholds and limits."""

    @pytest.mark.asyncio
    async def test_find_max_concurrent_streams(self, streaming_pipeline):
        """Find maximum concurrent streams before degradation."""
        print("\n\nMaximum Concurrent Streams Analysis:\n")
        print("Testing increasing stream counts to find threshold...\n")
        print("Streams | Throughput | P99 Latency | Success % | Status")
        print("─" * 70)

        max_acceptable_streams = 0
        p99_threshold = 150.0  # ms
        success_threshold = 90.0  # %

        for stream_count in [50, 100, 150, 200, 250, 300]:
            metrics = await run_concurrent_load_test(
                stream_count=stream_count,
                metrics_per_stream=50,
                pipeline=streaming_pipeline,
            )

            meets_latency = metrics.p99_latency < p99_threshold
            meets_success = metrics.success_rate >= success_threshold
            status = "OK" if meets_latency and meets_success else "DEGRADED"

            if meets_latency and meets_success:
                max_acceptable_streams = stream_count

            print(
                f"{stream_count:7} | {metrics.throughput:10,.0f} | "
                f"{metrics.p99_latency:11.3f} | {metrics.success_rate:8.2f}% | {status}"
            )

        print(f"\nMax acceptable concurrent streams: {max_acceptable_streams}")
        assert max_acceptable_streams >= 100, "System should handle at least 100 streams"

    @pytest.mark.asyncio
    async def test_sustained_load_degradation(self, streaming_pipeline):
        """Test for performance degradation over sustained load."""
        from datetime import datetime, timedelta
        from .conftest import emit_metrics_for_stream
        import time

        print("\n\nSustained Load Degradation Analysis:\n")
        print("Monitoring performance over 60 seconds...\n")
        print("Time (s) | Throughput | P99 Latency | Errors")
        print("─" * 55)

        overall_metrics = LoadTestMetrics()
        overall_metrics.start_time = datetime.now()
        overall_metrics.stream_count = 50

        # Run for 60 seconds, measure every 10 seconds
        interval_metrics = []

        async def monitored_stream(stream_id: int):
            """Emit metrics and track intervals."""
            try:
                from optimization.streaming import get_streaming_pipeline
                from optimization.streaming_handlers import (
                    create_optimization_stream,
                    get_optimization_handler,
                    OptimizationMetric,
                )

                stream_handler_id = await create_optimization_stream(streaming_pipeline)
                handler = await get_optimization_handler(stream_handler_id, streaming_pipeline)

                while (
                    datetime.now() - overall_metrics.start_time < timedelta(seconds=60)
                ):
                    try:
                        emit_start = time.perf_counter()
                        metric = OptimizationMetric(
                            type=OptimizationMetricType.CACHE_HIT, value=1.0, unit="hit"
                        )
                        await handler.emit_metric(metric)
                        emit_duration = time.perf_counter() - emit_start

                        overall_metrics.total_metrics_emitted += 1
                        overall_metrics.latencies.append(emit_duration)

                        await asyncio.sleep(0.01)
                    except Exception:
                        overall_metrics.errors += 1
            except Exception:
                pass

        import asyncio

        tasks = [monitored_stream(i) for i in range(50)]
        await asyncio.gather(*tasks, return_exceptions=True)

        overall_metrics.end_time = datetime.now()

        print(f"\n60s    | {overall_metrics.throughput:10,.0f} | ")
        print(f"{overall_metrics.p99_latency:11.3f} | {overall_metrics.errors}")

        # Check for significant degradation
        assert overall_metrics.success_rate >= 85, "Performance degraded over time"


# Run tests to see results
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
