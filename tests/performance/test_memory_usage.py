"""Memory usage and resource monitoring tests.

Tests memory consumption and resource usage patterns.
Target: <10MB per request, no memory leaks
"""

import asyncio
import gc
import time
from typing import List

import psutil
import pytest

from bifrost_extensions.models import RoutingStrategy


@pytest.mark.asyncio
@pytest.mark.benchmark
class TestMemoryUsage:
    """Test memory consumption patterns."""

    async def test_memory_per_request(
        self, gateway_client, sample_messages, performance_targets
    ):
        """Measure memory usage per routing request.

        Target: <10MB per request
        """
        process = psutil.Process()

        # Force garbage collection
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Execute requests
        request_count = 100
        for _ in range(request_count):
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

        # Force garbage collection again
        gc.collect()
        await asyncio.sleep(0.1)  # Allow cleanup

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - baseline_memory
        memory_per_request = memory_growth / request_count

        print(f"\nMemory Per Request:")
        print(f"  Baseline: {baseline_memory:.2f}MB")
        print(f"  Final: {final_memory:.2f}MB")
        print(f"  Growth: {memory_growth:.2f}MB")
        print(f"  Per Request: {memory_per_request:.2f}MB")

        # Should meet target
        assert (
            memory_per_request < performance_targets["memory_per_request_mb"]
        ), f"Memory per request {memory_per_request:.2f}MB exceeds target"

    async def test_memory_leak_detection(self, gateway_client, sample_messages):
        """Detect memory leaks over extended operation.

        Runs multiple batches and checks if memory grows linearly.
        """
        process = psutil.Process()
        batch_size = 50
        num_batches = 10
        memory_samples = []

        gc.collect()

        for batch in range(num_batches):
            batch_start_memory = process.memory_info().rss / 1024 / 1024

            # Execute batch
            for _ in range(batch_size):
                await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )

            # Force GC and measure
            gc.collect()
            await asyncio.sleep(0.1)

            batch_end_memory = process.memory_info().rss / 1024 / 1024
            batch_growth = batch_end_memory - batch_start_memory

            memory_samples.append(
                {
                    "batch": batch + 1,
                    "start_mb": batch_start_memory,
                    "end_mb": batch_end_memory,
                    "growth_mb": batch_growth,
                }
            )

        print(f"\nMemory Leak Detection (10 batches x 50 requests):")
        for sample in memory_samples:
            print(
                f"  Batch {sample['batch']}: "
                f"{sample['start_mb']:.2f}MB -> {sample['end_mb']:.2f}MB "
                f"(+{sample['growth_mb']:.2f}MB)"
            )

        # Analyze trend
        first_half_growth = sum(s["growth_mb"] for s in memory_samples[:5])
        second_half_growth = sum(s["growth_mb"] for s in memory_samples[5:])

        print(f"\nFirst Half Growth: {first_half_growth:.2f}MB")
        print(f"Second Half Growth: {second_half_growth:.2f}MB")

        # Memory growth should stabilize (second half <= first half)
        growth_ratio = second_half_growth / first_half_growth if first_half_growth > 0 else 0

        print(f"Growth Ratio (2nd/1st): {growth_ratio:.2f}")

        assert growth_ratio <= 1.5, f"Memory growth increasing: ratio={growth_ratio:.2f}"

    async def test_memory_cleanup_after_errors(self, gateway_client):
        """Test memory cleanup after errors."""
        process = psutil.Process()

        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024

        # Trigger errors (invalid requests)
        error_count = 0
        for _ in range(50):
            try:
                # Invalid: empty messages
                await gateway_client.route(messages=[], strategy=RoutingStrategy.BALANCED)
            except Exception:
                error_count += 1

        gc.collect()
        await asyncio.sleep(0.1)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - baseline_memory

        print(f"\nMemory After Errors:")
        print(f"  Errors Triggered: {error_count}")
        print(f"  Baseline: {baseline_memory:.2f}MB")
        print(f"  Final: {final_memory:.2f}MB")
        print(f"  Growth: {memory_growth:.2f}MB")

        # Minimal growth even with errors
        assert memory_growth < 50, f"Excessive memory after errors: {memory_growth:.2f}MB"

    async def test_concurrent_memory_usage(
        self, gateway_client, sample_messages, concurrent_executor
    ):
        """Test memory usage under concurrent load."""
        process = psutil.Process()

        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024

        # Run concurrent requests
        async def make_request():
            return await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

        await concurrent_executor(make_request, count=100, concurrency=50)

        gc.collect()
        await asyncio.sleep(0.5)  # Allow cleanup

        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = peak_memory - baseline_memory

        print(f"\nConcurrent Memory Usage (100 requests, 50 concurrent):")
        print(f"  Baseline: {baseline_memory:.2f}MB")
        print(f"  Peak: {peak_memory:.2f}MB")
        print(f"  Growth: {memory_growth:.2f}MB")

        # Should handle concurrency efficiently
        assert (
            memory_growth < 500
        ), f"Excessive memory under concurrency: {memory_growth:.2f}MB"


@pytest.mark.asyncio
@pytest.mark.benchmark
class TestResourceMonitoring:
    """Test CPU and other resource usage."""

    async def test_cpu_usage(self, gateway_client, sample_messages, perf_tracker):
        """Monitor CPU usage during operations."""
        process = psutil.Process()

        # Warm up
        for _ in range(10):
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

        # Measure CPU during load
        perf_tracker.start()
        cpu_samples = []

        for i in range(100):
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

            if i % 10 == 0:
                cpu_percent = process.cpu_percent(interval=0.1)
                cpu_samples.append(cpu_percent)

        metrics = perf_tracker.stop("cpu_monitoring", 100)

        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        max_cpu = max(cpu_samples) if cpu_samples else 0

        print(f"\nCPU Usage:")
        print(f"  Average: {avg_cpu:.1f}%")
        print(f"  Max: {max_cpu:.1f}%")
        print(f"  Samples: {len(cpu_samples)}")

        # CPU should be reasonable
        assert avg_cpu < 80, f"High average CPU usage: {avg_cpu:.1f}%"

    async def test_thread_count_stability(self, gateway_client, sample_messages):
        """Ensure thread count remains stable."""
        process = psutil.Process()

        baseline_threads = process.num_threads()

        # Execute requests
        for _ in range(100):
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

        final_threads = process.num_threads()
        thread_growth = final_threads - baseline_threads

        print(f"\nThread Count:")
        print(f"  Baseline: {baseline_threads}")
        print(f"  Final: {final_threads}")
        print(f"  Growth: {thread_growth}")

        # Thread count should not grow significantly
        assert abs(thread_growth) < 10, f"Thread count grew: {thread_growth}"

    async def test_file_descriptor_usage(self, gateway_client, sample_messages):
        """Monitor file descriptor usage."""
        process = psutil.Process()

        try:
            baseline_fds = process.num_fds()
        except AttributeError:
            # Windows doesn't support num_fds
            pytest.skip("File descriptor monitoring not available on this platform")
            return

        # Execute requests
        for _ in range(50):
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

        final_fds = process.num_fds()
        fd_growth = final_fds - baseline_fds

        print(f"\nFile Descriptors:")
        print(f"  Baseline: {baseline_fds}")
        print(f"  Final: {final_fds}")
        print(f"  Growth: {fd_growth}")

        # FDs should not leak
        assert abs(fd_growth) < 20, f"File descriptor leak: {fd_growth}"

    async def test_network_connections(self, gateway_client, sample_messages):
        """Monitor network connection count."""
        process = psutil.Process()

        baseline_conns = len(process.connections())

        # Execute requests
        for _ in range(30):
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

        # Allow connection pooling to settle
        await asyncio.sleep(1.0)

        final_conns = len(process.connections())
        conn_growth = final_conns - baseline_conns

        print(f"\nNetwork Connections:")
        print(f"  Baseline: {baseline_conns}")
        print(f"  Final: {final_conns}")
        print(f"  Growth: {conn_growth}")

        # Should reuse connections (connection pooling)
        assert (
            conn_growth < 10
        ), f"Too many new connections (no pooling?): {conn_growth}"


@pytest.mark.asyncio
@pytest.mark.benchmark
class TestGarbageCollection:
    """Test garbage collection behavior."""

    async def test_gc_frequency(self, gateway_client, sample_messages):
        """Monitor garbage collection frequency."""
        gc.collect()
        gc_stats_before = gc.get_stats()

        # Execute operations
        for _ in range(100):
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

        gc.collect()
        gc_stats_after = gc.get_stats()

        print(f"\nGarbage Collection Stats:")
        print(f"  Before: {gc_stats_before}")
        print(f"  After: {gc_stats_after}")

    async def test_object_creation_rate(self, gateway_client, sample_messages):
        """Monitor object creation rate."""
        gc.collect()
        gc.disable()  # Disable auto GC for measurement

        try:
            before_count = len(gc.get_objects())

            # Execute operations
            for _ in range(50):
                await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )

            after_count = len(gc.get_objects())
            objects_created = after_count - before_count

            print(f"\nObject Creation:")
            print(f"  Before: {before_count} objects")
            print(f"  After: {after_count} objects")
            print(f"  Created: {objects_created} objects")
            print(f"  Per Request: {objects_created / 50:.2f} objects")

        finally:
            gc.enable()

    async def test_reference_cycles(self, gateway_client, sample_messages):
        """Check for reference cycles."""
        gc.collect()

        # Execute operations
        for _ in range(50):
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )

        # Check for garbage
        gc.collect()
        garbage_count = len(gc.garbage)

        print(f"\nGarbage Collection:")
        print(f"  Uncollectable objects: {garbage_count}")

        # Should have no uncollectable objects
        assert garbage_count == 0, f"Found {garbage_count} uncollectable objects"
