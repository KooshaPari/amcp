"""Throughput benchmarks.

Tests maximum sustainable throughput (requests per second).
Target: 1000 req/sec
"""

import asyncio
import time
from typing import List

import pytest

from bifrost_extensions.models import RoutingStrategy


@pytest.mark.asyncio
@pytest.mark.benchmark
class TestThroughput:
    """Test maximum throughput under various conditions."""

    async def test_routing_throughput(
        self, gateway_client, sample_messages, perf_tracker, performance_targets
    ):
        """Measure routing throughput (requests per second).

        Target: 1000 req/sec
        """
        duration_seconds = 10
        request_count = 0

        perf_tracker.start()
        start_time = time.time()
        end_time = start_time + duration_seconds

        while time.time() < end_time:
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )
            request_count += 1

        actual_duration = time.time() - start_time
        metrics = perf_tracker.stop("routing_throughput", request_count)

        throughput = request_count / actual_duration

        print(f"\nRouting Throughput:")
        print(f"  Total Requests: {request_count}")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} req/s")
        print(f"  Avg Latency: {metrics['avg_latency_ms']:.2f}ms")
        print(f"  Memory: {metrics['memory_mb']:.2f}MB")

        # Should meet throughput target
        assert (
            throughput >= performance_targets["throughput_rps"] * 0.8
        ), f"Throughput {throughput:.2f} req/s below 80% of target"

    async def test_sustained_throughput(
        self, gateway_client, sample_messages, perf_tracker
    ):
        """Test sustained throughput over extended period.

        Ensures performance doesn't degrade over time.
        """
        duration_seconds = 60
        checkpoint_interval = 10
        checkpoints = []

        start_time = time.time()
        end_time = start_time + duration_seconds
        last_checkpoint = start_time
        checkpoint_requests = 0

        perf_tracker.start()

        while time.time() < end_time:
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )
            checkpoint_requests += 1

            # Record checkpoint every N seconds
            if time.time() - last_checkpoint >= checkpoint_interval:
                checkpoint_duration = time.time() - last_checkpoint
                checkpoint_throughput = checkpoint_requests / checkpoint_duration

                checkpoints.append(
                    {
                        "elapsed": time.time() - start_time,
                        "throughput": checkpoint_throughput,
                        "requests": checkpoint_requests,
                    }
                )

                last_checkpoint = time.time()
                checkpoint_requests = 0

        metrics = perf_tracker.stop("sustained_throughput", sum(c["requests"] for c in checkpoints))

        print(f"\nSustained Throughput (60s):")
        for cp in checkpoints:
            print(f"  {cp['elapsed']:.0f}s: {cp['throughput']:.2f} req/s")

        # Calculate degradation
        if len(checkpoints) >= 2:
            first_throughput = checkpoints[0]["throughput"]
            last_throughput = checkpoints[-1]["throughput"]
            degradation = (first_throughput - last_throughput) / first_throughput

            print(f"\nThroughput Degradation: {degradation:.1%}")

            # Should not degrade more than 20%
            assert (
                degradation < 0.2
            ), f"Throughput degraded {degradation:.1%} over 60s"

    async def test_burst_throughput(self, gateway_client, sample_messages, perf_tracker):
        """Test burst throughput (short duration, max speed).

        Measures peak throughput in ideal conditions.
        """
        burst_duration = 5
        request_count = 0

        perf_tracker.start()
        start_time = time.time()
        end_time = start_time + burst_duration

        # Run requests as fast as possible
        tasks = []
        while time.time() < end_time:
            task = asyncio.create_task(
                gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )
            )
            tasks.append(task)
            request_count += 1

            # Prevent too many pending tasks
            if len(tasks) >= 100:
                await asyncio.gather(*tasks)
                tasks = []

        # Wait for remaining tasks
        if tasks:
            await asyncio.gather(*tasks)

        actual_duration = time.time() - start_time
        metrics = perf_tracker.stop("burst_throughput", request_count)

        burst_throughput = request_count / actual_duration

        print(f"\nBurst Throughput (5s):")
        print(f"  Total Requests: {request_count}")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Peak Throughput: {burst_throughput:.2f} req/s")
        print(f"  Avg Latency: {metrics['avg_latency_ms']:.2f}ms")

    async def test_mixed_operation_throughput(
        self, gateway_client, sample_messages, tool_actions, available_tools
    ):
        """Test throughput with mixed operations.

        Simulates realistic workload with routing, tool routing, and classification.
        """
        duration_seconds = 10
        operation_counts = {"routing": 0, "tool_routing": 0, "classification": 0}

        start_time = time.time()
        end_time = start_time + duration_seconds

        while time.time() < end_time:
            # Rotate through operations
            op = operation_counts.keys()
            op_index = sum(operation_counts.values()) % 3

            if op_index == 0:
                await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )
                operation_counts["routing"] += 1
            elif op_index == 1:
                await gateway_client.route_tool(
                    action=tool_actions[0], available_tools=available_tools
                )
                operation_counts["tool_routing"] += 1
            else:
                await gateway_client.classify(prompt="test prompt")
                operation_counts["classification"] += 1

        actual_duration = time.time() - start_time
        total_requests = sum(operation_counts.values())
        total_throughput = total_requests / actual_duration

        print(f"\nMixed Operation Throughput:")
        print(f"  Total Requests: {total_requests}")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Throughput: {total_throughput:.2f} req/s")
        print(f"  Routing: {operation_counts['routing']}")
        print(f"  Tool Routing: {operation_counts['tool_routing']}")
        print(f"  Classification: {operation_counts['classification']}")


@pytest.mark.asyncio
@pytest.mark.benchmark
class TestThroughputScaling:
    """Test throughput scaling characteristics."""

    async def test_throughput_vs_message_complexity(
        self, gateway_client, sample_messages, complex_messages
    ):
        """Compare throughput for simple vs complex messages."""
        test_cases = [
            ("simple", sample_messages),
            ("complex", complex_messages),
        ]

        results = {}

        for name, messages in test_cases:
            request_count = 0
            duration = 5

            start_time = time.time()
            end_time = start_time + duration

            while time.time() < end_time:
                await gateway_client.route(
                    messages=messages, strategy=RoutingStrategy.BALANCED
                )
                request_count += 1

            actual_duration = time.time() - start_time
            throughput = request_count / actual_duration

            results[name] = {
                "requests": request_count,
                "throughput": throughput,
            }

        print(f"\nThroughput vs Message Complexity:")
        for name, data in results.items():
            print(f"  {name.capitalize()}:")
            print(f"    Throughput: {data['throughput']:.2f} req/s")
            print(f"    Total: {data['requests']} requests")

    async def test_throughput_vs_strategy(self, gateway_client, sample_messages):
        """Compare throughput across routing strategies."""
        strategies = [
            RoutingStrategy.COST_OPTIMIZED,
            RoutingStrategy.PERFORMANCE_OPTIMIZED,
            RoutingStrategy.BALANCED,
        ]

        results = {}

        for strategy in strategies:
            request_count = 0
            duration = 5

            start_time = time.time()
            end_time = start_time + duration

            while time.time() < end_time:
                await gateway_client.route(messages=sample_messages, strategy=strategy)
                request_count += 1

            actual_duration = time.time() - start_time
            throughput = request_count / actual_duration

            results[strategy.value] = {
                "requests": request_count,
                "throughput": throughput,
            }

        print(f"\nThroughput vs Strategy:")
        for strategy, data in results.items():
            print(f"  {strategy}:")
            print(f"    Throughput: {data['throughput']:.2f} req/s")

    async def test_throughput_degradation_detection(
        self, gateway_client, sample_messages
    ):
        """Detect throughput degradation over time."""
        window_size = 10  # seconds
        num_windows = 6
        window_results = []

        for window in range(num_windows):
            request_count = 0
            start_time = time.time()
            end_time = start_time + window_size

            while time.time() < end_time:
                await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )
                request_count += 1

            actual_duration = time.time() - start_time
            throughput = request_count / actual_duration

            window_results.append(
                {"window": window + 1, "throughput": throughput, "requests": request_count}
            )

        print(f"\nThroughput Degradation Analysis:")
        for result in window_results:
            print(
                f"  Window {result['window']}: "
                f"{result['throughput']:.2f} req/s "
                f"({result['requests']} requests)"
            )

        # Calculate trend
        first_half_avg = sum(r["throughput"] for r in window_results[:3]) / 3
        second_half_avg = sum(r["throughput"] for r in window_results[3:]) / 3
        degradation_pct = (first_half_avg - second_half_avg) / first_half_avg

        print(f"\nFirst Half Avg: {first_half_avg:.2f} req/s")
        print(f"Second Half Avg: {second_half_avg:.2f} req/s")
        print(f"Degradation: {degradation_pct:.1%}")

        # Should not degrade significantly
        assert (
            abs(degradation_pct) < 0.25
        ), f"Significant throughput degradation: {degradation_pct:.1%}"
