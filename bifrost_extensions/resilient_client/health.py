"""Health check functionality for Bifrost client."""

from typing import Any, Dict

import httpx

from bifrost_extensions.resilience.circuit_breaker import CircuitBreaker


async def perform_health_check(
    base_url: str,
    http_client: httpx.AsyncClient,
    circuit_breaker: CircuitBreaker,
) -> Dict[str, Any]:
    """Check client and service health.

    Args:
        base_url: Bifrost API base URL
        http_client: Configured HTTP client
        circuit_breaker: Circuit breaker instance

    Returns:
        Health status with circuit breaker and metrics

    Example:
        >>> health = await perform_health_check(...)
        >>> print(health["status"])  # "healthy" or "degraded"
    """
    circuit_metrics = circuit_breaker.get_metrics()

    health = {
        "status": "healthy",
        "version": "1.0.0",
        "circuit_breaker": circuit_metrics,
        "http_client": {
            "pool_size": http_client._limits.max_connections,
            "keepalive": http_client._limits.max_keepalive_connections,
        },
    }

    # Check if circuit is open
    if circuit_metrics["state"] == "open":
        health["status"] = "degraded"

    # Optionally ping backend
    try:
        response = await http_client.get(
            f"{base_url}/health",
            timeout=5.0,
        )
        health["backend"] = {
            "status": "up" if response.status_code == 200 else "down",
            "latency_ms": response.elapsed.total_seconds() * 1000,
        }
    except Exception as e:
        health["backend"] = {
            "status": "down",
            "error": str(e),
        }
        health["status"] = "degraded"

    return health
