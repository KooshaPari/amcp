"""Default timeout and duration settings across the codebase.

Consolidates hardcoded timeouts, sleep durations, and retry intervals
from services, tools, and extensions.
"""

from dataclasses import dataclass


@dataclass
class ExecutionDefaults:
    """Code execution sandbox timeout settings (in seconds)."""

    # Default execution timeout
    DEFAULT_TIMEOUT: int = 30

    # Min/max execution time bounds
    MIN_TIMEOUT: int = 1
    MAX_TIMEOUT: int = 300

    # Memory limits
    DEFAULT_MAX_MEMORY_MB: int = 512
    MIN_MEMORY_MB: int = 64
    MAX_MEMORY_MB: int = 4096

    # Output limits
    DEFAULT_MAX_OUTPUT_BYTES: int = 1_048_576  # 1MB
    MIN_OUTPUT_BYTES: int = 1024
    MAX_OUTPUT_BYTES: int = 104_857_600  # 100MB


@dataclass
class CacheDefaults:
    """Cache TTL and size defaults."""

    # Default cache TTL (in seconds)
    DEFAULT_TTL: int = 300  # 5 minutes

    # Cache size limits
    DEFAULT_MAX_SIZE: int = 1000
    MIN_SIZE: int = 10
    MAX_SIZE: int = 100_000

    # Default pool size for connections
    DEFAULT_POOL_SIZE: int = 10
    MIN_POOL_SIZE: int = 1
    MAX_POOL_SIZE: int = 100


@dataclass
class RateLimitDefaults:
    """Rate limiting durations and windows."""

    # Requests per minute (default)
    DEFAULT_REQUESTS_PER_MINUTE: int = 100

    # Sliding window duration (in seconds)
    WINDOW_DURATION: int = 60

    # Token bucket refill rate
    TOKEN_REFILL_RATE: float = 1.0  # tokens per second


@dataclass
class RetryDefaults:
    """Retry and backoff settings."""

    # Maximum number of retries
    MAX_RETRIES: int = 3

    # Exponential backoff multiplier
    BACKOFF_MULTIPLIER: float = 2.0

    # Initial backoff delay (in seconds)
    INITIAL_BACKOFF: float = 1.0

    # Maximum backoff delay (in seconds)
    MAX_BACKOFF: float = 60.0


@dataclass
class HealthCheckDefaults:
    """Health check and probe settings."""

    # Health check timeout (in seconds)
    TIMEOUT: float = 5.0

    # Health check probe interval (in seconds)
    INTERVAL: int = 30


@dataclass
class QueryDefaults:
    """Database query defaults."""

    # Default query timeout (in seconds)
    TIMEOUT: int = 30

    # Min/max query time bounds
    MIN_TIMEOUT: int = 1
    MAX_TIMEOUT: int = 300

    # Pagination defaults
    DEFAULT_LIMIT: int = 20
    MAX_LIMIT: int = 100


# Convenience instances
execution = ExecutionDefaults()
cache = CacheDefaults()
rate_limit = RateLimitDefaults()
retry = RetryDefaults()
health_check = HealthCheckDefaults()
query = QueryDefaults()
