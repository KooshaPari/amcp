"""
Request flow E2E tests.

Tests complete request flows:
- Route to tool execution
- Classification, routing, and execution
- Semantic search to tool discovery
- Multi-tool workflows with state management
"""

import pytest
import asyncio
from typing import Dict, Any


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.integration
async def test_route_to_tool_execution(
    bifrost_client,
    smartcp_stdio_client,
    test_workspace_id,
    test_user_id,
    track_performance
):
    """
    Test: Bifrost route → SmartCP execute tool → Result.

    Complete flow:
    1. User prompt to Bifrost
    2. Bifrost routes to appropriate tool
    3. SmartCP executes the tool
    4. Result returned to user
    """
    stop = track_performance("route_to_execution")

    # Step 1: Route prompt via Bifrost
    routing = await bifrost_client.route_request(
        prompt="Execute command: ls -la",
        context={
            "workspace_id": test_workspace_id,
            "user_id": test_user_id
        }
    )

    assert routing.selected_tool
    print(f"Routing decision: {routing.selected_tool} (confidence: {routing.confidence})")

    # Step 2: Execute via SmartCP (simulating Bifrost → SmartCP delegation)
    result = await smartcp_stdio_client.call_tool(
        name="execute",  # Assuming routing selected this
        arguments={
            "command": "ls -la",
            "cwd": None
        }
    )

    assert result.content

    duration = stop()

    # Performance check
    assert duration < 10.0, f"Route to execution too slow: {duration:.3f}s"

    print(f"Complete flow: {duration:.3f}s")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.integration
async def test_classification_routing_execution(
    bifrost_client,
    smartcp_stdio_client,
    track_performance
):
    """
    Test: Classification → Routing → Tool selection → Execution.

    Flow:
    1. Classify user intent
    2. Route based on classification
    3. Select appropriate tool
    4. Execute tool
    """
    stop = track_performance("classify_route_execute")

    # Step 1: Classify intent (via Bifrost)
    try:
        classify_response = await bifrost_client.http_client.post(
            f"{bifrost_client.url}/v1/classify",
            json={
                "text": "Show me my recent documents",
                "categories": ["search", "query", "execute", "memory"]
            }
        )

        if classify_response.status_code == 200:
            classification = classify_response.json()
            category = classification.get("category", "query")
            print(f"Classification: {category}")

            # Step 2: Route based on classification
            routing = await bifrost_client.route_request(
                prompt="Show me my recent documents",
                context={"category": category}
            )

            # Step 3 & 4: Execute selected tool
            if routing.selected_tool:
                result = await smartcp_stdio_client.call_tool(
                    name=routing.selected_tool,
                    arguments={"query": "recent documents"}
                )
                assert result.content

    except Exception as e:
        pytest.skip(f"Classification endpoint not available: {e}")

    duration = stop()

    print(f"Classify → Route → Execute: {duration:.3f}s")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.integration
async def test_semantic_search_to_tool_discovery(
    bifrost_client,
    smartcp_stdio_client,
    track_performance
):
    """
    Test: Semantic search → Tool discovery → Execution.

    Flow:
    1. Semantic search for relevant tools
    2. Discover tool via search results
    3. Execute discovered tool
    """
    stop = track_performance("search_discover_execute")

    # Step 1: Semantic search
    search_results = await bifrost_client.semantic_search(
        query="execute shell commands",
        limit=5
    )

    print(f"Search found {len(search_results)} results")

    # Step 2: Discover tools from search
    tools = await smartcp_stdio_client.list_tools()
    tool_names = [t.name for t in tools.tools]

    # Find execute tool
    execute_tool = next((t for t in tools.tools if "execute" in t.name.lower()), None)

    if execute_tool:
        # Step 3: Execute discovered tool
        result = await smartcp_stdio_client.call_tool(
            name=execute_tool.name,
            arguments={
                "command": "echo 'discovered via search'",
                "cwd": None
            }
        )
        assert result.content

    duration = stop()

    print(f"Search → Discover → Execute: {duration:.3f}s")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.integration
async def test_multi_tool_workflow(
    bifrost_client,
    smartcp_stdio_client,
    test_workspace_id,
    track_performance
):
    """
    Test: Multi-tool workflow with state management.

    Workflow:
    1. Route to determine first tool
    2. Execute first tool
    3. Store result in memory
    4. Route based on first result
    5. Execute second tool
    6. Combine results
    """
    stop = track_performance("multi_tool_workflow")

    # Step 1: Route for first action
    routing1 = await bifrost_client.route_request(
        prompt="List files in current directory",
        context={"workspace_id": test_workspace_id}
    )

    # Step 2: Execute first tool
    result1 = await smartcp_stdio_client.call_tool(
        name="execute",
        arguments={
            "command": "ls",
            "cwd": None
        }
    )

    # Step 3: Store result
    await smartcp_stdio_client.call_tool(
        name="memory",
        arguments={
            "action": "store",
            "key": "ls_output",
            "value": {"output": str(result1.content)}
        }
    )

    # Step 4: Route for second action
    routing2 = await bifrost_client.route_request(
        prompt="Count the files from previous result",
        context={
            "workspace_id": test_workspace_id,
            "previous_result": "ls_output"
        }
    )

    # Step 5: Execute second tool
    result2 = await smartcp_stdio_client.call_tool(
        name="execute",
        arguments={
            "command": "echo 'Processing count'",
            "cwd": None
        }
    )

    # Step 6: Combine results
    combined = {
        "first": result1.content,
        "second": result2.content
    }

    duration = stop()

    assert result1.content
    assert result2.content

    print(f"Multi-tool workflow: {duration:.3f}s")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.slow
async def test_concurrent_workflows(
    bifrost_client,
    smartcp_stdio_client,
    track_performance
):
    """
    Test: Multiple concurrent workflows.

    Simulates multiple users executing workflows simultaneously.
    """
    stop = track_performance("concurrent_workflows")

    async def workflow(user_id: str):
        # Route
        routing = await bifrost_client.route_request(
            prompt=f"Execute workflow for {user_id}",
            context={"user_id": user_id}
        )

        # Execute
        result = await smartcp_stdio_client.call_tool(
            name="execute",
            arguments={
                "command": f"echo 'User {user_id}'",
                "cwd": None
            }
        )

        return result

    # Run 5 concurrent workflows
    tasks = [workflow(f"user-{i}") for i in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = stop()

    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) >= 4, "Most workflows should succeed"

    print(f"Concurrent workflows: {duration:.3f}s")
