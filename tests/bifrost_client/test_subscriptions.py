"""
Tests for subscription operations.

Tests WebSocket subscription functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestSubscriptions:
    """Test subscription helpers."""

    @pytest.mark.asyncio
    async def test_subscribe_tool_events(self, bifrost_client_instance):
        """Test subscribing to tool events."""
        client = bifrost_client_instance
        handler = AsyncMock()

        with patch.object(client, "subscribe", AsyncMock(return_value="sub_123")):
            sub_id = await client.subscribe_tool_events(
                tool_name="entity_create",
                handler=handler,
                workspace_id="123"
            )

            assert sub_id == "sub_123"
            client.subscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_routing_events(self, bifrost_client_instance):
        """Test subscribing to routing events."""
        client = bifrost_client_instance
        handler = AsyncMock()

        with patch.object(client, "subscribe", AsyncMock(return_value="sub_456")):
            sub_id = await client.subscribe_routing_events(
                handler=handler,
                workspace_id="123"
            )

            assert sub_id == "sub_456"
            client.subscribe.assert_called_once()
