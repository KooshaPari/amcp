"""Tests for OAuth providers (DCR, PKCE, FastMCP Auth).

Tests Device Code Request provider, PKCE provider, and FastMCP enhanced auth provider.
"""

import sys
import os

# Add smartcp directory to path for imports
smartcp_dir = "/Users/kooshapari/temp-PRODVERCEL/485/API/smartcp"
if smartcp_dir not in sys.path:
    sys.path.insert(0, smartcp_dir)

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, patch
from .conftest import _utcnow

from fastmcp_auth.models import PKCEChallenge, DeviceCodeResponse
from fastmcp_auth.providers import DCRProvider, PKCEProvider
from auth import (
    FastMCPAuthEnhancedProvider,
    create_smartcp_server_with_auth,
)


# ============================================================================
# DCRProvider Tests
# ============================================================================


class TestDCRProvider:
    """Test Device Code Request flow."""

    @pytest.fixture
    def dcr_provider(self):
        """Create DCR provider."""
        return DCRProvider(
            client_id="test_client",
            client_secret="test_secret",
            auth_server_url="https://auth.example.com",
        )

    @pytest.mark.asyncio
    async def test_device_code_response_not_expired(self):
        """Test device code expiry detection."""
        response = DeviceCodeResponse(
            device_code="test_code",
            user_code="TEST-1234",
            verification_uri="https://auth.example.com/device",
            verification_uri_complete=None,
            expires_in=600,
            interval=5,
        )

        issued_at = _utcnow()
        assert not response.is_expired(issued_at)

    @pytest.mark.asyncio
    async def test_device_code_response_expired(self):
        """Test expired device code detection."""
        response = DeviceCodeResponse(
            device_code="test_code",
            user_code="TEST-1234",
            verification_uri="https://auth.example.com/device",
            verification_uri_complete=None,
            expires_in=30,
            interval=5,
        )

        issued_at = _utcnow() - timedelta(seconds=100)
        assert response.is_expired(issued_at)


# ============================================================================
# PKCEProvider Tests
# ============================================================================


class TestPKCEProvider:
    """Test PKCE flow."""

    @pytest.fixture
    def pkce_provider(self):
        """Create PKCE provider."""
        return PKCEProvider(
            client_id="test_client",
            client_secret="test_secret",
            auth_server_url="https://auth.example.com",
            redirect_uri="http://localhost:8080/callback",
        )

    def test_authorization_url_generation(self, pkce_provider):
        """Test authorization URL generation with PKCE."""
        challenge = PKCEChallenge.generate()
        state = "test_state"

        url = pkce_provider.get_authorization_url(challenge, state)

        assert "client_id=test_client" in url
        assert f"code_challenge={challenge.code_challenge}" in url
        assert "code_challenge_method=S256" in url
        assert "state=test_state" in url
        # Scope may be URL-encoded or not
        assert "scope=openid" in url and "profile" in url

    @pytest.mark.asyncio
    async def test_token_refresh(self, pkce_provider):
        """Test token refresh flow."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "new_refresh",
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            token = await pkce_provider.refresh_token("old_refresh_token")

            assert token is not None
            assert token.access_token == "new_token"
            assert token.refresh_token == "new_refresh"


# ============================================================================
# FastMCPAuthEnhancedProvider Tests
# ============================================================================


class TestFastMCPAuthEnhancedProvider:
    """Test FastMCP enhanced auth provider."""

    @pytest.fixture
    def auth_provider(self, temp_cache_dir):
        """Create auth provider with temp cache."""
        return FastMCPAuthEnhancedProvider(
            client_id="test_client",
            auth_server_url="https://auth.example.com",
            client_secret="test_secret",
            flow_type="device_code",
            cache_dir=temp_cache_dir,
        )

    @pytest.mark.asyncio
    async def test_authenticate_with_provided_token(self, auth_provider):
        """Test authentication with provided token."""
        result = await auth_provider.authenticate({
            "access_token": "provided_token"
        })

        assert result is True
        assert auth_provider.get_token() == "provided_token"

    @pytest.mark.asyncio
    async def test_get_token_returns_current_token(self, auth_provider):
        """Test getting current token."""
        await auth_provider.authenticate({
            "access_token": "test_token"
        })

        token = auth_provider.get_token()
        assert token == "test_token"

    @pytest.mark.asyncio
    async def test_authorize_with_valid_token(self, auth_provider):
        """Test authorization check."""
        await auth_provider.authenticate({
            "access_token": "test_token"
        })

        result = await auth_provider.authorize("user1", "/mcp/resource")
        assert result is True

    @pytest.mark.asyncio
    async def test_authorize_without_token(self, auth_provider):
        """Test authorization fails without token."""
        result = await auth_provider.authorize("user1", "/mcp/resource")
        assert result is False

    def test_clear_cache(self, auth_provider):
        """Test cache clearing."""
        auth_provider.clear_cache()
        # Should not raise
        assert auth_provider.get_token() is None

    def test_server_creation_with_auth(self, temp_cache_dir):
        """Test creating FastMCP server with enhanced auth."""
        server = create_smartcp_server_with_auth(
            name="test_server",
            client_id="test_client",
            auth_server_url="https://auth.example.com",
            client_secret="test_secret",
            transport="stdio",
            flow_type="device_code",
        )

        assert server is not None
        assert server._auth_enhanced is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
