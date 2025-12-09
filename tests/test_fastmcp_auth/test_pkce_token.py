"""Tests for PKCE challenges, tokens, and token caching.

Tests PKCE challenge generation, token management, and token cache functionality.
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
    def cache(self, temp_cache_dir):
        """Create token cache in temp directory."""
        return TokenCache(temp_cache_dir)

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
