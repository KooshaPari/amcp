"""
Shared fixtures and utilities for BifrostClient tests.

This module provides common fixtures used across all bifrost_client tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any


@pytest.fixture
def mock_http_response():
    """Mock HTTP response."""
    def _create_response(data: Dict[str, Any], status_code: int = 200):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = {"data": data}
        response.raise_for_status = MagicMock()
        return response
    return _create_response


@pytest.fixture
async def bifrost_client_instance():
    """Create BifrostClient instance for testing."""
    from infrastructure.bifrost.client import BifrostClient

    # Mock WebSocket connection
    with patch("smartcp.infrastructure.bifrost.client.GraphQLSubscriptionClient.connect") as mock_connect:
        mock_connect.return_value = True
        client = BifrostClient(
            url="ws://localhost:4000/graphql",
            api_key="test_key"
        )
        # Don't actually connect WebSocket in tests
        client._state = MagicMock()
        yield client
        # Cleanup
        if client._http_client:
            await client._http_client.aclose()
