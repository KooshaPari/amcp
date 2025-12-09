"""Configuration fixtures for testing.

Provides common configuration objects used across test suites:
- Authentication configuration
- Sandbox settings
- Subscription settings
- Performance targets
- Error scenarios
- Routing strategies
"""

import pytest
from typing import Dict, Any, List


@pytest.fixture
def auth_config() -> Dict[str, Any]:
    """Authentication configuration for testing."""
    return {
        "oauth": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "auth_url": "https://auth.example.com/oauth/authorize",
            "token_url": "https://auth.example.com/oauth/token",
        },
        "api_key": {
            "header_name": "X-API-Key",
            "key_value": "test-api-key",
        },
    }


@pytest.fixture
def sandbox_config() -> Dict[str, Any]:
    """Sandbox configuration for testing."""
    return {
        "enabled": True,
        "timeout_seconds": 30,
        "max_memory_mb": 512,
        "allowed_imports": ["os", "json", "datetime"],
        "blocked_imports": ["subprocess", "socket"],
    }


@pytest.fixture
def subscription_config() -> Dict[str, Any]:
    """Subscription configuration for testing."""
    return {
        "enabled": True,
        "transports": ["websocket", "sse"],
        "max_connections": 100,
        "keepalive_interval": 30,
    }


@pytest.fixture
def performance_config() -> Dict[str, Any]:
    """Performance test configuration."""
    return {
        "concurrent_requests": 100,
        "target_latency_p50_ms": 30,
        "target_latency_p95_ms": 50,
        "target_latency_p99_ms": 100,
        "timeout_ms": 5000,
    }


@pytest.fixture
def error_scenarios() -> List[Dict[str, Any]]:
    """Error scenarios for testing error handling."""
    import asyncio

    return [
        {
            "name": "timeout",
            "exception": asyncio.TimeoutError,
            "message": "Operation timed out",
        },
        {
            "name": "validation_error",
            "exception": ValueError,
            "message": "Invalid input",
        },
        {
            "name": "routing_error",
            "exception": Exception,
            "message": "Routing failed",
        },
    ]


@pytest.fixture
def routing_strategies() -> List[str]:
    """All routing strategies for parametrized testing."""
    try:
        from bifrost_extensions import RoutingStrategy

        return [
            RoutingStrategy.COST_OPTIMIZED,
            RoutingStrategy.PERFORMANCE_OPTIMIZED,
            RoutingStrategy.SPEED_OPTIMIZED,
            RoutingStrategy.BALANCED,
            RoutingStrategy.PARETO,
        ]
    except ImportError:
        # Fallback to string strategies if module not available
        return [
            "cost_optimized",
            "performance_optimized",
            "speed_optimized",
            "balanced",
            "pareto",
        ]
