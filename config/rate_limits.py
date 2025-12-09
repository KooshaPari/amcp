"""Rate limiting and throttling configuration.

Consolidates hardcoded rate limits, request quotas, and token bucket settings
from config, auth, and resilience modules.
"""

from dataclasses import dataclass


@dataclass
class RequestRateLimits:
    """HTTP request rate limiting settings."""

    # Default requests per minute
    DEFAULT_REQUESTS_PER_MINUTE: int = 100

    # API-specific rate limits
    API_REQUESTS_PER_MINUTE: int = 100
    BIFROST_REQUESTS_PER_MINUTE: int = 100

    # User-level limits
    USER_REQUESTS_PER_MINUTE: int = 60
    GUEST_REQUESTS_PER_MINUTE: int = 10

    # Endpoint-specific limits
    CHAT_REQUESTS_PER_MINUTE: int = 30
    EXECUTE_REQUESTS_PER_MINUTE: int = 20
    SEARCH_REQUESTS_PER_MINUTE: int = 60


@dataclass
class TokenBucketConfig:
    """Token bucket rate limiter configuration."""

    # Tokens per second (refill rate)
    REFILL_RATE: float = 100.0 / 60.0  # 100 per minute

    # Capacity (max tokens in bucket)
    CAPACITY: int = 100

    # Cost per request (in tokens)
    DEFAULT_COST: int = 1
    WRITE_OPERATION_COST: int = 2
    EXPENSIVE_OPERATION_COST: int = 5


@dataclass
class SlidingWindowConfig:
    """Sliding window rate limiter configuration."""

    # Window duration in seconds
    WINDOW_DURATION: int = 60

    # Max requests in window
    DEFAULT_MAX_REQUESTS: int = 100

    # Cleanup interval (remove old requests)
    CLEANUP_INTERVAL: int = 300


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration for resilience."""

    # Failure threshold (percentage)
    FAILURE_THRESHOLD: float = 50.0

    # Minimum requests before triggering
    MIN_REQUESTS: int = 5

    # Recovery timeout (in seconds)
    RECOVERY_TIMEOUT: int = 60

    # Success threshold to close circuit
    SUCCESS_THRESHOLD: int = 2


@dataclass
class BackoffConfig:
    """Exponential backoff configuration."""

    # Multiplier for each retry
    MULTIPLIER: float = 2.0

    # Initial delay (in seconds)
    INITIAL_DELAY: float = 1.0

    # Maximum delay (in seconds)
    MAX_DELAY: float = 60.0

    # Jitter: add random delay up to jitter * delay
    JITTER_FACTOR: float = 0.1


@dataclass
class ConcurrencyLimits:
    """Concurrency and parallelism limits."""

    # Default concurrent requests
    DEFAULT_MAX_CONCURRENT: int = 10

    # Per-user concurrent limits
    USER_MAX_CONCURRENT: int = 5
    GUEST_MAX_CONCURRENT: int = 2

    # Per-operation limits
    EMBEDDING_MAX_CONCURRENT: int = 5
    SEARCH_MAX_CONCURRENT: int = 10
    EXECUTION_MAX_CONCURRENT: int = 3


@dataclass
class QuotaConfig:
    """Per-user quotas and allowances."""

    # Daily request quota
    DAILY_REQUEST_QUOTA: int = 10_000

    # Monthly token quota (for models with usage metering)
    MONTHLY_TOKEN_QUOTA: int = 10_000_000

    # Storage quota (in bytes)
    STORAGE_QUOTA_BYTES: int = 1_073_741_824  # 1GB

    # Memory entries per user
    MEMORY_ENTRIES_PER_USER: int = 10_000

    # Learning patterns per user
    LEARNING_PATTERNS_PER_USER: int = 1_000


# Convenience instances
request_limits = RequestRateLimits()
token_bucket = TokenBucketConfig()
sliding_window = SlidingWindowConfig()
circuit_breaker = CircuitBreakerConfig()
backoff = BackoffConfig()
concurrency = ConcurrencyLimits()
quotas = QuotaConfig()
