"""
Production load test scenarios for concurrent and sustained streaming.

Tests:
- Concurrent stream loads (100, 200, 300 streams)
- Sustained load over time (30 seconds)
- Ramp-up load patterns
"""

import asyncio
import pytest
from datetime import datetime, timedelta

from optimization.streaming_handlers import OptimizationMetricType
from .conftest import (
    LoadTestMetrics,
    run_concurrent_load_test,
    run_sustained_load_test,
)


class TestConcurrentStreamLoads:
    """Test with increasing concurrent streams."""

    @pytest.mark.asyncio
    async def test_100_concurrent_streams(self, streaming_pipeline):
        """Load test with 100 concurrent streams."""
        metrics = await run_concurrent_load_test(
            stream_count=100,
            metrics_per_stream=100,
            pipeline=streaming_pipeline,
        )

        # Assertions
        assert metrics.throughput > 1000, f"Throughput too low: {metrics.throughput:.0f}"
        assert metrics.p99_latency < 100, f"P99 latency too high: {metrics.p99_latency:.3f}ms"
        assert metrics.success_rate >= 95, f"Success rate too low: {metrics.success_rate:.2f}%"

        print(metrics.summary())

    @pytest.mark.asyncio
    async def test_200_concurrent_streams(self, streaming_pipeline):
        """Load test with 200 concurrent streams."""
        metrics = await run_concurrent_load_test(
            stream_count=200,
            metrics_per_stream=50,
            pipeline=streaming_pipeline,
        )

        assert metrics.throughput > 1000
        assert metrics.p99_latency < 200
        assert metrics.success_rate >= 95

        print(metrics.summary())

    @pytest.mark.asyncio
    async def test_300_concurrent_streams(self, streaming_pipeline):
        """Load test with 300 concurrent streams."""
        metrics = await run_concurrent_load_test(
            stream_count=300,
            metrics_per_stream=30,
            pipeline=streaming_pipeline,
        )

        assert metrics.throughput > 1000
        assert metrics.p99_latency < 300
        assert metrics.success_rate >= 90

        print(metrics.summary())


class TestSustainedLoad:
    """Test sustained load over time."""

    @pytest.mark.asyncio
    async def test_sustained_load_30_seconds(self, streaming_pipeline):
        """Run sustained load for 30 seconds."""
        metrics = await run_sustained_load_test(
            stream_count=50,
            duration_seconds=30,
            pipeline=streaming_pipeline,
            metric_type=OptimizationMetricType.CACHE_HIT,
            emission_delay=0.001,
        )

        assert metrics.duration >= 28  # Allow 2 second variance
        assert metrics.throughput > 100
        assert metrics.success_rate >= 90

        print(metrics.summary())

    @pytest.mark.asyncio
    async def test_ramp_up_load(self, streaming_pipeline):
        """Test gradual ramp-up of load."""
        metrics = LoadTestMetrics()
        metrics.start_time = datetime.now()

        async def ramp_stream(batch_size: int):
            """Create streams in batches."""
            from .conftest import emit_metrics_for_stream

            for batch_num in range(5):  # 5 batches
                streams = []

                # Create batch of streams
                try:
                    batch_metrics = LoadTestMetrics()
                    batch_metrics.start_time = datetime.now()

                    # Create and run batch
                    tasks = [
                        emit_metrics_for_stream(
                            stream_id=i,
                            metrics_count=50,
                            metrics=metrics,
                            pipeline=streaming_pipeline,
                            metric_type=OptimizationMetricType.TOKEN_REDUCTION,
                        )
                        for i in range(batch_size)
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)

                    # Wait between batches
                    await asyncio.sleep(0.5)

                    metrics.stream_count += batch_size
                except Exception:
                    pass

        # Start ramp-up: 5 batches of 20 = 100 streams total
        await ramp_stream(20)

        metrics.end_time = datetime.now()

        assert metrics.throughput > 500
        assert metrics.success_rate >= 90

        print(metrics.summary())


class TestStressScenarios:
    """Stress testing to identify breaking points."""

    @pytest.mark.asyncio
    async def test_burst_load(self, streaming_pipeline):
        """Test burst load scenario with sudden spike."""
        from .conftest import emit_metrics_for_stream

        metrics = LoadTestMetrics()
        metrics.stream_count = 150
        metrics.start_time = datetime.now()

        # Create burst of streams
        tasks = [
            emit_metrics_for_stream(
                stream_id=i,
                metrics_count=200,
                metrics=metrics,
                pipeline=streaming_pipeline,
                metric_type=OptimizationMetricType.COMPLEXITY_LEVEL,
            )
            for i in range(150)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        metrics.end_time = datetime.now()

        # More lenient assertions for stress test
        assert metrics.throughput > 500
        assert metrics.success_rate >= 85

        print(metrics.summary())

    @pytest.mark.asyncio
    async def test_long_duration_streams(self, streaming_pipeline):
        """Test streams that run for extended duration."""
        metrics = await run_sustained_load_test(
            stream_count=20,
            duration_seconds=60,
            pipeline=streaming_pipeline,
            metric_type=OptimizationMetricType.PARALLELIZATION_FACTOR,
            emission_delay=0.01,
        )

        assert metrics.duration >= 58  # Allow variance
        assert metrics.throughput > 50
        assert metrics.success_rate >= 90

        print(metrics.summary())

    @pytest.mark.asyncio
    async def test_mixed_workload(self, streaming_pipeline):
        """Test mixed workload with different metric types."""
        from .conftest import emit_metrics_for_stream

        metrics = LoadTestMetrics()
        metrics.stream_count = 100
        metrics.start_time = datetime.now()

        # Mix different metric types
        metric_types = [
            OptimizationMetricType.COST_REDUCTION,
            OptimizationMetricType.CACHE_HIT,
            OptimizationMetricType.TOKEN_REDUCTION,
            OptimizationMetricType.COMPLEXITY_LEVEL,
            OptimizationMetricType.PARALLELIZATION_FACTOR,
        ]

        tasks = [
            emit_metrics_for_stream(
                stream_id=i,
                metrics_count=100,
                metrics=metrics,
                pipeline=streaming_pipeline,
                metric_type=metric_types[i % len(metric_types)],
            )
            for i in range(100)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        metrics.end_time = datetime.now()

        assert metrics.throughput > 800
        assert metrics.success_rate >= 90

        print(metrics.summary())


# Run tests to see results
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
