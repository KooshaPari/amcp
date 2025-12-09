"""
Tests for signal detection scenarios.

Tests specific signal detection patterns including:
- Multiple signals per message
- Confidence scoring
"""

import pytest


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
