"""Example integration test to validate test structure.

This file demonstrates the test structure and can be run independently
to verify the test infrastructure is working correctly.

Run with:
    pytest tests/integration/test_example.py -v
"""

import pytest
import asyncio
import time


class TestExampleBasic:
    """Basic test examples."""

    def test_simple_assertion(self):
        """Test simple assertion works."""
        assert 1 + 1 == 2

    def test_string_assertion(self):
        """Test string comparison works."""
        result = "hello world"
        assert "hello" in result
        assert result.startswith("hello")

    def test_list_assertion(self):
        """Test list operations work."""
        items = [1, 2, 3, 4, 5]
        assert len(items) == 5
        assert 3 in items
        assert items[0] == 1


class TestExampleAsync:
    """Async test examples."""

    @pytest.mark.asyncio
    async def test_async_basic(self):
        """Test basic async function."""
        async def async_func():
            await asyncio.sleep(0.01)
            return "result"

        result = await async_func()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_async_timeout(self):
        """Test async timeout handling."""
        async def slow_func():
            await asyncio.sleep(0.1)
            return "done"

        # Should complete within timeout
        result = await asyncio.wait_for(slow_func(), timeout=1.0)
        assert result == "done"

    @pytest.mark.asyncio
    async def test_async_concurrent(self):
        """Test concurrent async execution."""
        async def task(n):
            await asyncio.sleep(0.01)
            return n * 2

        tasks = [task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert results[5] == 10  # 5 * 2


class TestExamplePerformance:
    """Performance test examples."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_latency_measurement(self):
        """Test latency measurement."""
        async def fast_func():
            await asyncio.sleep(0.001)  # 1ms
            return "result"

        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            await fast_func()
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        latencies.sort()
        p50 = latencies[49]
        p95 = latencies[94]

        print(f"\nLatency - P50: {p50:.2f}ms, P95: {p95:.2f}ms")

        # Should be fast
        assert p95 < 50, f"P95 latency {p95:.2f}ms too high"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_throughput(self):
        """Test concurrent throughput."""
        async def task():
            await asyncio.sleep(0.01)
            return "done"

        tasks = [task() for _ in range(100)]
        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        duration = time.perf_counter() - start

        throughput = 100 / duration

        print(f"\nThroughput: {throughput:.2f} ops/sec")

        assert len(results) == 100
        assert all(r == "done" for r in results)


class TestExampleErrorHandling:
    """Error handling test examples."""

    def test_exception_raised(self):
        """Test exception is raised."""
        with pytest.raises(ValueError, match="invalid value"):
            raise ValueError("invalid value")

    @pytest.mark.asyncio
    async def test_async_exception(self):
        """Test async exception handling."""
        async def failing_func():
            raise RuntimeError("operation failed")

        with pytest.raises(RuntimeError, match="operation failed"):
            await failing_func()

    @pytest.mark.asyncio
    async def test_timeout_exception(self):
        """Test timeout exception."""
        async def slow_func():
            await asyncio.sleep(10)
            return "too slow"

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_func(), timeout=0.1)


class TestExampleParametrized:
    """Parametrized test examples."""

    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
        (5, 10),
    ])
    def test_multiply_by_two(self, input, expected):
        """Test multiplication is correct."""
        assert input * 2 == expected

    @pytest.mark.parametrize("strategy", [
        "strategy_a",
        "strategy_b",
        "strategy_c",
    ])
    def test_all_strategies(self, strategy):
        """Test all strategies work."""
        result = f"Using {strategy}"
        assert strategy in result


class TestExampleFixtures:
    """Fixture usage examples."""

    @pytest.fixture
    def sample_data(self):
        """Provide sample data for tests."""
        return {"key": "value", "count": 42}

    @pytest.fixture
    def sample_list(self):
        """Provide sample list for tests."""
        return [1, 2, 3, 4, 5]

    def test_with_fixture(self, sample_data):
        """Test using fixture."""
        assert sample_data["key"] == "value"
        assert sample_data["count"] == 42

    def test_with_multiple_fixtures(self, sample_data, sample_list):
        """Test using multiple fixtures."""
        assert len(sample_list) == 5
        assert sample_data["count"] > len(sample_list)


@pytest.mark.slow
class TestExampleSlow:
    """Slow test examples (skip with -m "not slow")."""

    @pytest.mark.asyncio
    async def test_slow_operation(self):
        """Test slow operation (>1s)."""
        await asyncio.sleep(1.0)
        assert True

    @pytest.mark.asyncio
    async def test_many_iterations(self):
        """Test many iterations."""
        results = []
        for i in range(1000):
            await asyncio.sleep(0.001)
            results.append(i)

        assert len(results) == 1000


if __name__ == "__main__":
    # Run this file directly for quick validation
    pytest.main([__file__, "-v", "-s"])
