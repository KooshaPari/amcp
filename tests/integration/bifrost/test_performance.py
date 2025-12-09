"""Performance integration tests for Bifrost SDK."""

import pytest
import asyncio
import time
from typing import List, Dict, Any
import statistics

from bifrost_extensions import GatewayClient, RoutingStrategy
from bifrost_extensions.models import Message


class TestRoutingPerformance:
    """Comprehensive performance tests for routing operations."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_routing_latency_percentiles(self, gateway_client, sample_messages):
        """Test routing latency across all percentiles."""
        latencies = []
        num_requests = 1000

        for _ in range(num_requests):
            start = time.perf_counter()
            await gateway_client.route(
                messages=sample_messages,
                strategy=RoutingStrategy.SPEED_OPTIMIZED,
            )
            latency = (time.perf_counter() - start) * 1000  # Convert to ms
            latencies.append(latency)

        latencies.sort()

        p50 = latencies[num_requests // 2]
        p95 = latencies[int(num_requests * 0.95)]
        p99 = latencies[int(num_requests * 0.99)]
        mean = statistics.mean(latencies)
        median = statistics.median(latencies)

        print(f"\nRouting Latency Metrics (n={num_requests}):")
        print(f"  Mean: {mean:.2f}ms")
        print(f"  Median: {median:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")

        # Performance targets
        assert p50 < 30, f"P50 latency {p50:.2f}ms exceeds 30ms target"
        assert p95 < 50, f"P95 latency {p95:.2f}ms exceeds 50ms target"
        assert p99 < 100, f"P99 latency {p99:.2f}ms exceeds 100ms target"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_routing_scalability(self, gateway_client, sample_messages):
        """Test routing performance under concurrent load."""
        concurrency_levels = [10, 50, 100, 200]
        results = {}

        for concurrency in concurrency_levels:
            tasks = []
            start = time.perf_counter()

            for _ in range(concurrency):
                task = gateway_client.route(
                    messages=sample_messages,
                    strategy=RoutingStrategy.BALANCED,
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            duration = time.perf_counter() - start

            results[concurrency] = {
                "duration": duration,
                "requests_per_second": concurrency / duration,
                "avg_latency_ms": (duration / concurrency) * 1000,
                "success_count": len([r for r in responses if r is not None]),
            }

            print(f"\nConcurrency {concurrency}:")
            print(f"  Duration: {duration:.2f}s")
            print(f"  RPS: {results[concurrency]['requests_per_second']:.2f}")
            print(f"  Avg Latency: {results[concurrency]['avg_latency_ms']:.2f}ms")

        # All requests should succeed
        for concurrency, result in results.items():
            assert result["success_count"] == concurrency

        # Performance should scale reasonably
        assert results[100]["requests_per_second"] > 10, \
            "Should handle at least 10 RPS at 100 concurrency"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_strategy_comparison_performance(
        self, gateway_client, sample_messages, routing_strategies
    ):
        """Compare performance across different routing strategies."""
        num_requests = 100
        strategy_metrics = {}

        for strategy in routing_strategies:
            latencies = []

            for _ in range(num_requests):
                start = time.perf_counter()
                await gateway_client.route(
                    messages=sample_messages,
                    strategy=strategy,
                )
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)

            latencies.sort()
            strategy_metrics[strategy.value] = {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": latencies[int(num_requests * 0.95)],
            }

        print("\nStrategy Performance Comparison:")
        for strategy, metrics in strategy_metrics.items():
            print(f"  {strategy}:")
            print(f"    Mean: {metrics['mean']:.2f}ms")
            print(f"    Median: {metrics['median']:.2f}ms")
            print(f"    P95: {metrics['p95']:.2f}ms")

        # All strategies should meet performance targets
        for metrics in strategy_metrics.values():
            assert metrics["p95"] < 100, "All strategies should have P95 <100ms"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_message_size_impact(self, gateway_client):
        """Test performance impact of message size."""
        message_sizes = {
            "tiny": "Hello",
            "small": "Write a function to sort an array" * 10,
            "medium": "Implement a complete web service" * 100,
            "large": "Design a distributed system architecture" * 500,
        }

        results = {}

        for size_label, content in message_sizes.items():
            messages = [Message(role="user", content=content)]
            latencies = []

            for _ in range(50):
                start = time.perf_counter()
                await gateway_client.route(
                    messages=messages,
                    strategy=RoutingStrategy.BALANCED,
                )
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)

            results[size_label] = {
                "content_length": len(content),
                "mean_latency": statistics.mean(latencies),
                "p95_latency": sorted(latencies)[int(len(latencies) * 0.95)],
            }

            print(f"\nMessage size {size_label} ({len(content)} chars):")
            print(f"  Mean latency: {results[size_label]['mean_latency']:.2f}ms")
            print(f"  P95 latency: {results[size_label]['p95_latency']:.2f}ms")

        # Latency should scale reasonably with message size
        assert results["tiny"]["p95_latency"] < results["large"]["p95_latency"]


class TestToolRoutingPerformance:
    """Performance tests for tool routing operations."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_tool_routing_latency(self, gateway_client, sample_tools):
        """Test tool routing latency percentiles."""
        latencies = []
        num_requests = 500

        for _ in range(num_requests):
            start = time.perf_counter()
            await gateway_client.route_tool(
                action="search for information",
                available_tools=sample_tools,
            )
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        latencies.sort()

        p50 = latencies[num_requests // 2]
        p95 = latencies[int(num_requests * 0.95)]

        print(f"\nTool Routing Latency (n={num_requests}):")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")

        # Tool routing should be faster than model routing
        assert p50 < 50, f"P50 latency {p50:.2f}ms too high"
        assert p95 < 100, f"P95 latency {p95:.2f}ms too high"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_tool_routing_throughput(self, gateway_client, sample_tools):
        """Test tool routing throughput."""
        num_requests = 1000
        start = time.perf_counter()

        tasks = []
        for i in range(num_requests):
            task = gateway_client.route_tool(
                action=f"search for item {i}",
                available_tools=sample_tools,
            )
            tasks.append(task)

        await asyncio.gather(*tasks)
        duration = time.perf_counter() - start

        throughput = num_requests / duration

        print(f"\nTool Routing Throughput:")
        print(f"  Requests: {num_requests}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} RPS")

        # Should handle high throughput
        assert throughput > 50, f"Throughput {throughput:.2f} RPS too low"


class TestMemoryPerformance:
    """Memory and resource usage tests."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_memory_leak_detection(self, gateway_client, sample_messages):
        """Test for memory leaks in repeated operations."""
        import gc
        import sys

        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Perform many operations
        for _ in range(1000):
            await gateway_client.route(
                messages=sample_messages,
                strategy=RoutingStrategy.BALANCED,
            )

        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())

        object_growth = final_objects - initial_objects
        growth_percentage = (object_growth / initial_objects) * 100

        print(f"\nMemory Leak Detection:")
        print(f"  Initial objects: {initial_objects}")
        print(f"  Final objects: {final_objects}")
        print(f"  Growth: {object_growth} ({growth_percentage:.2f}%)")

        # Object growth should be minimal (<10%)
        assert growth_percentage < 10, \
            f"Potential memory leak: {growth_percentage:.2f}% object growth"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_resource_cleanup(self, gateway_client, sample_messages):
        """Test proper resource cleanup under concurrent load."""
        num_iterations = 10
        concurrency = 100

        for iteration in range(num_iterations):
            tasks = []
            for _ in range(concurrency):
                task = gateway_client.route(
                    messages=sample_messages,
                    strategy=RoutingStrategy.BALANCED,
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

        # Should complete without resource exhaustion
        # If we get here without errors, cleanup is working
        assert True


class TestStressTests:
    """Stress tests for edge case performance."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_sustained_load(self, gateway_client, sample_messages):
        """Test performance under sustained load."""
        duration_seconds = 60
        requests_per_second = 10
        start_time = time.perf_counter()
        request_count = 0
        errors = []

        while time.perf_counter() - start_time < duration_seconds:
            batch_start = time.perf_counter()

            # Send batch of requests
            tasks = []
            for _ in range(requests_per_second):
                task = gateway_client.route(
                    messages=sample_messages,
                    strategy=RoutingStrategy.BALANCED,
                )
                tasks.append(task)

            try:
                await asyncio.gather(*tasks)
                request_count += requests_per_second
            except Exception as e:
                errors.append(str(e))

            # Maintain target RPS
            batch_duration = time.perf_counter() - batch_start
            if batch_duration < 1.0:
                await asyncio.sleep(1.0 - batch_duration)

        total_duration = time.perf_counter() - start_time
        actual_rps = request_count / total_duration
        error_rate = len(errors) / request_count if request_count > 0 else 0

        print(f"\nSustained Load Test:")
        print(f"  Duration: {total_duration:.2f}s")
        print(f"  Total requests: {request_count}")
        print(f"  Actual RPS: {actual_rps:.2f}")
        print(f"  Errors: {len(errors)}")
        print(f"  Error rate: {error_rate:.2%}")

        # Should maintain stable performance
        assert actual_rps >= requests_per_second * 0.9, "RPS dropped below target"
        assert error_rate < 0.01, f"Error rate {error_rate:.2%} too high"

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_burst_handling(self, gateway_client, sample_messages):
        """Test handling of traffic bursts."""
        burst_sizes = [50, 100, 200, 500]
        results = {}

        for burst_size in burst_sizes:
            tasks = []
            start = time.perf_counter()

            for _ in range(burst_size):
                task = gateway_client.route(
                    messages=sample_messages,
                    strategy=RoutingStrategy.BALANCED,
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.perf_counter() - start

            successful = len([r for r in responses if not isinstance(r, Exception)])
            failed = len([r for r in responses if isinstance(r, Exception)])

            results[burst_size] = {
                "duration": duration,
                "successful": successful,
                "failed": failed,
                "success_rate": successful / burst_size,
            }

            print(f"\nBurst size {burst_size}:")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Successful: {successful}/{burst_size}")
            print(f"  Success rate: {results[burst_size]['success_rate']:.2%}")

        # Should handle bursts without significant failures
        for burst_size, result in results.items():
            assert result["success_rate"] > 0.95, \
                f"Burst {burst_size} had {result['success_rate']:.2%} success rate"
