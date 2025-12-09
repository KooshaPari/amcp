"""Unified Bifrost client module.

Consolidated client supporting GraphQL, HTTP APIs, WebSocket subscriptions,
and full resilience patterns (retry, circuit breaker, rate limiting).

Backward compatibility: Provides aliases for legacy imports.
"""

from .client import (
    BifrostClient,
    BifrostClientConfig,
    BifrostError,
    RateLimitError,
    CircuitBreakerError,
    TimeoutError,
    ValidationError,
    CircuitBreakerState,
    TokenBucketLimiter,
)
from .errors import ConnectionError, GraphQLError
from .queries import QueryBuilder, QueryProcessor, RoutingDecision, SearchResult, ToolMetadata
from .mutations import MutationBuilder, MutationFactory, MutationProcessor
from .subscriptions import SubscriptionBuilder, SubscriptionVariables

# Backward compatibility aliases for legacy code
HTTPClient = BifrostClient
BifrostHTTPClient = BifrostClient
ProductionGatewayClient = BifrostClient
GraphQLSubscriptionClient = BifrostClient

__all__ = [
    # Core client
    "BifrostClient",
    "BifrostClientConfig",
    # Backward compatibility aliases
    "HTTPClient",
    "BifrostHTTPClient",
    "ProductionGatewayClient",
    "GraphQLSubscriptionClient",
    # Exceptions
    "BifrostError",
    "RateLimitError",
    "CircuitBreakerError",
    "TimeoutError",
    "ValidationError",
    "ConnectionError",
    "GraphQLError",
    # Resilience components (for advanced usage)
    "CircuitBreakerState",
    "TokenBucketLimiter",
    # GraphQL builders
    "QueryBuilder",
    "QueryProcessor",
    "MutationBuilder",
    "MutationFactory",
    "MutationProcessor",
    "SubscriptionBuilder",
    "SubscriptionVariables",
    # Response types
    "RoutingDecision",
    "SearchResult",
    "ToolMetadata",
]
