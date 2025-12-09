"""
Response flow E2E tests.

Tests response and subscription flows:
- Real-time subscription-based workflows
- Event handling and processing
"""

import pytest
import asyncio


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.integration
async def test_subscription_based_workflow(
    bifrost_client,
    smartcp_stdio_client,
    track_performance
):
    """
    Test: Real-time subscription-based workflow.

    Flow:
    1. Subscribe to tool events
    2. Execute tools
    3. Receive events in real-time
    4. Process events
    """
    stop = track_performance("subscription_workflow")

    events = []

    async def event_handler(data):
        events.append(data)
        print(f"Event received: {data}")

    # Subscribe to events
    sub_id = await bifrost_client.subscribe_tool_events(
        tool_name="execute",
        handler=event_handler
    )

    # Execute tools to trigger events
    await smartcp_stdio_client.call_tool(
        name="execute",
        arguments={"command": "echo 'event 1'", "cwd": None}
    )

    await asyncio.sleep(1)

    await smartcp_stdio_client.call_tool(
        name="execute",
        arguments={"command": "echo 'event 2'", "cwd": None}
    )

    await asyncio.sleep(2)

    # Unsubscribe
    await bifrost_client.unsubscribe(sub_id)

    duration = stop()

    # Check events received
    assert len(events) >= 1, "Should receive at least one event"

    print(f"Subscription workflow: {duration:.3f}s, events: {len(events)}")
