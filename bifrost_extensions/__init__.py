"""
Bifrost Extensions SDK - Smart LLM Gateway

Production-grade SDK for intelligent model routing, tool routing,
classification, and cost optimization.

Unified client from infrastructure.bifrost with backward compatibility aliases.

Public API:
    - GatewayClient: Main client for routing operations
    - BifrostClient: Unified client (GraphQL, HTTP, WebSocket)
    - RoutingStrategy: Routing optimization strategies
    - Models: Request/response data models

Example:
    >>> from bifrost_extensions import GatewayClient, RoutingStrategy
    >>>
    >>> client = GatewayClient()
    >>> response = await client.route(
    ...     messages=[{"role": "user", "content": "Analyze this code"}],
    ...     strategy=RoutingStrategy.COST_OPTIMIZED
    ... )
"""

__version__ = "2.0.0"
__author__ = "SmartCP Team"
__license__ = "MIT"

# Import unified client from infrastructure
from infrastructure.bifrost import (
    BifrostClient,
    BifrostClientConfig,
    HTTPClient,
    BifrostHTTPClient,
    ProductionGatewayClient,
    BifrostError,
    RateLimitError,
    CircuitBreakerError,
    TimeoutError as BifrostTimeoutError,
    ValidationError as BifrostValidationError,
)

# Import gateway client
from bifrost_extensions.client.gateway import GatewayClient
from bifrost_extensions.models import (
    RoutingStrategy,
    RoutingRequest,
    RoutingResponse,
    ToolRoutingRequest,
    ToolRoutingDecision,
    ClassificationRequest,
    ClassificationResult,
)
from bifrost_extensions.exceptions import (
    RoutingError,
    ValidationError,
    TimeoutError,
)

__all__ = [
    # Core unified client
    "BifrostClient",
    "BifrostClientConfig",
    # Gateway client (orchestration)
    "GatewayClient",
    # Backward compatibility aliases
    "HTTPClient",
    "BifrostHTTPClient",
    "ProductionGatewayClient",
    # Models
    "RoutingStrategy",
    "RoutingRequest",
    "RoutingResponse",
    "ToolRoutingRequest",
    "ToolRoutingDecision",
    "ClassificationRequest",
    "ClassificationResult",
    # Exceptions (unified + legacy)
    "BifrostError",
    "RateLimitError",
    "CircuitBreakerError",
    "BifrostTimeoutError",
    "BifrostValidationError",
    "RoutingError",
    "ValidationError",
    "TimeoutError",
]
