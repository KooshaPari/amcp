"""Tests for resilience patterns."""

import pytest

# Skip module if dependencies are not installed
pytest.importorskip("pybreaker")

import asyncio
import time

from bifrost_extensions.resilience.retry import (
    RetryPolicy,
    retry_with_backoff,
)
from bifrost_extensions.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
)
from bifrost_extensions.resilience.rate_limiter import (
    TokenBucketLimiter,
    SlidingWindowLimiter,
    RateLimitExceeded,
)


class TestRetry:
    """Test retry logic with exponential backoff via tenacity."""

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test successful operation on first attempt."""
        call_count = 0

        @retry_with_backoff(RetryPolicy(max_retries=3))
        async def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_operation()

        assert result == "success"
        assert call_count == 1  # No retries needed

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry succeeds after transient failures."""
        call_count = 0

        @retry_with_backoff(
            RetryPolicy(
                max_retries=3,
                initial_delay=0.01,  # Fast retry for testing
            )
        )
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Transient error")
            return "success"

        result = await flaky_operation()

        assert result == "success"
        assert call_count == 3  # Failed twice, succeeded on 3rd

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test retry exhaustion after max attempts."""

        @retry_with_backoff(
            RetryPolicy(
                max_retries=2,
                initial_delay=0.01,
            )
        )
        async def always_fails():
            raise RuntimeError("Permanent error")

        with pytest.raises(RuntimeError, match="Permanent error"):
            await always_fails()


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    @pytest.mark.asyncio
    async def test_closed_state_allows_requests(self):
        """Test circuit allows requests in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=5, timeout=60.0)

        assert breaker.state == CircuitState.CLOSED

        # Should succeed
        result = await breaker.call(lambda: asyncio.sleep(0.001))
        assert result is None

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        """Test circuit opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=60.0)

        # Cause failures
        for i in range(3):
            with pytest.raises(RuntimeError):
                await breaker.call(
                    lambda: (_ for _ in ()).throw(RuntimeError("Error"))
                )

        # Circuit should now be OPEN
        assert breaker.state == CircuitState.OPEN

        # Next request should be rejected immediately
        with pytest.raises(CircuitBreakerError) as exc_info:
            await breaker.call(lambda: asyncio.sleep(0.001))

        assert exc_info.value.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_half_open_on_timeout(self):
        """Test circuit transitions to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            timeout=0.1,  # Short timeout for testing
        )

        # Open circuit
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await breaker.call(
                    lambda: (_ for _ in ()).throw(RuntimeError("Error"))
                )

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Should transition to HALF_OPEN on next call
        await breaker.call(lambda: asyncio.sleep(0.001))

        # After success in HALF_OPEN, might close or stay half-open
        assert breaker.state in [CircuitState.HALF_OPEN, CircuitState.CLOSED]

    @pytest.mark.asyncio
    async def test_closes_after_success_threshold(self):
        """Test circuit closes after success threshold in HALF_OPEN."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1,
        )

        # Open circuit
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await breaker.call(
                    lambda: (_ for _ in ()).throw(RuntimeError("Error"))
                )

        # Wait for timeout
        await asyncio.sleep(0.15)

        # First success transitions to HALF_OPEN
        await breaker.call(lambda: asyncio.sleep(0.001))

        # Second success should close circuit
        await breaker.call(lambda: asyncio.sleep(0.001))

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestRateLimiter:
    """Test rate limiting patterns."""

    @pytest.mark.asyncio
    async def test_token_bucket_allows_within_limit(self):
        """Test token bucket allows requests within limit."""
        limiter = TokenBucketLimiter(rate=10, period=1.0)

        # Should acquire 5 tokens immediately
        for _ in range(5):
            await limiter.acquire(1)

    @pytest.mark.asyncio
    async def test_token_bucket_refills_over_time(self):
        """Test token bucket refills tokens."""
        limiter = TokenBucketLimiter(rate=10, period=0.1, burst=10)

        # Drain bucket
        for _ in range(10):
            await limiter.acquire(1)

        # Wait for refill (0.1s = 10 tokens)
        await asyncio.sleep(0.15)

        # Should have tokens again
        assert await limiter.try_acquire(5) is True

    @pytest.mark.asyncio
    async def test_token_bucket_burst_capacity(self):
        """Test token bucket allows burst."""
        limiter = TokenBucketLimiter(rate=10, period=1.0, burst=20)

        # Should allow burst up to 20
        assert await limiter.try_acquire(20) is True

        # But not more
        assert await limiter.try_acquire(1) is False

    @pytest.mark.asyncio
    async def test_sliding_window_enforces_limit(self):
        """Test sliding window enforces rate limit."""
        limiter = SlidingWindowLimiter(rate=5, period=0.1)

        # Allow 5 requests
        for _ in range(5):
            assert await limiter.try_acquire() is True

        # 6th should fail
        assert await limiter.try_acquire() is False

    @pytest.mark.asyncio
    async def test_sliding_window_releases_old_requests(self):
        """Test sliding window releases old timestamps."""
        limiter = SlidingWindowLimiter(rate=3, period=0.1)

        # Use up limit
        for _ in range(3):
            await limiter.acquire()

        # Wait for window to slide
        await asyncio.sleep(0.15)

        # Should have capacity again
        assert await limiter.try_acquire(3) is True

    @pytest.mark.asyncio
    async def test_rate_limiter_wait_time(self):
        """Test rate limiter calculates wait time."""
        limiter = TokenBucketLimiter(rate=10, period=1.0)

        # Drain tokens
        for _ in range(10):
            await limiter.acquire()

        # Should need to wait ~1 second for 10 tokens
        wait_time = limiter.get_wait_time(10)
        assert 0.9 <= wait_time <= 1.1


class TestIntegration:
    """Integration tests for combined resilience patterns."""

    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker(self):
        """Test retry combined with circuit breaker."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1.0)
        call_count = 0

        @retry_with_backoff(
            RetryPolicy(max_retries=5, initial_delay=0.01)
        )
        async def operation_with_breaker():
            nonlocal call_count
            call_count += 1

            async with breaker:
                if call_count < 2:
                    raise RuntimeError("Fail")
                return "success"

        result = await operation_with_breaker()

        assert result == "success"
        assert call_count == 2
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_all_patterns_combined(self):
        """Test retry + circuit breaker + rate limiting."""
        breaker = CircuitBreaker(failure_threshold=5)
        limiter = TokenBucketLimiter(rate=10, period=0.1)

        @retry_with_backoff(RetryPolicy(max_retries=3, initial_delay=0.01))
        async def resilient_operation():
            # Rate limit
            await limiter.acquire()

            # Circuit breaker
            async with breaker:
                # Simulated operation
                await asyncio.sleep(0.001)
                return "success"

        # Should succeed with all patterns active
        result = await resilient_operation()
        assert result == "success"
