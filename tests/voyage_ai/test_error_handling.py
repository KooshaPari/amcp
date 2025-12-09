"""Tests for error handling scenarios."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from services.embeddings import VoyageConfig, VoyageAIClient


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create client for error tests."""
        config = VoyageConfig(api_key="test-key")
        return VoyageAIClient(config)

    @pytest.mark.asyncio
    async def test_api_error_handling(self, client):
        """Test API error is handled."""
        with patch.object(
            client, '_make_request', new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = Exception("API Error: Rate limit exceeded")

            with pytest.raises(Exception) as exc_info:
                await client.embed("test", use_cache=False)

            assert "Rate limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, client):
        """Test invalid API key error."""
        with patch.object(
            client, '_make_request', new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = Exception("Invalid API key")

            with pytest.raises(Exception) as exc_info:
                await client.embed("test", use_cache=False)

            assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_handling(self, client):
        """Test timeout is handled."""
        with patch.object(
            client, '_make_request', new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = asyncio.TimeoutError()

            with pytest.raises(asyncio.TimeoutError):
                await client.embed("test", use_cache=False)
