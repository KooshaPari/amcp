"""
Tests for BifrostClient initialization.

Tests client initialization with various configurations.
"""

import pytest
from unittest.mock import patch

from smartcp.infrastructure.bifrost import BifrostClient


class TestBifrostClientInit:
    """Test BifrostClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        with patch.dict("os.environ", {
            "BIFROST_URL": "ws://test.com/graphql",
            "BIFROST_API_KEY": "env_key"
        }):
            client = BifrostClient()
            assert client.url == "ws://test.com/graphql"
            assert client.api_key == "env_key"
            assert client.timeout == 30.0

    def test_init_with_explicit_values(self):
        """Test initialization with explicit values."""
        client = BifrostClient(
            url="ws://custom.com/graphql",
            api_key="custom_key",
            timeout=60.0
        )
        assert client.url == "ws://custom.com/graphql"
        assert client.api_key == "custom_key"
        assert client.timeout == 60.0

    def test_headers_with_api_key(self):
        """Test that API key is added to headers."""
        client = BifrostClient(api_key="test_key")
        headers = client.config.headers
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_key"
