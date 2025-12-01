"""
Integration tests for MCP Inference Bridge and FastMCP Inference Server.

Tests the complete pipeline:
1. OpenAI-compatible messages → inference
2. Tool call processing
3. Scope activation
4. History tracking
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

from mcp_inference_bridge import (
    MCPInferenceBridge,
    InferenceMiddleware,
    InferenceContext,
    create_inference_middleware,
)

from dsl_scope import get_dsl_scope_system, ScopeLevel


@pytest.fixture
def dsl_system():
    """Get DSL scope system instance."""
    return get_dsl_scope_system()


@pytest.fixture
def bridge(dsl_system):
    """Create MCP inference bridge."""
    return MCPInferenceBridge(dsl_system=dsl_system)


@pytest.fixture
def sample_messages() -> List[Dict[str, Any]]:
    """Sample OpenAI-format messages."""
    return [
        {
            "role": "user",
            "content": "I'm working on the MyApp project",
        },
        {
            "role": "assistant",
            "content": "Great! Let's start implementing the feature.",
        },
        {
            "role": "user",
            "content": "Let's write unit tests for the auth module",
        },
    ]


@pytest.fixture
def sample_tools() -> List[Dict[str, Any]]:
    """Sample tool definitions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file",
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_tests",
                "description": "Run test suite",
            },
        },
    ]


class TestMCPInferenceBridge:
    """Test MCPInferenceBridge functionality."""

    @pytest.mark.asyncio
    async def test_process_openai_completion(
        self, bridge, sample_messages, sample_tools
    ):
        """Test processing OpenAI completion."""
        result = await bridge.process_openai_completion(
            messages=sample_messages,
            tools=sample_tools,
            session_id="test-session-123",
            request_id="test-request-456",
            model="claude-3-sonnet",
            temperature=0.7,
        )

        # Check result structure
        assert result["success"] is True
        assert "signals" in result
        assert "activated_scopes" in result
        assert "inference_context" in result

        # Check context
        context = result["inference_context"]
        assert context["session_id"] == "test-session-123"
        assert context["request_id"] == "test-request-456"
        assert context["model"] == "claude-3-sonnet"
        assert context["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_project_inference(self, bridge):
        """Test project name inference from messages."""
        messages = [
            {
                "role": "user",
                "content": "I'm working on the MyApp project",
            }
        ]

        result = await bridge.process_openai_completion(
            messages=messages, session_id="test"
        )

        # Should detect project mention
        assert result["success"] is True
        assert len(result["signals"]) > 0

        # At least one signal should mention project
        project_signals = [
            s for s in result["signals"]
            if s.scope_level == ScopeLevel.PROJECT
        ]
        assert len(project_signals) > 0

    @pytest.mark.asyncio
    async def test_phase_inference(self, bridge):
        """Test phase inference from intent keywords."""
        messages = [
            {
                "role": "user",
                "content": "Let's write unit tests for the module",
            }
        ]

        result = await bridge.process_openai_completion(
            messages=messages, session_id="test"
        )

        assert result["success"] is True
        # Should detect testing phase
        phase_signals = [
            s for s in result["signals"]
            if s.scope_level == ScopeLevel.PHASE
        ]
        assert len(phase_signals) > 0

    @pytest.mark.asyncio
    async def test_tool_call_processing(self, bridge):
        """Test tool call analysis."""
        signals = await bridge.process_tool_call(
            tool_name="run_tests",
            arguments={"test_path": "tests/unit/"},
            result={"passed": 10, "failed": 0},
        )

        # Tool call analysis should complete
        assert isinstance(signals, list)

    @pytest.mark.asyncio
    async def test_get_current_scopes(self, bridge, dsl_system):
        """Test retrieving current active scopes."""
        scopes = await bridge.get_current_scopes()

        # Should have all scope fields
        expected_fields = [
            "session_id",
            "tool_call_id",
            "prompt_chain_id",
            "phase_id",
            "phase_type",
            "project_id",
            "project_name",
            "workspace_id",
            "workspace_name",
            "organization_id",
            "organization_name",
        ]

        for field in expected_fields:
            assert field in scopes

    @pytest.mark.asyncio
    async def test_inference_history_tracking(self, bridge, sample_messages):
        """Test inference history is tracked."""
        # Process two requests
        for i in range(2):
            await bridge.process_openai_completion(
                messages=sample_messages,
                session_id=f"session-{i}",
                request_id=f"request-{i}",
            )

        # Check history
        history = bridge.get_inference_history(limit=10)
        assert len(history) >= 2

        # History should be in reverse chronological order (most recent first)
        assert (
            history[0]["context"]["request_id"]
            == "request-1"
        )

    @pytest.mark.asyncio
    async def test_clear_inference_history(self, bridge, sample_messages):
        """Test clearing inference history."""
        # Add entry
        await bridge.process_openai_completion(
            messages=sample_messages, session_id="test"
        )

        # Verify it's there
        assert len(bridge.get_inference_history()) > 0

        # Clear it
        bridge.clear_inference_history()
        assert len(bridge.get_inference_history()) == 0

    @pytest.mark.asyncio
    async def test_infer_from_recent_history(self, bridge, sample_messages):
        """Test inference context from recent history."""
        # Add entries
        for i in range(3):
            await bridge.process_openai_completion(
                messages=sample_messages,
                session_id=f"session-{i}",
            )

        # Infer from recent
        result = await bridge.infer_from_recent_history(window=3)

        assert "recent_entries" in result
        assert "signal_counts" in result
        assert result["recent_entries"] >= 1


class TestInferenceMiddleware:
    """Test InferenceMiddleware functionality."""

    @pytest.mark.asyncio
    async def test_process_completion_request(self):
        """Test middleware processes completion requests."""
        middleware = create_inference_middleware()

        request = {
            "method": "POST",
            "path": "/v1/completions",
            "body": {
                "messages": [
                    {
                        "role": "user",
                        "content": "I'm working on MyApp",
                    }
                ]
            },
            "headers": {
                "X-Session-ID": "session-123",
                "X-Request-ID": "request-456",
            },
        }

        result = await middleware.process_request(request)

        # Check request was processed
        assert "_inference_result" in result or "_inference_error" in result

        if "_inference_result" in result:
            assert result["_inference_result"]["success"] is True

    @pytest.mark.asyncio
    async def test_middleware_passes_non_completion_requests(self):
        """Test middleware passes through non-completion requests."""
        middleware = create_inference_middleware()

        request = {
            "method": "GET",
            "path": "/v1/models",
            "headers": {},
        }

        result = await middleware.process_request(request)

        # Should pass through unchanged (no inference fields added)
        assert "_inference_result" not in result
        assert "_inference_error" not in result

    @pytest.mark.asyncio
    async def test_middleware_error_handling(self):
        """Test middleware handles inference errors gracefully."""
        middleware = create_inference_middleware()

        # Malformed request
        request = {
            "method": "POST",
            "path": "/v1/completions",
            "body": None,  # This will cause an error
            "headers": {},
        }

        result = await middleware.process_request(request)

        # Should not crash, just mark error
        assert "_inference_error" in result or "_inference_result" in result


class TestSignalDetection:
    """Test specific signal detection scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_signals_per_message(self, bridge):
        """Test detecting multiple signals from single message."""
        messages = [
            {
                "role": "user",
                "content": (
                    "I'm implementing tests for the MyApp project "
                    "in the engineering workspace"
                ),
            }
        ]

        result = await bridge.process_openai_completion(
            messages=messages, session_id="test"
        )

        # Should detect multiple scope types
        scope_types = set(s.scope_level for s in result["signals"])
        assert len(scope_types) >= 2  # At least project and phase

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, bridge):
        """Test that signals have confidence scores."""
        messages = [
            {"role": "user", "content": "Working on MyApp project"}
        ]

        result = await bridge.process_openai_completion(
            messages=messages, session_id="test"
        )

        # All signals should have confidence
        for signal in result["signals"]:
            assert 0.0 <= signal.confidence <= 1.0
            assert signal.evidence is not None


class TestScopeActivation:
    """Test scope activation via DSL system."""

    @pytest.mark.asyncio
    async def test_scopes_are_activated(self, bridge, dsl_system):
        """Test that scopes are actually activated in DSL system."""
        messages = [
            {"role": "user", "content": "I'm working on MyApp project"}
        ]

        # Process
        result = await bridge.process_openai_completion(
            messages=messages,
            session_id="test-session-final",
        )

        # Check that scopes were activated
        scopes = await bridge.get_current_scopes()

        # Session should be set
        assert scopes["session_id"] == "test-session-final"

        # If project was inferred, it should be in scopes
        activated = result["activated_scopes"]
        if "project" in activated:
            assert scopes["project_name"] is not None


@pytest.mark.asyncio
async def test_end_to_end_workflow(dsl_system):
    """Test complete workflow: messages → inference → scopes."""
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
