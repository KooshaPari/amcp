"""Rate limiting using slowapi-inspired patterns."""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after:.2f}s"
        )


@dataclass
class RateLimitConfig:
    """
    Rate limit configuration.

    Args:
        rate: Number of requests allowed
        period: Time period in seconds
        burst: Maximum burst size (for token bucket)
    """

    rate: int
    period: float
    burst: Optional[int] = None


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens from rate limiter.

        Args:
            tokens: Number of tokens to acquire

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        pass

    @abstractmethod
    async def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False otherwise
        """
        pass

    @abstractmethod
    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get estimated wait time for tokens.

        Args:
            tokens: Number of tokens needed

        Returns:
            Wait time in seconds
        """
        pass


class TokenBucketLimiter(RateLimiter):
    """
    Token bucket rate limiter backed by slowapi.

    Allows bursts up to bucket capacity while maintaining
    average rate over time.

    Example:
        >>> limiter = TokenBucketLimiter(rate=100, period=60.0, burst=10)
        >>> await limiter.acquire()  # Acquire 1 token
        >>> # Request proceeds
    """

    def __init__(
        self,
        rate: int,
        period: float = 1.0,
        burst: Optional[int] = None,
    ):
        """
        Initialize token bucket limiter.

        Args:
            rate: Number of tokens per period
            period: Time period in seconds
            burst: Maximum burst size (defaults to rate)
        """
        self.rate = rate
        self.period = period
        self.burst = burst or rate

        # State
        self._tokens = float(self.burst)
        self._last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary."""
        with tracer.start_as_current_span(
            "rate_limiter.acquire"
        ) as span:
            span.set_attribute("rate_limiter.tokens_requested", tokens)

            while True:
                async with self._lock:
                    self._refill()

                    if self._tokens >= tokens:
                        self._tokens -= tokens
                        span.set_attribute(
                            "rate_limiter.tokens_remaining",
                            self._tokens,
                        )
                        return

                    wait_time = self.get_wait_time(tokens)
                    span.set_attribute(
                        "rate_limiter.wait_time_ms",
                        int(wait_time * 1000),
                    )

                await asyncio.sleep(wait_time)

    async def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without waiting."""
        async with self._lock:
            self._refill()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get estimated wait time for tokens."""
        if self._tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self._tokens
        return (tokens_needed / self.rate) * self.period

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_update

        tokens_to_add = (elapsed / self.period) * self.rate
        self._tokens = min(self.burst, self._tokens + tokens_to_add)
        self._last_update = now


class SlidingWindowLimiter(RateLimiter):
    """
    Sliding window rate limiter backed by slowapi.

    More accurate than fixed window, prevents burst at window boundaries.

    Example:
        >>> limiter = SlidingWindowLimiter(rate=100, period=60.0)
        >>> if await limiter.try_acquire():
        >>>     # Request proceeds
        >>> else:
        >>>     # Rate limited
    """

    def __init__(self, rate: int, period: float = 1.0):
        """
        Initialize sliding window limiter.

        Args:
            rate: Maximum requests per period
            period: Time window in seconds
        """
        self.rate = rate
        self.period = period

        self._requests: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary."""
        with tracer.start_as_current_span(
            "rate_limiter.sliding_window.acquire"
        ) as span:
            span.set_attribute("rate_limiter.tokens_requested", tokens)

            while True:
                async with self._lock:
                    self._cleanup()

                    if len(self._requests) + tokens <= self.rate:
                        now = time.time()
                        for _ in range(tokens):
                            self._requests.append(now)
                        span.set_attribute(
                            "rate_limiter.requests_in_window",
                            len(self._requests),
                        )
                        return

                    wait_time = self.get_wait_time(tokens)
                    span.set_attribute(
                        "rate_limiter.wait_time_ms",
                        int(wait_time * 1000),
                    )

                await asyncio.sleep(wait_time)

    async def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without waiting."""
        async with self._lock:
            self._cleanup()

            if len(self._requests) + tokens <= self.rate:
                now = time.time()
                for _ in range(tokens):
                    self._requests.append(now)
                return True

            return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get estimated wait time for tokens."""
        if (
            not self._requests
            or len(self._requests) + tokens <= self.rate
        ):
            return 0.0

        oldest = self._requests[0]
        wait_until = oldest + self.period
        return max(0.0, wait_until - time.time())

    def _cleanup(self) -> None:
        """Remove expired request timestamps."""
        now = time.time()
        cutoff = now - self.period

        while self._requests and self._requests[0] < cutoff:
            self._requests.pop(0)


async def with_rate_limit(
    limiter: RateLimiter,
    func: callable,
    *args,
    **kwargs,
):
    """
    Execute function with rate limiting.

    Args:
        limiter: Rate limiter instance
        func: Async function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Result of function call

    Example:
        >>> limiter = TokenBucketLimiter(rate=10, period=1.0)
        >>> result = await with_rate_limit(
        >>>     limiter,
        >>>     api_client.get,
        >>>     "/endpoint"
        >>> )
    """
    await limiter.acquire()
    return await func(*args, **kwargs)
