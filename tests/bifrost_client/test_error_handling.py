"""
Tests for error handling and cleanup.

Tests error handling, context manager, and resource cleanup.
"""

import pytest
from unittest.mock import AsyncMock, patch

from infrastructure.bifrost.client import BifrostClient


class TestContextManager:
    """Test context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using BifrostClient as context manager."""
        with patch("smartcp.infrastructure.bifrost.client.GraphQLSubscriptionClient.connect") as mock_connect:
            mock_connect.return_value = True

            async with BifrostClient(
                url="ws://test.com/graphql",
                api_key="test"
            ) as client:
                assert client is not None
                assert client.api_key == "test"


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_http_error(self, bifrost_client_instance):
        """Test handling HTTP errors."""
        client = bifrost_client_instance

        with patch.object(client, "http_client") as mock_http:
            mock_http.post = AsyncMock(side_effect=Exception("Connection failed"))

            with pytest.raises(Exception, match="Connection failed"):
                await client.query("query { test }")

    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self, bifrost_client_instance):
        """Test that disconnect cleans up resources."""
        client = bifrost_client_instance

        # Initialize HTTP client
        _ = client.http_client

        assert client._http_client is not None

        with patch("smartcp.infrastructure.bifrost.client.GraphQLSubscriptionClient.disconnect"):
            await client.disconnect()

        # HTTP client should be closed
        assert client._http_client is None
