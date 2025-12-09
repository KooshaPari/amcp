"""
Tests for routing operations.

Tests request routing and tool selection functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch

from smartcp.infrastructure.bifrost import RoutingDecision


class TestRouting:
    """Test routing operations."""

    @pytest.mark.asyncio
    async def test_route_request(self, bifrost_client_instance):
        """Test routing request."""
        client = bifrost_client_instance
        mock_data = {
            "route": {
                "selectedTool": "entity_create",
                "confidence": 0.95,
                "reasoning": "User wants to create entity",
                "alternatives": [
                    {"tool": "entity_update", "score": 0.3}
                ]
            }
        }

        with patch.object(client, "query", AsyncMock(return_value=mock_data)):
            decision = await client.route_request(
                prompt="Create a new project",
                context={"workspace_id": "123"}
            )

            assert isinstance(decision, RoutingDecision)
            assert decision.selected_tool == "entity_create"
            assert decision.confidence == 0.95
            assert decision.reasoning == "User wants to create entity"
            assert len(decision.alternatives) == 1
