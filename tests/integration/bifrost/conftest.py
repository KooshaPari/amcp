"""Fixtures for Bifrost SDK integration tests."""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from bifrost_extensions import GatewayClient, RoutingStrategy
from bifrost_extensions.models import Message, ModelInfo


@pytest.fixture
def mock_router_service():
    """Mock RoutingService for integration tests."""
    from router.router_core.application.routing_service import RoutingContext
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
    with patch("bifrost_extensions.client.RoutingService") as mock_routing:
        mock_routing.return_value = mock_router_service
        client = GatewayClient(
            api_key="test-key",
            base_url="http://localhost:8000",
            timeout=30.0,
        )
        client._router = mock_router_service
        yield client


@pytest.fixture
def sample_messages() -> List[Message]:
    """Sample chat messages for testing."""
    return [
        Message(role="user", content="Write a Python function to parse JSON"),
        Message(role="assistant", content="Here's a function to parse JSON..."),
        Message(role="user", content="Add error handling"),
    ]


@pytest.fixture
def sample_messages_simple() -> List[Message]:
    """Simple single message for testing."""
    return [Message(role="user", content="Hello")]


@pytest.fixture
def sample_messages_complex() -> List[Message]:
    """Complex multi-turn conversation for testing."""
    return [
        Message(role="system", content="You are a helpful coding assistant"),
        Message(role="user", content="Implement a binary search tree in Python"),
        Message(role="assistant", content="Here's a basic BST implementation..."),
        Message(role="user", content="Add deletion with rebalancing"),
        Message(role="assistant", content="For deletion with rebalancing..."),
        Message(role="user", content="Optimize for cache locality"),
    ]


@pytest.fixture
def sample_tools() -> List[str]:
    """Sample tool names for testing."""
    return ["web_search", "doc_search", "code_search", "file_search"]


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
def mock_llm_responses():
    """Mock LLM API responses for testing."""
    return {
        "classification": {
            "category": "code_generation",
            "confidence": 0.9,
            "complexity": "moderate",
        },
        "tool_routing": {
            "tool": "code_search",
            "confidence": 0.85,
            "reasoning": "Code-related query",
        },
    }


@pytest.fixture(scope="function")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def routing_strategies() -> List[RoutingStrategy]:
    """All routing strategies for parametrized testing."""
    return [
        RoutingStrategy.COST_OPTIMIZED,
        RoutingStrategy.PERFORMANCE_OPTIMIZED,
        RoutingStrategy.SPEED_OPTIMIZED,
        RoutingStrategy.BALANCED,
        RoutingStrategy.PARETO,
    ]


@pytest.fixture
def error_scenarios() -> List[Dict[str, Any]]:
    """Error scenarios for testing error handling."""
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
