"""HTTP client for Bifrost API with retry and resilience patterns."""

from typing import Any, Dict, List, Optional

import httpx
from opentelemetry import trace
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bifrost_extensions.exceptions import (
    AuthenticationError,
    RateLimitError,
    RoutingError,
    TimeoutError,
)
from bifrost_extensions.models import (
    ClassificationResult,
    ModelInfo,
    RoutingResponse,
    ToolRoutingDecision,
    UsageStats,
)

tracer = trace.get_tracer(__name__)


class HTTPClient:
    """
    Async HTTP client for Bifrost API with built-in retry and resilience.

    Features:
    - Automatic exponential backoff retries via tenacity
    - Connection pooling and timeout management
    - OpenTelemetry tracing integration
    - Structured error handling and mapping

    Args:
        base_url: Base URL for Bifrost API
        api_key: API key for authentication
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts (default 3)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    async def close(self):
        """Close HTTP client and cleanup resources."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with automatic retry via tenacity.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json: JSON request body
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
            RoutingError: If request fails
            TimeoutError: If request times out
        """
        try:
            response = await self._client.request(
                method=method,
                url=endpoint,
                json=json,
                params=params,
                headers=self._get_headers(),
            )

            # Handle HTTP errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "60"))
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after_seconds=retry_after,
                    limit_type="requests",
                )
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("detail", f"HTTP {response.status_code}")
                raise RoutingError(f"Request failed: {error_msg}")

            return response.json()

        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"Request timed out after {self.timeout}s",
                timeout_ms=int(self.timeout * 1000),
            ) from e
        except httpx.RequestError as e:
            raise RoutingError(f"Request failed: {e}") from e

    @tracer.start_as_current_span("http_client.route")
    async def route(
        self,
        messages: List[Dict[str, str]],
        strategy: str = "balanced",
        constraints: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingResponse:
        """
        Route request to optimal model via HTTP API.

        Args:
            messages: Conversation messages
            strategy: Routing strategy
            constraints: Optional constraints
            context: Optional context

        Returns:
            Routing response with selected model
        """
        span = trace.get_current_span()
        span.set_attribute("routing.strategy", strategy)
        span.set_attribute("routing.message_count", len(messages))

        response_data = await self._request(
            method="POST",
            endpoint="/v1/route",
            json={
                "messages": messages,
                "strategy": strategy,
                "constraints": constraints,
                "context": context,
            },
        )

        model_data = response_data["model"]
        return RoutingResponse(
            model=ModelInfo(
                model_id=model_data["model_id"],
                provider=model_data["provider"],
                estimated_cost_usd=model_data.get("estimated_cost_usd"),
                estimated_latency_ms=model_data.get("estimated_latency_ms"),
            ),
            confidence=response_data["confidence"],
            reasoning=response_data.get("reasoning"),
        )

    @tracer.start_as_current_span("http_client.route_tool")
    async def route_tool(
        self,
        action: str,
        available_tools: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> ToolRoutingDecision:
        """
        Route action to optimal tool via HTTP API.

        Args:
            action: Action description
            available_tools: Available tool names
            context: Optional context

        Returns:
            Tool routing decision
        """
        response_data = await self._request(
            method="POST",
            endpoint="/v1/route-tool",
            json={
                "action": action,
                "available_tools": available_tools,
                "context": context,
            },
        )

        return ToolRoutingDecision(
            recommended_tool=response_data["recommended_tool"],
            confidence=response_data["confidence"],
            reasoning=response_data.get("reasoning"),
        )

    @tracer.start_as_current_span("http_client.classify")
    async def classify(
        self, prompt: str, categories: Optional[List[str]] = None
    ) -> ClassificationResult:
        """
        Classify prompt via HTTP API.

        Args:
            prompt: Prompt to classify
            categories: Optional target categories

        Returns:
            Classification result
        """
        response_data = await self._request(
            method="POST",
            endpoint="/v1/classify",
            json={"prompt": prompt, "categories": categories},
        )

        return ClassificationResult(
            category=response_data["category"],
            confidence=response_data["confidence"],
            complexity=response_data["complexity"],
        )

    @tracer.start_as_current_span("http_client.get_usage")
    async def get_usage(
        self, start_date: str, end_date: str, group_by: str = "model"
    ) -> UsageStats:
        """
        Get usage statistics via HTTP API.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            group_by: Grouping dimension

        Returns:
            Usage statistics
        """
        response_data = await self._request(
            method="GET",
            endpoint="/v1/usage",
            params={"start_date": start_date, "end_date": end_date, "group_by": group_by},
        )

        return UsageStats(
            total_requests=response_data["total_requests"],
            total_cost_usd=response_data["total_cost_usd"],
            avg_latency_ms=response_data["avg_latency_ms"],
            requests_by_model=response_data.get("requests_by_model", {}),
            cost_by_model=response_data.get("cost_by_model", {}),
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check API health.

        Returns:
            Health status
        """
        return await self._request(method="GET", endpoint="/health")


# Backwards compatibility alias
BifrostHTTPClient = HTTPClient
