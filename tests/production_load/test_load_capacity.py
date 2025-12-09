"""
Capacity planning and resource analysis tests.

Tests:
- Resource efficiency metrics
- Capacity recommendations
- Scaling projections
"""

import pytest

from optimization.streaming_handlers import OptimizationMetricType
from .conftest import LoadTestMetrics, run_concurrent_load_test


class TestCapacityPlanning:
    """Capacity planning and resource analysis."""

    @pytest.mark.asyncio
    async def test_resource_efficiency(self, streaming_pipeline):
        """Analyze resource efficiency metrics."""
        print("\n\nResource Efficiency Analysis:\n")

        stream_count = 50
        metrics = await run_concurrent_load_test(
            stream_count=stream_count,
            metrics_per_stream=100,
            pipeline=streaming_pipeline,
            metric_type=OptimizationMetricType.PARALLELIZATION_FACTOR,
        )

        # Calculate per-stream metrics
        metrics_per_stream = metrics.total_metrics_emitted / stream_count
        duration_per_stream = (
            metrics.duration / stream_count if stream_count > 0 else 0
        )
        per_stream_throughput = (
            metrics.throughput / stream_count if stream_count > 0 else 0
        )

        print(f"Streams Tested: {stream_count}")
        print(f"Total Metrics: {metrics.total_metrics_emitted:,}")
        print(f"Per-Stream Metrics: {metrics_per_stream:.0f}")
        print(f"Total Throughput: {metrics.throughput:,.0f} m/s")
        print(f"Per-Stream Throughput: {per_stream_throughput:,.0f} m/s")
        print(f"P99 Latency: {metrics.p99_latency:.3f} ms")
        print(f"Success Rate: {metrics.success_rate:.2f}%")

        # Capacity planning recommendations
        print(f"\n\nCapacity Planning Recommendations:")
        print(f"─" * 50)

        target_throughput = 10000  # 10k m/s
        recommended_servers = max(1, int(target_throughput / metrics.throughput))
        print(f"To achieve {target_throughput:,} m/s: {recommended_servers} servers")

        target_streams = 1000
        streams_per_server = stream_count
        recommended_servers_for_streams = max(
            1, int(target_streams / streams_per_server)
        )
        print(
            f"To support {target_streams} concurrent streams: "
            f"{recommended_servers_for_streams} servers"
        )

        # Assertions
        assert metrics.success_rate >= 90, "Resource efficiency too low"

    @pytest.mark.asyncio
    async def test_scaling_projections(self, streaming_pipeline):
        """Project resource needs for different scales."""
        print("\n\nScaling Projections:\n")
        print(
            "Target Load     | Est. Throughput | Est. Servers | Est. Latency P99"
        )
        print("─" * 75)

        # Baseline measurement
        baseline_streams = 50
        baseline_metrics = await run_concurrent_load_test(
            stream_count=baseline_streams,
            metrics_per_stream=100,
            pipeline=streaming_pipeline,
        )

        # Project for different scales
        target_loads = [100, 500, 1000, 5000, 10000]

        for target in target_loads:
            scale_factor = target / baseline_streams
            estimated_throughput = baseline_metrics.throughput * scale_factor
            estimated_servers = max(1, int(scale_factor))

            # Latency degradation estimate (non-linear)
            latency_growth = 1 + (scale_factor - 1) * 0.3
            estimated_p99 = baseline_metrics.p99_latency * latency_growth

            print(
                f"{target:6} streams | {estimated_throughput:14,.0f} m/s | "
                f"{estimated_servers:12} | {estimated_p99:15.3f} ms"
            )

    @pytest.mark.asyncio
    async def test_cost_efficiency(self, streaming_pipeline):
        """Analyze cost efficiency at different scales."""
        print("\n\nCost Efficiency Analysis:\n")
        print("Streams | Throughput | Per-Stream Cost | Efficiency Score")
        print("─" * 70)

        # Assume base cost per server unit
        base_cost = 100.0  # arbitrary units

        for stream_count in [25, 50, 100, 150, 200]:
            metrics = await run_concurrent_load_test(
                stream_count=stream_count,
                metrics_per_stream=100,
                pipeline=streaming_pipeline,
            )

            # Simple cost model: more streams may need more resources
            estimated_cost = base_cost * (stream_count / 25)
            per_stream_cost = estimated_cost / stream_count
            efficiency_score = (
                metrics.throughput / estimated_cost if estimated_cost > 0 else 0
            )

            print(
                f"{stream_count:7} | {metrics.throughput:10,.0f} | "
                f"{per_stream_cost:14.2f} | {efficiency_score:15.2f}"
            )


class TestResourceUtilization:
    """Test resource utilization patterns."""

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, streaming_pipeline):
        """Test memory usage patterns under load."""
        # Note: This is a placeholder for memory profiling
        # In production, you would use memory_profiler or similar tools

        print("\n\nMemory Efficiency Test:\n")

        metrics = await run_concurrent_load_test(
            stream_count=100,
            metrics_per_stream=100,
            pipeline=streaming_pipeline,
        )

        print(f"Streams: {metrics.stream_count}")
        print(f"Total Metrics: {metrics.total_metrics_emitted:,}")
        print(f"Success Rate: {metrics.success_rate:.2f}%")
        print("\nNote: Enable memory profiling for detailed analysis")

        assert metrics.success_rate >= 90

    @pytest.mark.asyncio
    async def test_concurrent_efficiency(self, streaming_pipeline):
        """Test efficiency of concurrent execution."""
        print("\n\nConcurrent Execution Efficiency:\n")
        print("Comparing sequential vs concurrent execution patterns\n")

        # Small batch test
        small_metrics = await run_concurrent_load_test(
            stream_count=10,
            metrics_per_stream=100,
            pipeline=streaming_pipeline,
        )

        # Large batch test
        large_metrics = await run_concurrent_load_test(
            stream_count=100,
            metrics_per_stream=10,
            pipeline=streaming_pipeline,
        )

        print("Small Batch (10 streams x 100 metrics):")
        print(f"  Throughput: {small_metrics.throughput:,.0f} m/s")
        print(f"  Duration: {small_metrics.duration:.2f}s")
        print(f"  P99 Latency: {small_metrics.p99_latency:.3f} ms")

        print("\nLarge Batch (100 streams x 10 metrics):")
        print(f"  Throughput: {large_metrics.throughput:,.0f} m/s")
        print(f"  Duration: {large_metrics.duration:.2f}s")
        print(f"  P99 Latency: {large_metrics.p99_latency:.3f} ms")

        # Concurrent execution should provide better throughput
        assert large_metrics.throughput > small_metrics.throughput * 0.8


class TestCapacityLimits:
    """Test capacity limits and breaking points."""

    @pytest.mark.asyncio
    async def test_identify_bottleneck(self, streaming_pipeline):
        """Identify the primary bottleneck in the system."""
        print("\n\nBottleneck Identification:\n")
        print("Testing various load patterns to identify constraints\n")

        # Test 1: Many streams, few metrics each
        many_streams = await run_concurrent_load_test(
            stream_count=200,
            metrics_per_stream=10,
            pipeline=streaming_pipeline,
        )

        # Test 2: Few streams, many metrics each
        few_streams = await run_concurrent_load_test(
            stream_count=20,
            metrics_per_stream=100,
            pipeline=streaming_pipeline,
        )

        print("Many Streams (200 x 10):")
        print(f"  Throughput: {many_streams.throughput:,.0f} m/s")
        print(f"  P99 Latency: {many_streams.p99_latency:.3f} ms")
        print(f"  Success Rate: {many_streams.success_rate:.2f}%")

        print("\nFew Streams (20 x 100):")
        print(f"  Throughput: {few_streams.throughput:,.0f} m/s")
        print(f"  P99 Latency: {few_streams.p99_latency:.3f} ms")
        print(f"  Success Rate: {few_streams.success_rate:.2f}%")

        # Analyze which dimension is the bottleneck
        if many_streams.success_rate < few_streams.success_rate - 5:
            print("\nBottleneck: Stream concurrency limit")
        elif few_streams.p99_latency > many_streams.p99_latency * 1.5:
            print("\nBottleneck: Per-stream throughput")
        else:
            print("\nBottleneck: Well-balanced system")

    @pytest.mark.asyncio
    async def test_peak_capacity(self, streaming_pipeline):
        """Determine peak capacity of the system."""
        print("\n\nPeak Capacity Test:\n")
        print("Finding maximum sustainable load...\n")

        best_throughput = 0
        optimal_config = None

        configs = [
            (50, 200),
            (100, 100),
            (150, 67),
            (200, 50),
        ]

        print("Streams | Metrics/Stream | Total Metrics | Throughput | Success %")
        print("─" * 75)

        for streams, metrics_per_stream in configs:
            metrics = await run_concurrent_load_test(
                stream_count=streams,
                metrics_per_stream=metrics_per_stream,
                pipeline=streaming_pipeline,
            )

            total_metrics = streams * metrics_per_stream
            print(
                f"{streams:7} | {metrics_per_stream:14} | {total_metrics:13,} | "
                f"{metrics.throughput:10,.0f} | {metrics.success_rate:8.2f}%"
            )

            if (
                metrics.throughput > best_throughput
                and metrics.success_rate >= 90
            ):
                best_throughput = metrics.throughput
                optimal_config = (streams, metrics_per_stream)

        if optimal_config:
            print(
                f"\nOptimal Configuration: {optimal_config[0]} streams x "
                f"{optimal_config[1]} metrics"
            )
            print(f"Peak Throughput: {best_throughput:,.0f} m/s")


# Run tests to see results
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
