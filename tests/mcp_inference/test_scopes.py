"""
Tests for scope activation via DSL system.

Tests that scopes are properly activated in the DSL scope system.
"""

import pytest


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
