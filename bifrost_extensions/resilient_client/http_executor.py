"""HTTP request execution for Bifrost client."""

import httpx

from bifrost_extensions.models import RoutingRequest, RoutingResponse
from bifrost_extensions.exceptions import (
    TimeoutError,
    AuthenticationError,
    RoutingError,
)
from bifrost_extensions.resilience.rate_limiter import RateLimitExceeded


async def execute_routing(
    http_client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    request: RoutingRequest,
    timeout: float,
    request_id: str,
) -> RoutingResponse:
    """Execute routing HTTP request.

    Args:
        http_client: Configured HTTP client
        base_url: Bifrost API base URL
        api_key: API key for authentication
        request: Routing request data
        timeout: Request timeout in seconds
        request_id: Unique request ID for tracing

    Returns:
        RoutingResponse with selected model

    Raises:
        TimeoutError: Request timed out
        AuthenticationError: Invalid API key
        RoutingError: HTTP error occurred
        RateLimitExceeded: Rate limit exceeded
    """
    headers = {
        "X-API-Key": api_key,
        "X-Request-ID": request_id,
    }

    # Prepare payload
    payload = request.model_dump(mode="json")

    # Make HTTP request
    try:
        response = await http_client.post(
            f"{base_url}/v1/route",
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()

        data = response.json()
        return RoutingResponse(**data)

    except httpx.TimeoutException:
        raise TimeoutError(
            f"Request timed out after {timeout}s",
            timeout_ms=int(timeout * 1000),
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif e.response.status_code == 429:
            retry_after = float(
                e.response.headers.get("Retry-After", "60")
            )
            raise RateLimitExceeded(retry_after)
        else:
            raise RoutingError(
                f"HTTP {e.response.status_code}: {e.response.text}"
            )
