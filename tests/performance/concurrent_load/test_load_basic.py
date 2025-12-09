"""Basic concurrent load tests.

Tests system behavior under concurrent load with varying request counts and
concurrency levels.
"""

import time

import pytest

from bifrost_extensions.models import RoutingStrategy


@pytest.mark.asyncio
@pytest.mark.load
class TestConcurrentLoad:
    """Test concurrent request handling."""

    async def test_100_concurrent_requests(
        self,
        gateway_client,
        sample_messages,
        concurrent_executor,
        success_rate_calculator,
        latency_tracker,
        performance_targets,
    ):
        """Test 100 concurrent routing requests.

        Target: 99% success rate
        """

        async def make_request():
            start = time.perf_counter()
            try:
                result = await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )
                latency_ms = (time.perf_counter() - start) * 1000
                latency_tracker.record(latency_ms)
                return result
            except Exception as e:
                return e

        # Execute 100 concurrent requests
        results = await concurrent_executor(make_request, count=100, concurrency=100)

        success_rate = success_rate_calculator(results)
        percentiles = latency_tracker.calculate()

        print(f"\n100 Concurrent Requests:")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  P50 Latency: {percentiles.get('p50', 0):.2f}ms")
        print(f"  P95 Latency: {percentiles.get('p95', 0):.2f}ms")
        print(f"  P99 Latency: {percentiles.get('p99', 0):.2f}ms")

        # Assertions
        assert (
            success_rate >= performance_targets["concurrent_100_success_rate"]
        ), f"Success rate {success_rate:.1%} below target"
        assert (
            percentiles.get("p95", float("inf"))
            < performance_targets["routing_latency_p95_ms"] * 3
        ), f"P95 latency too high under load: {percentiles.get('p95', 0):.2f}ms"

    async def test_1000_concurrent_requests(
        self,
        gateway_client,
        sample_messages,
        concurrent_executor,
        success_rate_calculator,
        latency_tracker,
        performance_targets,
    ):
        """Test 1000 concurrent routing requests.

        Target: 95% success rate
        """

        async def make_request():
            start = time.perf_counter()
            try:
                result = await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )
                latency_ms = (time.perf_counter() - start) * 1000
                latency_tracker.record(latency_ms)
                return result
            except Exception as e:
                return e

        # Execute 1000 concurrent requests
        results = await concurrent_executor(
            make_request, count=1000, concurrency=200
        )

        success_rate = success_rate_calculator(results)
        percentiles = latency_tracker.calculate()

        print(f"\n1000 Concurrent Requests:")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  P50 Latency: {percentiles.get('p50', 0):.2f}ms")
        print(f"  P95 Latency: {percentiles.get('p95', 0):.2f}ms")
        print(f"  P99 Latency: {percentiles.get('p99', 0):.2f}ms")

        # Assertions
        assert (
            success_rate >= performance_targets["concurrent_1000_success_rate"]
        ), f"Success rate {success_rate:.1%} below target"

    async def test_varying_concurrency_levels(
        self,
        gateway_client,
        sample_messages,
        concurrent_executor,
        success_rate_calculator,
    ):
        """Test different concurrency levels to find breaking point."""
        concurrency_levels = [10, 50, 100, 200, 500]
        results_by_level = {}

        for concurrency in concurrency_levels:

            async def make_request():
                try:
                    return await gateway_client.route(
                        messages=sample_messages, strategy=RoutingStrategy.BALANCED
                    )
                except Exception as e:
                    return e

            start_time = time.time()
            results = await concurrent_executor(
                make_request, count=concurrency, concurrency=concurrency
            )
            duration = time.time() - start_time

            success_rate = success_rate_calculator(results)

            results_by_level[concurrency] = {
                "success_rate": success_rate,
                "duration": duration,
                "throughput": concurrency / duration,
            }

        print(f"\nConcurrency Scaling:")
        for level, metrics in results_by_level.items():
            print(f"  {level} concurrent:")
            print(f"    Success: {metrics['success_rate']:.1%}")
            print(f"    Duration: {metrics['duration']:.2f}s")
            print(f"    Throughput: {metrics['throughput']:.2f} req/s")

        # All levels should have good success rates
        for level, metrics in results_by_level.items():
            assert (
                metrics["success_rate"] >= 0.90
            ), f"{level} concurrent had low success rate: {metrics['success_rate']:.1%}"
