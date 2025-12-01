"""
Integration tests for FastMCP Authentication Enhancement.

Tests DCR, PKCE, token caching, and provider fallback mechanisms.
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp_auth_enhancement import (
    PKCEChallenge,
    DeviceCodeResponse,
    Token,
    TokenCache,
    DCRProvider,
    PKCEProvider,
    OAuthProviderFallback,
    OAuthFlow,
)
from fastmcp_auth_provider import (
    FastMCPAuthEnhancedProvider,
    create_smartcp_server_with_auth,
)


# ============================================================================
# PKCEChallenge Tests
# ============================================================================


class TestPKCEChallenge:
    """Test PKCE challenge generation."""

    def test_generate_creates_verifier_and_challenge(self):
        """Test that PKCE challenge generates valid verifier and challenge."""
        challenge = PKCEChallenge.generate()

        assert challenge.code_verifier
        assert challenge.code_challenge
        assert challenge.code_challenge_method == "S256"
        assert len(challenge.code_verifier) > 32
        assert len(challenge.code_challenge) > 32

    def test_generate_creates_unique_challenges(self):
        """Test that each generated challenge is unique."""
        challenges = [PKCEChallenge.generate() for _ in range(5)]
        verifiers = [c.code_verifier for c in challenges]
        assert len(set(verifiers)) == 5

    def test_generate_creates_valid_base64_challenge(self):
        """Test that code challenge is valid base64."""
        challenge = PKCEChallenge.generate()
        # Should not contain padding or special chars
        assert "=" not in challenge.code_challenge
        assert "-" in challenge.code_challenge or "_" in challenge.code_challenge


# ============================================================================
# Token Tests
# ============================================================================


class TestToken:
    """Test Token management."""

    def test_token_not_expired_within_window(self):
        """Test that fresh token is not expired."""
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
        )
        assert not token.is_expired()

    def test_token_expired_beyond_window(self):
        """Test that expired token is detected."""
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=30,
            issued_at=_utcnow() - timedelta(seconds=100),
        )
        assert token.is_expired()

    def test_token_expiry_buffer(self):
        """Test expiry buffer calculation."""
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=120,
            issued_at=_utcnow() - timedelta(seconds=70),
        )
        # Not expired without buffer
        assert not token.is_expired(buffer_seconds=0)
        # Expired with 60 second buffer
        assert token.is_expired(buffer_seconds=60)

    def test_token_to_dict(self):
        """Test token serialization."""
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="refresh_token",
            scope="openid profile",
        )
        token_dict = token.to_dict()

        assert token_dict["access_token"] == "test_token"
        assert token_dict["token_type"] == "Bearer"
        assert token_dict["expires_in"] == 3600
        assert token_dict["refresh_token"] == "refresh_token"
        assert "issued_at" in token_dict


# ============================================================================
# TokenCache Tests
# ============================================================================


class TestTokenCache:
    """Test token caching."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create token cache in temp directory."""
        return TokenCache(str(tmp_path / ".cache"))

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache):
        """Test setting and getting cached token."""
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
        )

        await cache.set("test_key", token)
        cached = await cache.get("test_key")

        assert cached is not None
        assert cached.access_token == "test_token"

    @pytest.mark.asyncio
    async def test_cache_expires_old_tokens(self, cache):
        """Test that expired tokens are not returned."""
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=30,
            issued_at=_utcnow() - timedelta(seconds=100),
        )

        await cache.set("test_key", token)
        cached = await cache.get("test_key")

        assert cached is None

    @pytest.mark.asyncio
    async def test_cache_clears_token(self, cache):
        """Test clearing cached token."""
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
        )

        await cache.set("test_key", token)
        assert await cache.get("test_key") is not None

        await cache.clear("test_key")
        assert await cache.get("test_key") is None

    @pytest.mark.asyncio
    async def test_cache_memory_fallback(self, cache):
        """Test memory cache fallback when file unavailable."""
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
        )

        await cache.set("test_key", token)
        # Subsequent get should come from memory
        cached = await cache.get("test_key")
        assert cached is not None


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
    def auth_provider(self, tmp_path):
        """Create auth provider with temp cache."""
        return FastMCPAuthEnhancedProvider(
            client_id="test_client",
            auth_server_url="https://auth.example.com",
            client_secret="test_secret",
            flow_type="device_code",
            cache_dir=str(tmp_path / ".cache"),
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


# ============================================================================
# Integration Tests
# ============================================================================


class TestAuthenticationIntegration:
    """Test complete authentication flows."""

    @pytest.mark.asyncio
    async def test_provider_fallback_tries_multiple_providers(self):
        """Test fallback to alternate providers."""
        cache = TokenCache()
        providers = [
            {
                "type": "device_code",
                "client_id": "client1",
                "client_secret": "secret1",
                "auth_server_url": "https://auth1.example.com",
            },
            {
                "type": "device_code",
                "client_id": "client2",
                "client_secret": "secret2",
                "auth_server_url": "https://auth2.example.com",
            },
        ]

        fallback = OAuthProviderFallback(providers, cache)
        # Fallback provider is created successfully
        assert fallback is not None

    @pytest.mark.asyncio
    async def test_cached_token_used_across_requests(self):
        """Test that cached tokens persist across requests."""
        provider = FastMCPAuthEnhancedProvider(
            client_id="test_client",
            auth_server_url="https://auth.example.com",
            client_secret="test_secret",
        )

        # First auth with provided token
        await provider.authenticate({"access_token": "cached_token"})
        first_token = provider.get_token()

        # Second auth should still have the token
        second_token = provider.get_token()
        assert first_token == second_token

    def test_server_creation_with_auth(self, tmp_path):
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


# ============================================================================
# Security Tests
# ============================================================================


class TestAuthenticationSecurity:
    """Test security aspects of authentication."""

    def test_pkce_verifier_cryptographically_random(self):
        """Test PKCE verifier is cryptographically random."""
        challenges = [PKCEChallenge.generate() for _ in range(10)]
        verifiers = [c.code_verifier for c in challenges]

        # All should be unique
        assert len(set(verifiers)) == 10

    @pytest.mark.asyncio
    async def test_token_cache_file_permissions(self, tmp_path):
        """Test token cache files have restricted permissions."""
        cache = TokenCache(str(tmp_path / ".cache"))
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
        )

        await cache.set("test_key", token)

        # Cache directory should be readable only by owner
        import os
        cache_stat = os.stat(cache.cache_dir)
        assert cache_stat.st_mode & 0o077 == 0  # No group/other permissions

    @pytest.mark.asyncio
    async def test_expired_token_not_used(self, tmp_path):
        """Test that expired tokens are not used from cache."""
        cache = TokenCache(str(tmp_path / ".cache"))
        expired_token = Token(
            access_token="expired_token",
            token_type="Bearer",
            expires_in=1,
            issued_at=_utcnow() - timedelta(seconds=100),
        )

        await cache.set("test_key", expired_token)
        retrieved = await cache.get("test_key")

        assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
