"""
Bifrost Extensions SDK - Smart LLM Gateway

Production-grade SDK for intelligent model routing, tool routing,
classification, and cost optimization.

Public API:
    - GatewayClient: Main client for routing operations
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

__version__ = "1.0.0"
__author__ = "SmartCP Team"
__license__ = "MIT"

from bifrost_extensions.client.gateway import GatewayClient
from bifrost_extensions.http_client import HTTPClient, BifrostHTTPClient
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
    BifrostError,
    RoutingError,
    ValidationError,
    TimeoutError,
)

__all__ = [
    # Client
    "GatewayClient",
    # HTTP Client
    "HTTPClient",
    "BifrostHTTPClient",
    # Models
    "RoutingStrategy",
    "RoutingRequest",
    "RoutingResponse",
    "ToolRoutingRequest",
    "ToolRoutingDecision",
    "ClassificationRequest",
    "ClassificationResult",
    # Exceptions
    "BifrostError",
    "RoutingError",
    "ValidationError",
    "TimeoutError",
]
