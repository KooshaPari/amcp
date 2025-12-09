"""Mock client fixtures for testing.

Provides mocked versions of external service clients:
- MCP Server
- Bifrost Client
- Gateway Client
- Router Service
"""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing."""
    server = MagicMock()
    server.name = "test-mcp-server"
    server.version = "1.0.0"
    return server


@pytest.fixture
def mock_bifrost_client():
    """Mock BifrostClient for SmartCP tests."""
    client = AsyncMock()

    async def mock_route(*args, **kwargs):
        return {
            "model": {
                "model_id": "claude-sonnet-4",
                "provider": "anthropic",
                "estimated_cost_usd": 0.005,
                "estimated_latency_ms": 200,
            },
            "confidence": 0.9,
        }

    client.route = mock_route
    return client


@pytest.fixture
def mock_router_service():
    """Mock RoutingService for integration tests."""
    pytest.importorskip("router", reason="Router module moved to research/KRouter-standalone")
    from router.router_core.domain.models.model import Model
    from router.router_core.domain.models.plan import RoutingPlan
    from router.router_core.domain.models.classification import Classification

    mock_service = MagicMock()

    # Create mock model
    mock_model = Model(
        key="claude-sonnet-4",
        provider="anthropic",
        price_in=0.003,
        price_out=0.015,
        context_window=200000,
        avg_latency_ms=250.0,
    )

    # Create mock classification
    mock_classification = Classification(
        complexity="moderate",
        confidence=0.85,
        reasoning="Based on prompt analysis",
    )

    # Create mock plan
    mock_plan = RoutingPlan(
        primary_model=mock_model,
        candidates=[mock_model],
        classification=mock_classification,
    )

    async def build_plan_mock(request, context=None):
        return mock_plan

    mock_service.build_plan = build_plan_mock

    return mock_service


@pytest.fixture
async def gateway_client(mock_router_service):
    """Create GatewayClient with mocked router service."""
    try:
        from bifrost_extensions import GatewayClient

        with patch("bifrost_extensions.client.RoutingService") as mock_routing:
            mock_routing.return_value = mock_router_service
            client = GatewayClient(
                api_key="test-key",
                base_url="http://localhost:8000",
                timeout=30.0,
            )
            client._router = mock_router_service
            yield client
    except ImportError:
        # If bifrost_extensions not available, skip
        yield None
