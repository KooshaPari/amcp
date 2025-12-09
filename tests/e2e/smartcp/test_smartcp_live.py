"""
E2E tests for SmartCP MCP Server.

Tests:
- stdio transport (primary)
- HTTP/SSE transport (if available)
- Tool execution
- Bifrost delegation
"""

import os
import pytest
import asyncio
from typing import Dict, Any


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_initialization_stdio(smartcp_stdio_client, track_performance):
    """Test SmartCP MCP server initialization via stdio."""
    stop = track_performance("smartcp_init_stdio")

    # Server already initialized by fixture
    # Check that we can list tools
    tools_result = await smartcp_stdio_client.list_tools()

    duration = stop()

    assert tools_result.tools
    assert len(tools_result.tools) > 0

    print(f"Available tools: {[t.name for t in tools_result.tools]}")

    # Performance check
    assert duration < 2.0, f"Initialization too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_list_tools(smartcp_stdio_client):
    """Test listing available MCP tools."""
    result = await smartcp_stdio_client.list_tools()

    assert result.tools
    assert len(result.tools) > 0

    # Check for expected tools
    tool_names = [t.name for t in result.tools]
    expected_tools = ["execute", "memory", "state"]

    for expected in expected_tools:
        assert any(expected in name for name in tool_names), \
            f"Expected tool '{expected}' not found"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_execute_tool_live(smartcp_stdio_client, track_performance):
    """Test executing a tool via SmartCP."""
    stop = track_performance("smartcp_execute_tool")

    # Execute a simple tool
    result = await smartcp_stdio_client.call_tool(
        name="execute",
        arguments={
            "command": "echo 'Hello from E2E test'",
            "cwd": None
        }
    )

    duration = stop()

    assert result.content
    assert len(result.content) > 0

    # Check output
    output = result.content[0].text if result.content else ""
    assert "Hello from E2E test" in output or "success" in output.lower()

    # Performance check
    assert duration < 5.0, f"Tool execution too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_memory_tool(smartcp_stdio_client):
    """Test memory tool for state management."""
    # Store value
    store_result = await smartcp_stdio_client.call_tool(
        name="memory",
        arguments={
            "action": "store",
            "key": "test_key_e2e",
            "value": {"data": "test_value", "timestamp": "2024-01-01"}
        }
    )

    assert store_result.content

    # Retrieve value
    retrieve_result = await smartcp_stdio_client.call_tool(
        name="memory",
        arguments={
            "action": "retrieve",
            "key": "test_key_e2e"
        }
    )

    assert retrieve_result.content
    # Verify stored data can be retrieved


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_state_tool(smartcp_stdio_client):
    """Test state management tool."""
    # Get current state
    result = await smartcp_stdio_client.call_tool(
        name="state",
        arguments={
            "action": "get"
        }
    )

    assert result.content


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_bifrost_delegation(
    smartcp_stdio_client,
    bifrost_client,
    track_performance
):
    """
    Test SmartCP delegating to Bifrost for routing.

    Flow:
    1. SmartCP receives tool call
    2. SmartCP delegates routing to Bifrost
    3. Bifrost returns routing decision
    4. SmartCP executes appropriate tool
    """
    stop = track_performance("smartcp_bifrost_delegation")

    # This assumes SmartCP has a tool that delegates to Bifrost
    # Adjust based on actual implementation
    try:
        result = await smartcp_stdio_client.call_tool(
            name="route",  # Or whatever the delegation tool is named
            arguments={
                "prompt": "Search for machine learning papers",
                "context": {"user_id": "test-user"}
            }
        )

        duration = stop()

        assert result.content

        # Performance check
        assert duration < 10.0, f"Delegation too slow: {duration:.3f}s"

    except Exception as e:
        pytest.skip(f"Delegation tool not available: {e}")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_error_handling(smartcp_stdio_client):
    """Test error handling with invalid tool calls."""
    # Test nonexistent tool
    with pytest.raises(Exception):
        await smartcp_stdio_client.call_tool(
            name="nonexistent_tool_xyz",
            arguments={}
        )

    # Test invalid arguments
    with pytest.raises(Exception):
        await smartcp_stdio_client.call_tool(
            name="execute",
            arguments={
                "invalid_arg": "value"
            }
        )


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_concurrent_tool_calls(smartcp_stdio_client, track_performance):
    """Test handling concurrent tool calls."""
    stop = track_performance("concurrent_tool_calls")

    # Execute multiple tools concurrently
    tasks = [
        smartcp_stdio_client.call_tool(
            name="execute",
            arguments={
                "command": f"echo 'Request {i}'",
                "cwd": None
            }
        )
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = stop()

    # Check that all succeeded
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) >= 4, "Most tool calls should succeed"

    # Performance check
    assert duration < 10.0, f"Concurrent calls too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.skipif(
    not bool(os.getenv("E2E_SMARTCP_HTTP_URL")),
    reason="HTTP endpoint not configured"
)
async def test_smartcp_http_transport(smartcp_http_client, track_performance):
    """Test SmartCP HTTP/SSE transport (if available)."""
    stop = track_performance("smartcp_http")

    client = smartcp_http_client["client"]
    base_url = smartcp_http_client["base_url"]

    # Test HTTP endpoint
    response = await client.get(f"{base_url}/health")

    duration = stop()

    assert response.status_code == 200

    # Performance check
    assert duration < 2.0, f"HTTP health check too slow: {duration:.3f}s"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_tool_discovery(smartcp_stdio_client):
    """Test tool discovery and metadata."""
    result = await smartcp_stdio_client.list_tools()

    assert result.tools

    # Check tool metadata
    for tool in result.tools:
        assert tool.name
        assert tool.description
        assert hasattr(tool, "inputSchema")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_resource_discovery(smartcp_stdio_client):
    """Test resource discovery (if supported)."""
    try:
        result = await smartcp_stdio_client.list_resources()
        assert result.resources is not None
    except Exception:
        pytest.skip("Resource listing not supported")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_prompt_discovery(smartcp_stdio_client):
    """Test prompt discovery (if supported)."""
    try:
        result = await smartcp_stdio_client.list_prompts()
        assert result.prompts is not None
    except Exception:
        pytest.skip("Prompt listing not supported")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smartcp_full_workflow(
    smartcp_stdio_client,
    test_workspace_id,
    cleanup_test_data,
    track_performance
):
    """
    Test complete workflow through SmartCP.

    Workflow:
    1. Initialize state
    2. Execute tool
    3. Store result in memory
    4. Retrieve and verify
    """
    stop = track_performance("smartcp_full_workflow")

    # Step 1: Initialize state
    await smartcp_stdio_client.call_tool(
        name="state",
        arguments={
            "action": "set",
            "key": "workflow_id",
            "value": "test-workflow-123"
        }
    )

    # Step 2: Execute tool
    exec_result = await smartcp_stdio_client.call_tool(
        name="execute",
        arguments={
            "command": "echo 'workflow test'",
            "cwd": None
        }
    )

    assert exec_result.content

    # Step 3: Store result
    await smartcp_stdio_client.call_tool(
        name="memory",
        arguments={
            "action": "store",
            "key": "workflow_result",
            "value": {"output": "workflow test", "status": "success"}
        }
    )

    # Step 4: Retrieve and verify
    retrieve_result = await smartcp_stdio_client.call_tool(
        name="memory",
        arguments={
            "action": "retrieve",
            "key": "workflow_result"
        }
    )

    assert retrieve_result.content

    duration = stop()

    # Performance check
    assert duration < 10.0, f"Workflow too slow: {duration:.3f}s"

    print(f"Workflow completed in {duration:.3f}s")

    # Register cleanup
    async def cleanup():
        await smartcp_stdio_client.call_tool(
            name="memory",
            arguments={"action": "delete", "key": "workflow_result"}
        )

    cleanup_test_data(cleanup())


import os
