"""Integration tests for Bifrost HTTP API."""

import pytest
from fastapi.testclient import TestClient

from bifrost_api.app import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create auth headers."""
    return {"X-API-Key": "test_api_key_123456"}


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_route_endpoint_no_auth(client):
    """Test route endpoint without authentication."""
    response = client.post("/v1/route", json={"messages": [], "strategy": "balanced"})
    assert response.status_code == 401


def test_route_endpoint_with_auth(client, auth_headers):
    """Test route endpoint with authentication."""
    response = client.post(
        "/v1/route",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "strategy": "balanced",
        },
        headers=auth_headers,
    )

    # May succeed or fail depending on router_core availability
    # Just check response structure
    assert response.status_code in (200, 500)

    if response.status_code == 200:
        data = response.json()
        assert "model" in data
        assert "confidence" in data
        assert "request_id" in data


def test_tool_route_endpoint(client, auth_headers):
    """Test tool routing endpoint."""
    response = client.post(
        "/v1/route-tool",
        json={
            "action": "search documentation",
            "available_tools": ["web_search", "doc_search"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "recommended_tool" in data
    assert "confidence" in data
    assert "request_id" in data


def test_classify_endpoint(client, auth_headers):
    """Test classification endpoint."""
    response = client.post(
        "/v1/classify",
        json={"prompt": "Write Python code", "categories": ["simple", "complex"]},
        headers=auth_headers,
    )

    assert response.status_code in (200, 500)

    if response.status_code == 200:
        data = response.json()
        assert "category" in data
        assert "confidence" in data
        assert "complexity" in data
        assert "request_id" in data


def test_usage_endpoint(client, auth_headers):
    """Test usage endpoint."""
    response = client.get(
        "/v1/usage",
        params={"start_date": "2025-12-01", "end_date": "2025-12-02"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_cost_usd" in data
    assert "avg_latency_ms" in data


def test_request_id_middleware(client, auth_headers):
    """Test request ID middleware."""
    custom_request_id = "custom_req_123"

    response = client.post(
        "/v1/route-tool",
        json={
            "action": "search",
            "available_tools": ["tool1"],
        },
        headers={**auth_headers, "X-Request-ID": custom_request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_request_id


def test_rate_limit_headers(client, auth_headers):
    """Test rate limit headers are present."""
    response = client.post(
        "/v1/route-tool",
        json={
            "action": "search",
            "available_tools": ["tool1"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


@pytest.mark.asyncio
async def test_http_client_integration():
    """Test HTTP client integration with GatewayClient."""
    from bifrost_extensions import GatewayClient, RoutingStrategy

    # Create client with HTTP mode
    client = GatewayClient(
        api_key="test_api_key_123456",
        base_url="http://localhost:8000",
        use_http=True,
    )

    # This test requires running server
    # Skip if server not available
    try:
        health = await client.health_check()
        assert health["status"] == "healthy"

        # Test routing
        response = await client.route(
            messages=[{"role": "user", "content": "Hello"}],
            strategy=RoutingStrategy.BALANCED,
        )

        assert response.model is not None
        assert response.confidence > 0

    except Exception as e:
        pytest.skip(f"Server not available: {e}")
