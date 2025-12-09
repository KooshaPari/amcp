"""
Bifrost Smart LLM Gateway Client - Main orchestration.

Provides intelligent model routing, tool routing, classification,
and cost optimization for LLM applications.
"""

import os
from datetime import date
from typing import Optional, Dict, Any, List

from opentelemetry import trace

from bifrost_extensions.models import (
    RoutingStrategy,
    RoutingResponse,
    ToolRoutingDecision,
    ClassificationResult,
    UsageStats,
)
from bifrost_extensions.client.internal_router import (
    initialize_internal_router,
)
from bifrost_extensions.client.routing import route
from bifrost_extensions.client.tools import route_tool
from bifrost_extensions.client.classification import classify

tracer = trace.get_tracer(__name__)


class GatewayClient:
    """
    Bifrost Smart LLM Gateway Client.

    Provides intelligent model routing, tool routing, classification,
    and cost optimization for LLM applications.

    Args:
        api_key: Bifrost API key. If not provided, reads from BIFROST_API_KEY env.
        base_url: Bifrost API base URL. Defaults to localhost.
        timeout: Request timeout in seconds. Defaults to 30.
        max_retries: Maximum retry attempts. Defaults to 3.

    Example:
        >>> from bifrost_extensions import GatewayClient, RoutingStrategy
        >>>
        >>> client = GatewayClient()
        >>> response = await client.route(
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     strategy=RoutingStrategy.COST_OPTIMIZED
        ... )
        >>> print(response.model.model_id)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        max_retries: int = 3,
        use_http: bool = False,
    ):
        """Initialize the Gateway Client."""
        self.api_key = api_key or os.getenv("BIFROST_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_http = use_http

        # Week 2+: HTTP client for API communication
        self._http_client = None
        if use_http:
            from bifrost_extensions.http_client import BifrostHTTPClient

            self._http_client = BifrostHTTPClient(
                base_url=base_url,
                api_key=self.api_key,
                timeout=timeout,
                max_retries=max_retries,
            )

        # Week 1 fallback: Internal router service (legacy)
        # TODO: Remove in Week 3 when HTTP is stable
        self._router = initialize_internal_router() if not use_http else None

    @tracer.start_as_current_span("gateway.route")
    async def route(
        self,
        messages: List[Any],
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        constraints: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> RoutingResponse:
        """
        Route request to optimal model.

        Args:
            messages: Conversation messages
            strategy: Routing optimization strategy
            constraints: Optional constraints (max cost, latency, etc.)
            context: Additional context for routing
            timeout: Optional timeout override

        Returns:
            RoutingResponse with selected model and metadata

        Raises:
            ValidationError: If request is invalid
            RoutingError: If routing fails
            TimeoutError: If operation times out
            AuthenticationError: If API key is invalid

        Example:
            >>> response = await client.route(
            ...     messages=[
            ...         {"role": "user", "content": "Write Python code"}
            ...     ],
            ...     strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
            ...     constraints={"max_latency_ms": 500}
            ... )
        """
        return await route(
            messages=messages,
            strategy=strategy,
            constraints=constraints,
            context=context,
            timeout=timeout,
            http_client=self._http_client,
            internal_router=self._router,
            default_timeout=self.timeout,
        )

    @tracer.start_as_current_span("gateway.route_tool")
    async def route_tool(
        self,
        action: str,
        available_tools: List[str],
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> ToolRoutingDecision:
        """
        Route action to optimal tool.

        Args:
            action: Action description (e.g., "search web")
            available_tools: List of available tool names
            context: Optional context for routing
            timeout: Optional timeout override

        Returns:
            ToolRoutingDecision with recommended tool

        Raises:
            ValidationError: If request is invalid
            RoutingError: If routing fails
            TimeoutError: If operation times out

        Example:
            >>> decision = await client.route_tool(
            ...     action="search for Python documentation",
            ...     available_tools=["web_search", "doc_search"]
            ... )
            >>> print(decision.recommended_tool)
        """
        return await route_tool(
            action=action,
            available_tools=available_tools,
            context=context,
            timeout=timeout,
            http_client=self._http_client,
            default_timeout=self.timeout,
        )

    @tracer.start_as_current_span("gateway.classify")
    async def classify(
        self,
        prompt: str,
        categories: Optional[List[str]] = None,
        timeout: Optional[float] = None,
    ) -> ClassificationResult:
        """
        Classify prompt.

        Args:
            prompt: Prompt to classify
            categories: Optional target categories (or auto-detect)
            timeout: Optional timeout override

        Returns:
            ClassificationResult with category and confidence

        Raises:
            ValidationError: If request is invalid
            RoutingError: If classification fails
            TimeoutError: If operation times out

        Example:
            >>> result = await client.classify(
            ...     prompt="Write a Python function to parse JSON",
            ...     categories=["simple", "moderate", "complex"]
            ... )
            >>> print(result.category)  # "simple"
        """
        return await classify(
            prompt=prompt,
            categories=categories,
            timeout=timeout,
            http_client=self._http_client,
            default_timeout=self.timeout,
        )

    @tracer.start_as_current_span("gateway.get_usage")
    async def get_usage(
        self,
        start_date: date | str,
        end_date: date | str,
        group_by: str = "model",
        timeout: Optional[float] = None,
    ) -> UsageStats:
        """
        Get usage statistics.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            group_by: Grouping dimension (model, provider, user)
            timeout: Optional timeout override

        Returns:
            UsageStats with aggregated metrics

        Example:
            >>> stats = await client.get_usage(
            ...     start_date="2025-12-01",
            ...     end_date="2025-12-02"
            ... )
            >>> print(f"Total cost: ${stats.total_cost_usd:.2f}")
        """
        if self._http_client:
            return await self._http_client.get_usage(
                start_date=str(start_date),
                end_date=str(end_date),
                group_by=group_by,
            )

        # TODO Week 3: Implement actual usage tracking
        # For now, placeholder
        return UsageStats(
            total_requests=0,
            total_cost_usd=0.0,
            avg_latency_ms=0.0,
            requests_by_model={},
            cost_by_model={},
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check SDK and routing service health.

        Returns:
            Health status dictionary

        Example:
            >>> health = await client.health_check()
            >>> print(health["status"])  # "healthy"
        """
        return {
            "status": "healthy",
            "version": "1.0.0",
            "router_available": self._router is not None,
        }
