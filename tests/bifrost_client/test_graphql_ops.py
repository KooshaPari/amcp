"""
Tests for GraphQL query and mutation operations.

Tests core GraphQL functionality including queries, mutations, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBifrostClientQueries:
    """Test GraphQL query execution."""

    @pytest.mark.asyncio
    async def test_query_success(self, bifrost_client_instance, mock_http_response):
        """Test successful query execution."""
        client = bifrost_client_instance
        mock_response = mock_http_response({"result": "success"})

        with patch.object(client, "http_client") as mock_http:
            mock_http.post = AsyncMock(return_value=mock_response)

            result = await client.query(
                query="query { test }",
                variables={"var": "value"}
            )

            assert result == {"result": "success"}
            mock_http.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_errors(self, bifrost_client_instance, mock_http_response):
        """Test query with GraphQL errors."""
        client = bifrost_client_instance
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errors": [{"message": "Field not found"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "http_client") as mock_http:
            mock_http.post = AsyncMock(return_value=mock_response)

            with pytest.raises(ValueError, match="GraphQL errors"):
                await client.query("query { invalid }")

    @pytest.mark.asyncio
    async def test_mutate(self, bifrost_client_instance, mock_http_response):
        """Test mutation execution."""
        client = bifrost_client_instance
        mock_response = mock_http_response({"created": True})

        with patch.object(client, "http_client") as mock_http:
            mock_http.post = AsyncMock(return_value=mock_response)

            result = await client.mutate(
                mutation="mutation { create }",
                variables={"input": "data"}
            )

            assert result == {"created": True}
