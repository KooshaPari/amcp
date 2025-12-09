"""SmartCP configuration module.

Provides centralized configuration for:
- Bifrost API endpoints and timeouts
- Default timeouts, durations, and cache settings
- AI model names and context windows
- Rate limits, quotas, and resilience settings

All hardcoded configuration values have been extracted from production code
into this module for easier maintenance and consistency.

Usage:
    from config.bifrost import endpoints, timeouts
    from config.defaults import execution, cache
    from config.models import claude, gemini
    from config.rate_limits import request_limits

Example:
    >>> from config.bifrost import timeouts
    >>> timeout = timeouts.get_default()
    >>> 30.0

    >>> from config.models import get_context_window
    >>> window = get_context_window("claude-opus")
    >>> 200000
"""

# Bifrost configuration
from config.bifrost import (
    BifrostAuth,
    BifrostConnections,
    BifrostEndpoints,
    BifrostTimeouts,
    auth,
    connections,
    endpoints,
    timeouts,
)

# Default timeouts and durations
from config.defaults import (
    CacheDefaults,
    ExecutionDefaults,
    HealthCheckDefaults,
    QueryDefaults,
    RateLimitDefaults,
    RetryDefaults,
    cache,
    execution,
    health_check,
    query,
    retry,
)

# Model names and capabilities
from config.models import (
    ClaudeModels,
    EmbeddingModels,
    GeminiModels,
    ModelCapabilities,
    ModelContextWindows,
    ModelProvider,
    OpenAIModels,
    capabilities,
    claude,
    context_windows,
    embeddings,
    gemini,
    get_context_window,
    get_model_provider,
    openai,
)

# Rate limits and quotas
from config.rate_limits import (
    BackoffConfig,
    CircuitBreakerConfig,
    ConcurrencyLimits,
    QuotaConfig,
    RequestRateLimits,
    SlidingWindowConfig,
    TokenBucketConfig,
    backoff,
    circuit_breaker,
    concurrency,
    quotas,
    request_limits,
    sliding_window,
    token_bucket,
)

__all__ = [
    # Bifrost
    "BifrostAuth",
    "BifrostConnections",
    "BifrostEndpoints",
    "BifrostTimeouts",
    "auth",
    "connections",
    "endpoints",
    "timeouts",
    # Defaults
    "CacheDefaults",
    "ExecutionDefaults",
    "HealthCheckDefaults",
    "QueryDefaults",
    "RateLimitDefaults",
    "RetryDefaults",
    "cache",
    "execution",
    "health_check",
    "query",
    "retry",
    # Models
    "ClaudeModels",
    "EmbeddingModels",
    "GeminiModels",
    "ModelCapabilities",
    "ModelContextWindows",
    "ModelProvider",
    "OpenAIModels",
    "capabilities",
    "claude",
    "context_windows",
    "embeddings",
    "gemini",
    "get_context_window",
    "get_model_provider",
    "openai",
    # Rate Limits
    "BackoffConfig",
    "CircuitBreakerConfig",
    "ConcurrencyLimits",
    "QuotaConfig",
    "RequestRateLimits",
    "SlidingWindowConfig",
    "TokenBucketConfig",
    "backoff",
    "circuit_breaker",
    "concurrency",
    "quotas",
    "request_limits",
    "sliding_window",
    "token_bucket",
]
