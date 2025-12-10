"""Tests for bifrost_client.py - GraphQL client for Bifrost backend."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bifrost_client import (
    BifrostClient,
    BifrostClientConfig,
    DEFAULT_BIFROST_URL,
    DEFAULT_TIMEOUT_SECONDS,
)


# =============================================================================
# BifrostClientConfig Tests
# =============================================================================


class TestBifrostClientConfig:
    """Tests for BifrostClientConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            config = BifrostClientConfig()
            assert config.url == DEFAULT_BIFROST_URL
            assert config.api_key is None
            assert config.timeout_seconds == DEFAULT_TIMEOUT_SECONDS

    def test_env_overrides(self):
        """Test that environment variables override defaults."""
        with patch.dict(
            os.environ,
            {
                "BIFROST_URL": "http://custom:9090/graphql",
                "BIFROST_API_KEY": "test-api-key",
            },
        ):
            config = BifrostClientConfig()
            assert config.url == "http://custom:9090/graphql"
            assert config.api_key == "test-api-key"

    def test_explicit_values(self):
        """Test explicit configuration values."""
        config = BifrostClientConfig(
            url="http://localhost:3000/graphql",
            api_key="my-key",
            timeout_seconds=60.0,
        )
        assert config.url == "http://localhost:3000/graphql"
        assert config.api_key == "my-key"
        assert config.timeout_seconds == 60.0


# =============================================================================
# BifrostClient Tests
# =============================================================================


class TestBifrostClient:
    """Tests for BifrostClient."""

    def test_init_default_config(self):
        """Test client initialization with default config."""
        client = BifrostClient()
        assert client.config is not None
        assert client._client is None
        assert client.is_connected is False

    def test_init_custom_config(self):
        """Test client initialization with custom config."""
        config = BifrostClientConfig(url="http://test:8080/graphql")
        client = BifrostClient(config)
        assert client.config.url == "http://test:8080/graphql"

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connect method."""
        client = BifrostClient()
        assert client.is_connected is False

        await client.connect()
        assert client.is_connected is True
        assert client._client is not None

        await client.close()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect method."""
        client = BifrostClient()
        await client.connect()
        assert client.is_connected is True

        await client.disconnect()
        assert client.is_connected is False
        assert client._client is None

    @pytest.mark.asyncio
    async def test_ensure_client_creates_client(self):
        """Test _ensure_client creates httpx client."""
        client = BifrostClient()
        assert client._client is None

        http_client = await client._ensure_client()
        assert http_client is not None
        assert client._client is http_client

        await client.close()

    @pytest.mark.asyncio
    async def test_ensure_client_with_api_key(self):
        """Test _ensure_client sets authorization header."""
        config = BifrostClientConfig(api_key="test-key")
        client = BifrostClient(config)

        http_client = await client._ensure_client()
        assert "Authorization" in http_client.headers
        assert http_client.headers["Authorization"] == "Bearer test-key"

        await client.close()

    @pytest.mark.asyncio
    async def test_close_clears_client(self):
        """Test close method clears client."""
        client = BifrostClient()
        await client._ensure_client()
        assert client._client is not None

        await client.close()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_idempotent(self):
        """Test close is safe to call multiple times."""
        client = BifrostClient()
        await client.close()  # No client yet
        await client._ensure_client()
        await client.close()
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_query_success(self):
        """Test successful GraphQL query."""
        client = BifrostClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"result": "success"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_ensure.return_value = mock_http

            result = await client.query("query { test }")
            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_query_with_variables(self):
        """Test query with variables."""
        client = BifrostClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"user": {"id": "123"}}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_ensure.return_value = mock_http

            result = await client.query(
                "query GetUser($id: ID!) { user(id: $id) { id } }",
                variables={"id": "123"},
            )
            assert result == {"user": {"id": "123"}}

            # Verify post was called with correct payload
            call_args = mock_http.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["variables"] == {"id": "123"}

    @pytest.mark.asyncio
    async def test_mutate_success(self):
        """Test successful GraphQL mutation."""
        client = BifrostClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"createUser": {"id": "new-123"}}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_ensure.return_value = mock_http

            result = await client.mutate(
                "mutation CreateUser($name: String!) { createUser(name: $name) { id } }",
                variables={"name": "Test"},
            )
            assert result == {"createUser": {"id": "new-123"}}

    @pytest.mark.asyncio
    async def test_execute_graphql_errors(self):
        """Test handling of GraphQL errors in response."""
        client = BifrostClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errors": [{"message": "Field not found"}],
            "data": None,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_ensure.return_value = mock_http

            with pytest.raises(RuntimeError) as exc_info:
                await client.query("query { invalid }")

            assert "Field not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Test handling of HTTP errors."""
        client = BifrostClient()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
            mock_ensure.return_value = mock_http

            with pytest.raises(httpx.HTTPError):
                await client.query("query { test }")

    @pytest.mark.asyncio
    async def test_health_success(self):
        """Test successful health check."""
        client = BifrostClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"__typename": "Query"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_ensure.return_value = mock_http

            result = await client.health()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_failure(self):
        """Test health check failure."""
        client = BifrostClient()

        with patch.object(client, "_ensure_client") as mock_ensure:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=Exception("Connection refused"))
            mock_ensure.return_value = mock_http

            result = await client.health()
            assert result is False

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        config = BifrostClientConfig()
        client = BifrostClient(config)

        async with client as c:
            assert c is client
            assert client._client is not None

        assert client._client is None

    @pytest.mark.asyncio
    async def test_context_manager_exception(self):
        """Test context manager cleanup on exception."""
        client = BifrostClient()

        try:
            async with client:
                assert client._client is not None
                raise ValueError("Test error")
        except ValueError:
            pass

        assert client._client is None
