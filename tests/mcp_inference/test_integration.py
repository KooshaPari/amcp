"""
End-to-end integration tests for MCP Inference Bridge.

Tests the complete workflow from messages to inference to scope activation.
"""

import pytest

from mcp_inference_bridge import MCPInferenceBridge
from agents.dsl_scope import get_dsl_scope_system


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow: messages -> inference -> scopes."""
    dsl_system = get_dsl_scope_system()
    bridge = MCPInferenceBridge(dsl_system=dsl_system)

    # 1. Process messages (simulating agent interaction)
    messages = [
        {"role": "user", "content": "I'm working on the MyApp project"},
        {"role": "assistant", "content": "Great! Let's start planning"},
        {
            "role": "user",
            "content": "Let's write the implementation",
        },
    ]

    result = await bridge.process_openai_completion(
        messages=messages,
        session_id="workflow-test",
    )

    # 2. Verify inference happened
    assert result["success"] is True
    assert len(result["signals"]) > 0

    # 3. Get activated scopes
    scopes = await bridge.get_current_scopes()
    assert scopes["session_id"] == "workflow-test"

    # 4. Check history
    history = bridge.get_inference_history(limit=1)
    assert len(history) > 0
    assert history[0]["context"]["session_id"] == "workflow-test"
