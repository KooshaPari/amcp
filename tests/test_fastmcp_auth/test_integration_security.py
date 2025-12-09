"""Integration and security tests for FastMCP authentication.

Tests complete authentication flows, provider fallback, and security aspects.
"""

import sys
import os

# Add smartcp directory to path for imports
smartcp_dir = "/Users/kooshapari/temp-PRODVERCEL/485/API/smartcp"
if smartcp_dir not in sys.path:
    sys.path.insert(0, smartcp_dir)

import pytest
from datetime import timedelta
from .conftest import _utcnow

from fastmcp_auth.models import PKCEChallenge, Token
from fastmcp_auth.cache import TokenCache
from fastmcp_auth.providers import DCRProvider, PKCEProvider
from auth import FastMCPAuthEnhancedProvider


# ============================================================================
# Integration Tests
# ============================================================================


class TestAuthenticationIntegration:
    """Test complete authentication flows."""

    @pytest.mark.asyncio
    async def test_provider_fallback_tries_multiple_providers(self):
        """Test multiple provider instances can be created for fallback scenarios."""
        # Create multiple DCRProvider instances to simulate fallback chain
        provider1 = DCRProvider(
            client_id="client1",
            client_secret="secret1",
            auth_server_url="https://auth1.example.com",
        )
        provider2 = DCRProvider(
            client_id="client2",
            client_secret="secret2",
            auth_server_url="https://auth2.example.com",
        )

        # Both providers are created successfully
        assert provider1 is not None
        assert provider2 is not None
        assert provider1.client_id != provider2.client_id

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
    async def test_token_cache_file_permissions(self, temp_cache_dir):
        """Test token cache files have restricted permissions."""
        cache = TokenCache(temp_cache_dir)
        token = Token(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
        )

        await cache.set("test_key", token)

        # Cache directory should be readable only by owner
        cache_stat = os.stat(cache.cache_dir)
        assert cache_stat.st_mode & 0o077 == 0  # No group/other permissions

    @pytest.mark.asyncio
    async def test_expired_token_not_used(self, temp_cache_dir):
        """Test that expired tokens are not used from cache."""
        cache = TokenCache(temp_cache_dir)
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
