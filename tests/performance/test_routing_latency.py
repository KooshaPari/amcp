"""Routing latency benchmarks.

Tests routing decision latency across different strategies and message complexities.
Target: P95 < 50ms
"""

import asyncio
import time
from typing import Dict

import pytest

from bifrost_extensions.models import RoutingStrategy


@pytest.mark.asyncio
@pytest.mark.benchmark
class TestRoutingLatency:
    """Test routing latency across different scenarios."""

    async def test_simple_routing_latency(
        self,
        gateway_client,
        sample_messages,
        latency_tracker,
        perf_tracker,
        performance_targets,
    ):
        """Benchmark latency for simple routing decisions.

        Target: P95 < 50ms
        """
        perf_tracker.start()

        for _ in range(100):
            start = time.perf_counter()

            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

            latency_ms = (time.perf_counter() - start) * 1000
            latency_tracker.record(latency_ms)

        metrics = perf_tracker.stop("simple_routing", 100)
        percentiles = latency_tracker.calculate()

        # Assertions
        assert (
            percentiles["p95"] < performance_targets["routing_latency_p95_ms"]
        ), f"P95 latency {percentiles['p95']:.2f}ms exceeds target"
        assert (
            percentiles["p99"] < performance_targets["routing_latency_p95_ms"] * 2
        ), f"P99 latency {percentiles['p99']:.2f}ms too high"

        print(f"\nSimple Routing Latency:")
        print(f"  P50: {percentiles['p50']:.2f}ms")
        print(f"  P95: {percentiles['p95']:.2f}ms")
        print(f"  P99: {percentiles['p99']:.2f}ms")
        print(f"  Mean: {percentiles['mean']:.2f}ms")
        print(f"  Throughput: {metrics['throughput']:.2f} req/s")

    async def test_complex_routing_latency(
        self,
        gateway_client,
        complex_messages,
        latency_tracker,
        perf_tracker,
        performance_targets,
    ):
        """Benchmark latency for complex prompts.

        Complex prompts may require more sophisticated routing logic.
        Target: P95 < 100ms (2x simple)
        """
        perf_tracker.start()

        for _ in range(50):
            start = time.perf_counter()

            await gateway_client.route(
                messages=complex_messages, strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED
            )

            latency_ms = (time.perf_counter() - start) * 1000
            latency_tracker.record(latency_ms)

        metrics = perf_tracker.stop("complex_routing", 50)
        percentiles = latency_tracker.calculate()

        # Assertions (relaxed for complex routing)
        assert (
            percentiles["p95"] < performance_targets["routing_latency_p95_ms"] * 2
        ), f"P95 latency {percentiles['p95']:.2f}ms exceeds 2x target"

        print(f"\nComplex Routing Latency:")
        print(f"  P50: {percentiles['p50']:.2f}ms")
        print(f"  P95: {percentiles['p95']:.2f}ms")
        print(f"  P99: {percentiles['p99']:.2f}ms")
        print(f"  Mean: {percentiles['mean']:.2f}ms")

    async def test_routing_strategies_comparison(
        self, gateway_client, sample_messages, perf_tracker
    ):
        """Compare latency across different routing strategies."""
        strategies = [
            RoutingStrategy.COST_OPTIMIZED,
            RoutingStrategy.PERFORMANCE_OPTIMIZED,
            RoutingStrategy.BALANCED,
        ]

        results: Dict[str, Dict] = {}

        for strategy in strategies:
            latencies = []

            for _ in range(50):
                start = time.perf_counter()
                await gateway_client.route(messages=sample_messages, strategy=strategy)
                latency_ms = (time.perf_counter() - start) * 1000
                latencies.append(latency_ms)

            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)

            results[strategy.value] = {
                "p50": sorted_latencies[int(n * 0.50)],
                "p95": sorted_latencies[int(n * 0.95)],
                "mean": sum(sorted_latencies) / n,
            }

        print(f"\nStrategy Latency Comparison:")
        for strategy, metrics in results.items():
            print(f"  {strategy}:")
            print(f"    P50: {metrics['p50']:.2f}ms")
            print(f"    P95: {metrics['p95']:.2f}ms")
            print(f"    Mean: {metrics['mean']:.2f}ms")

        # All strategies should meet targets
        for strategy, metrics in results.items():
            assert (
                metrics["p95"] < 100
            ), f"{strategy} P95 latency too high: {metrics['p95']:.2f}ms"

    async def test_routing_with_constraints_latency(
        self, gateway_client, sample_messages, latency_tracker
    ):
        """Test routing latency with various constraints."""
        constraints = [
            {"max_cost_usd": 0.01},
            {"max_latency_ms": 500},
            {"max_cost_usd": 0.005, "max_latency_ms": 1000},
        ]

        for constraint in constraints:
            start = time.perf_counter()

            await gateway_client.route(
                messages=sample_messages,
                strategy=RoutingStrategy.BALANCED,
                constraints=constraint,
            )

            latency_ms = (time.perf_counter() - start) * 1000
            latency_tracker.record(latency_ms)

        percentiles = latency_tracker.calculate()

        print(f"\nConstrained Routing Latency:")
        print(f"  P95: {percentiles['p95']:.2f}ms")
        print(f"  Mean: {percentiles['mean']:.2f}ms")

        assert (
            percentiles["p95"] < 100
        ), f"Constrained routing P95 too high: {percentiles['p95']:.2f}ms"

    async def test_sequential_routing_consistency(
        self, gateway_client, sample_messages, latency_tracker
    ):
        """Test latency consistency across sequential requests."""
        latencies = []

        for i in range(100):
            start = time.perf_counter()

            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)
            latency_tracker.record(latency_ms)

        # Calculate variance
        mean = sum(latencies) / len(latencies)
        variance = sum((x - mean) ** 2 for x in latencies) / len(latencies)
        std_dev = variance**0.5
        coefficient_of_variation = std_dev / mean

        percentiles = latency_tracker.calculate()

        print(f"\nSequential Routing Consistency:")
        print(f"  Mean: {mean:.2f}ms")
        print(f"  Std Dev: {std_dev:.2f}ms")
        print(f"  CV: {coefficient_of_variation:.2%}")
        print(f"  P95: {percentiles['p95']:.2f}ms")

        # Latency should be consistent (CV < 50%)
        assert (
            coefficient_of_variation < 0.5
        ), f"High variance in latency: CV={coefficient_of_variation:.2%}"


@pytest.mark.asyncio
@pytest.mark.benchmark
class TestToolRoutingLatency:
    """Test tool routing latency."""

    async def test_tool_routing_latency(
        self,
        gateway_client,
        tool_actions,
        available_tools,
        latency_tracker,
        performance_targets,
    ):
        """Benchmark tool routing latency.

        Tool routing should be very fast (simpler logic).
        Target: P95 < 10ms
        """
        for action in tool_actions:
            start = time.perf_counter()

            await gateway_client.route_tool(
                action=action, available_tools=available_tools
            )

            latency_ms = (time.perf_counter() - start) * 1000
            latency_tracker.record(latency_ms)

        percentiles = latency_tracker.calculate()

        print(f"\nTool Routing Latency:")
        print(f"  P50: {percentiles['p50']:.2f}ms")
        print(f"  P95: {percentiles['p95']:.2f}ms")
        print(f"  P99: {percentiles['p99']:.2f}ms")

        assert (
            percentiles["p95"] < performance_targets["tool_routing_latency_p95_ms"]
        ), f"Tool routing P95 {percentiles['p95']:.2f}ms exceeds target"

    async def test_tool_routing_with_many_tools(
        self, gateway_client, latency_tracker, performance_targets
    ):
        """Test tool routing with large number of available tools."""
        many_tools = [f"tool_{i}" for i in range(100)]

        for i in range(20):
            start = time.perf_counter()

            await gateway_client.route_tool(
                action=f"perform action {i}", available_tools=many_tools
            )

            latency_ms = (time.perf_counter() - start) * 1000
            latency_tracker.record(latency_ms)

        percentiles = latency_tracker.calculate()

        print(f"\nTool Routing (100 tools) Latency:")
        print(f"  P95: {percentiles['p95']:.2f}ms")

        # Should still be fast even with many tools
        assert (
            percentiles["p95"] < performance_targets["tool_routing_latency_p95_ms"] * 2
        ), f"Tool routing with many tools too slow: {percentiles['p95']:.2f}ms"


@pytest.mark.asyncio
@pytest.mark.benchmark
class TestClassificationLatency:
    """Test classification latency."""

    async def test_classification_latency(
        self,
        gateway_client,
        classification_prompts,
        latency_tracker,
        performance_targets,
    ):
        """Benchmark classification latency.

        Classification should be very fast (keyword/pattern matching).
        Target: P95 < 5ms
        """
        for prompt in classification_prompts:
            start = time.perf_counter()

            await gateway_client.classify(
                prompt=prompt, categories=["simple", "moderate", "complex"]
            )

            latency_ms = (time.perf_counter() - start) * 1000
            latency_tracker.record(latency_ms)

        percentiles = latency_tracker.calculate()

        print(f"\nClassification Latency:")
        print(f"  P50: {percentiles['p50']:.2f}ms")
        print(f"  P95: {percentiles['p95']:.2f}ms")
        print(f"  P99: {percentiles['p99']:.2f}ms")

        assert (
            percentiles["p95"] < performance_targets["classification_latency_p95_ms"]
        ), f"Classification P95 {percentiles['p95']:.2f}ms exceeds target"

    async def test_classification_without_categories(
        self, gateway_client, latency_tracker
    ):
        """Test auto-detection classification latency."""
        prompts = ["Write a function", "Build a system", "Fix a bug"]

        for prompt in prompts:
            start = time.perf_counter()

            await gateway_client.classify(prompt=prompt)

            latency_ms = (time.perf_counter() - start) * 1000
            latency_tracker.record(latency_ms)

        percentiles = latency_tracker.calculate()

        print(f"\nAuto-detection Classification Latency:")
        print(f"  P95: {percentiles['p95']:.2f}ms")

        # Auto-detection might be slightly slower
        assert percentiles["p95"] < 10, f"Auto-detection too slow: {percentiles['p95']:.2f}ms"
