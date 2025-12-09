"""Stress tests for sustained and spike load.

Tests system behavior under sustained high load and sudden traffic spikes.
- Sustained load (1000 req/sec for 5min)
- Spike test (instant 2x traffic)
- Soak test (500 req/sec for 1 hour)
"""

import asyncio
import time

import pytest

from bifrost_extensions.models import RoutingStrategy


@pytest.mark.asyncio
@pytest.mark.load
@pytest.mark.slow
class TestSustainedLoad:
    """Test sustained load over extended periods."""

    async def test_sustained_load_5_minutes(
        self,
        gateway_client,
        sample_messages,
        perf_tracker,
        latency_tracker,
        success_rate_calculator,
    ):
        """Sustained load: 1000 req/sec for 5 minutes.

        Tests system stability under sustained high load.
        """
        target_rps = 1000
        duration_seconds = 300  # 5 minutes
        interval_seconds = 1.0 / target_rps  # Time between requests

        total_requests = 0
        errors = []
        checkpoint_interval = 30  # Report every 30s
        last_checkpoint = time.time()

        perf_tracker.start()
        start_time = time.time()
        end_time = start_time + duration_seconds

        while time.time() < end_time:
            request_start = time.time()

            try:
                await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )
                total_requests += 1

                latency_ms = (time.perf_counter() - request_start) * 1000
                latency_tracker.record(latency_ms)

            except Exception as e:
                errors.append(e)

            # Checkpoint reporting
            if time.time() - last_checkpoint >= checkpoint_interval:
                elapsed = time.time() - start_time
                current_rps = total_requests / elapsed
                print(
                    f"  [{elapsed:.0f}s] "
                    f"Requests: {total_requests}, "
                    f"RPS: {current_rps:.2f}, "
                    f"Errors: {len(errors)}"
                )
                last_checkpoint = time.time()

            # Rate limiting
            sleep_time = max(0, interval_seconds - (time.time() - request_start))
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        metrics = perf_tracker.stop("sustained_load_5min", total_requests)
        percentiles = latency_tracker.calculate()

        actual_duration = time.time() - start_time
        actual_rps = total_requests / actual_duration
        success_rate = (
            (total_requests - len(errors)) / total_requests
            if total_requests > 0
            else 0
        )

        print(f"\nSustained Load (5 minutes):")
        print(f"  Total Requests: {total_requests}")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Actual RPS: {actual_rps:.2f}")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  P50 Latency: {percentiles.get('p50', 0):.2f}ms")
        print(f"  P95 Latency: {percentiles.get('p95', 0):.2f}ms")
        print(f"  Memory: {metrics['memory_mb']:.2f}MB")

        # Assertions
        assert success_rate >= 0.95, f"Low success rate: {success_rate:.1%}"
        assert (
            actual_rps >= target_rps * 0.9
        ), f"Actual RPS {actual_rps:.2f} below 90% of target"

    @pytest.mark.skip(reason="Long running test - run manually")
    async def test_soak_test_1_hour(
        self, gateway_client, sample_messages, perf_tracker, latency_tracker
    ):
        """Soak test: 500 req/sec for 1 hour.

        Tests for memory leaks and gradual performance degradation.
        """
        target_rps = 500
        duration_seconds = 3600  # 1 hour
        interval_seconds = 1.0 / target_rps

        total_requests = 0
        errors = []
        memory_samples = []
        latency_samples = []

        checkpoint_interval = 60  # Report every minute
        last_checkpoint = time.time()

        perf_tracker.start()
        start_time = time.time()
        end_time = start_time + duration_seconds

        while time.time() < end_time:
            request_start = time.time()

            try:
                await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )
                total_requests += 1

                latency_ms = (time.perf_counter() - request_start) * 1000
                latency_tracker.record(latency_ms)

            except Exception as e:
                errors.append(e)

            # Checkpoint reporting
            if time.time() - last_checkpoint >= checkpoint_interval:
                elapsed = time.time() - start_time
                current_rps = total_requests / elapsed

                # Sample memory
                import psutil

                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append({"time": elapsed, "memory_mb": memory_mb})

                print(
                    f"  [{elapsed/60:.0f}min] "
                    f"Requests: {total_requests}, "
                    f"RPS: {current_rps:.2f}, "
                    f"Memory: {memory_mb:.2f}MB"
                )

                last_checkpoint = time.time()

            # Rate limiting
            sleep_time = max(0, interval_seconds - (time.time() - request_start))
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        metrics = perf_tracker.stop("soak_test_1hour", total_requests)
        percentiles = latency_tracker.calculate()

        # Analyze memory trend
        if len(memory_samples) >= 2:
            first_memory = memory_samples[0]["memory_mb"]
            last_memory = memory_samples[-1]["memory_mb"]
            memory_growth = last_memory - first_memory
            memory_growth_pct = (memory_growth / first_memory) * 100

            print(f"\nMemory Analysis:")
            print(f"  Initial: {first_memory:.2f}MB")
            print(f"  Final: {last_memory:.2f}MB")
            print(f"  Growth: {memory_growth:.2f}MB ({memory_growth_pct:.1f}%)")

            # Should not have significant memory growth
            assert (
                memory_growth_pct < 50
            ), f"Excessive memory growth: {memory_growth_pct:.1f}%"

        print(f"\nSoak Test (1 hour):")
        print(f"  Total Requests: {total_requests}")
        print(
            f"  Success Rate: "
            f"{(total_requests - len(errors))/total_requests:.1%}"
        )
        print(f"  P95 Latency: {percentiles.get('p95', 0):.2f}ms")


@pytest.mark.asyncio
@pytest.mark.load
class TestSpikeLoad:
    """Test response to sudden traffic spikes."""

    async def test_traffic_spike_2x(
        self,
        gateway_client,
        sample_messages,
        concurrent_executor,
        success_rate_calculator,
    ):
        """Test 2x instant traffic spike.

        Simulates sudden doubling of traffic.
        """
        baseline_rps = 100
        spike_multiplier = 2
        baseline_duration = 10
        spike_duration = 5

        # Baseline load
        print(f"\nBaseline phase ({baseline_rps} RPS)...")
        baseline_requests = 0
        baseline_start = time.time()

        while time.time() - baseline_start < baseline_duration:
            await gateway_client.route(
                messages=sample_messages, strategy=RoutingStrategy.BALANCED
            )
            baseline_requests += 1
            await asyncio.sleep(1.0 / baseline_rps)

        baseline_actual_rps = baseline_requests / baseline_duration

        # Spike load
        print(f"Spike phase ({baseline_rps * spike_multiplier} RPS)...")

        async def make_request():
            try:
                return await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )
            except Exception as e:
                return e

        spike_count = int(baseline_rps * spike_multiplier * spike_duration)
        spike_start = time.time()
        spike_results = await concurrent_executor(
            make_request, count=spike_count, concurrency=spike_count // 5
        )
        spike_duration_actual = time.time() - spike_start

        spike_success_rate = success_rate_calculator(spike_results)
        spike_actual_rps = spike_count / spike_duration_actual

        print(f"\nTraffic Spike Results:")
        print(f"  Baseline RPS: {baseline_actual_rps:.2f}")
        print(f"  Spike RPS: {spike_actual_rps:.2f}")
        print(f"  Spike Success Rate: {spike_success_rate:.1%}")
        print(f"  Spike Duration: {spike_duration_actual:.2f}s")

        # Should handle spike gracefully
        assert (
            spike_success_rate >= 0.90
        ), f"Low success during spike: {spike_success_rate:.1%}"

    async def test_gradual_ramp_up(
        self, gateway_client, sample_messages, success_rate_calculator
    ):
        """Test gradual traffic ramp-up.

        Increases load from 10 to 500 RPS over 30 seconds.
        """
        ramp_duration = 30
        start_rps = 10
        end_rps = 500

        total_requests = 0
        errors = []

        start_time = time.time()
        end_time = start_time + ramp_duration

        while time.time() < end_time:
            # Calculate current target RPS based on time
            elapsed = time.time() - start_time
            progress = elapsed / ramp_duration
            current_target_rps = start_rps + (end_rps - start_rps) * progress

            request_start = time.time()

            try:
                await gateway_client.route(
                    messages=sample_messages, strategy=RoutingStrategy.BALANCED
                )
                total_requests += 1
            except Exception as e:
                errors.append(e)

            # Rate limiting
            interval = 1.0 / current_target_rps
            sleep_time = max(0, interval - (time.time() - request_start))
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        success_rate = (
            (total_requests - len(errors)) / total_requests
            if total_requests > 0
            else 0
        )
        actual_duration = time.time() - start_time
        average_rps = total_requests / actual_duration

        print(f"\nGradual Ramp-up:")
        print(f"  Total Requests: {total_requests}")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Average RPS: {average_rps:.2f}")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  Errors: {len(errors)}")

        # Should handle ramp-up well
        assert success_rate >= 0.95, f"Low success during ramp: {success_rate:.1%}"
