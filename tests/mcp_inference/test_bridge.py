"""
Tests for MCPInferenceBridge functionality.

Tests the core inference bridge operations including:
- OpenAI completion processing
- Project and phase inference
- Tool call processing
- Scope retrieval
- History tracking
"""

import pytest

from agents.dsl_scope import ScopeLevel


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
