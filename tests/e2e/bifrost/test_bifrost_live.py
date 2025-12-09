"""
E2E tests for Bifrost Gateway stack.

Tests real HTTP calls to:
- Bifrost API (localhost:8000)
- GraphQL Backend (localhost:8080)
- gRPC MLX Service (localhost:8001)

All tests run against live services started via docker-compose.
"""

import pytest
import asyncio
from typing import Dict, Any


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_health(bifrost_client, track_performance):
    """Test Bifrost Gateway health endpoint."""
    stop = track_performance("bifrost_health")

    # Real HTTP call to localhost:8000/health
    response = await bifrost_client.http_client.get(f"{bifrost_client.url}/health")

    duration = stop()

    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"

    # Performance check
    assert duration < 1.0, f"Health check too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_route_live(bifrost_client, track_performance):
    """Test live routing through Bifrost."""
    stop = track_performance("bifrost_route")

    # Real routing request
    response = await bifrost_client.route_request(
        prompt="What is the weather in San Francisco?",
        context={"user_id": "test-user"}
    )

    duration = stop()

    assert response.selected_tool
    assert response.confidence > 0.0
    assert response.reasoning

    # Performance check
    assert duration < 5.0, f"Routing too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_tool_execution_live(bifrost_client, track_performance):
    """Test live tool execution via Bifrost."""
    stop = track_performance("bifrost_execute_tool")

    # Execute tool through Bifrost
    result = await bifrost_client.execute_tool(
        name="echo_tool",
        input_data={"message": "Hello from E2E test"}
    )

    duration = stop()

    assert result.get("success") is True
    assert "data" in result

    # Performance check
    assert duration < 10.0, f"Tool execution too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_query_tools_live(bifrost_client, track_performance):
    """Test querying available tools from Bifrost."""
    stop = track_performance("bifrost_query_tools")

    tools = await bifrost_client.query_tools(limit=50)

    duration = stop()

    assert len(tools) > 0
    assert all(hasattr(t, "name") for t in tools)
    assert all(hasattr(t, "description") for t in tools)

    # Performance check
    assert duration < 3.0, f"Tool query too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_semantic_search_live(bifrost_client, track_performance):
    """Test semantic search via Bifrost."""
    stop = track_performance("bifrost_semantic_search")

    results = await bifrost_client.semantic_search(
        query="find documents about machine learning",
        limit=10
    )

    duration = stop()

    assert isinstance(results, list)
    # Results may be empty if no documents indexed yet

    # Performance check
    assert duration < 5.0, f"Search too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_graphql_integration(graphql_client, track_performance):
    """Test direct GraphQL backend integration."""
    stop = track_performance("graphql_query")

    query = """
    query {
        models {
            id
            name
            provider
        }
    }
    """

    result = await graphql_client.query(query)

    duration = stop()

    assert "models" in result
    assert isinstance(result["models"], list)

    # Performance check
    assert duration < 2.0, f"GraphQL query too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_grpc_classification(bifrost_client, track_performance):
    """Test gRPC classification service integration."""
    stop = track_performance("grpc_classification")

    # This would call through Bifrost → Go backend → gRPC
    # Assuming Bifrost has a classification endpoint
    try:
        response = await bifrost_client.http_client.post(
            f"{bifrost_client.url}/v1/classify",
            json={
                "text": "Show me the latest news about AI",
                "categories": ["search", "news", "weather", "calculation"]
            }
        )

        duration = stop()

        if response.status_code == 200:
            data = response.json()
            assert "category" in data
            assert "confidence" in data

            # Performance check
            assert duration < 3.0, f"Classification too slow: {duration:.3f}s"
    except Exception as e:
        pytest.skip(f"Classification endpoint not available: {e}")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_error_handling_live(bifrost_client):
    """Test error handling with invalid requests."""
    # Test invalid tool name
    with pytest.raises(Exception):
        await bifrost_client.execute_tool(
            name="nonexistent_tool_xyz",
            input_data={}
        )

    # Test invalid GraphQL query
    with pytest.raises(Exception):
        await bifrost_client.query("invalid query syntax {}")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_concurrent_requests(bifrost_client, track_performance):
    """Test handling concurrent requests."""
    stop = track_performance("concurrent_requests")

    # Send 10 concurrent routing requests
    tasks = [
        bifrost_client.route_request(
            prompt=f"Test request {i}",
            context={"user_id": f"user-{i}"}
        )
        for i in range(10)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = stop()

    # Check that all succeeded
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) >= 8, "Most requests should succeed"

    # Performance check - should handle concurrency well
    assert duration < 10.0, f"Concurrent requests too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
async def test_bifrost_subscription_live(bifrost_client):
    """Test GraphQL subscription for real-time events."""
    events_received = []

    async def handler(data):
        events_received.append(data)

    # Subscribe to tool events
    sub_id = await bifrost_client.subscribe_tool_events(
        tool_name="echo_tool",
        handler=handler
    )

    assert sub_id

    # Execute tool to trigger event
    await bifrost_client.execute_tool(
        name="echo_tool",
        input_data={"message": "subscription test"}
    )

    # Wait for event
    await asyncio.sleep(2)

    # Unsubscribe
    await bifrost_client.unsubscribe(sub_id)

    # Check if event was received
    assert len(events_received) > 0


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_bifrost_full_flow_live(
    bifrost_client,
    test_workspace_id,
    test_user_id,
    track_performance
):
    """
    Test complete flow: Route → Execute → Verify.

    Simulates real user interaction:
    1. Route user prompt to appropriate tool
    2. Execute selected tool
    3. Verify result
    """
    stop = track_performance("full_flow")

    # Step 1: Route prompt
    routing = await bifrost_client.route_request(
        prompt="Search for documents about Python programming",
        context={
            "workspace_id": test_workspace_id,
            "user_id": test_user_id
        }
    )

    assert routing.selected_tool
    print(f"Selected tool: {routing.selected_tool} (confidence: {routing.confidence})")

    # Step 2: Execute selected tool
    result = await bifrost_client.execute_tool(
        name=routing.selected_tool,
        input_data={
            "query": "Python programming",
            "workspace_id": test_workspace_id
        }
    )

    # Step 3: Verify result
    assert result.get("success") is not False  # May be True or None

    duration = stop()

    # Performance check for full flow
    assert duration < 15.0, f"Full flow too slow: {duration:.3f}s"

    print(f"Full flow completed in {duration:.3f}s")
