"""
FastMCP Authentication Token Cache

Secure token cache with TTL using cachetools.TTLCache.
Provides both memory and file-based persistence with automatic expiration.
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Optional

import cachetools

from .models import Token


logger = logging.getLogger(__name__)


class TokenCache:
    """Secure token cache with TTL and file persistence.

    Uses cachetools.TTLCache for memory caching with automatic expiration.
    Provides optional file-based persistence for durability.
    """

    def __init__(self, cache_dir: str = ".mcp_token_cache", ttl_seconds: int = 3600):
        """Initialize token cache.

        Args:
            cache_dir: Directory for file-based cache storage
            ttl_seconds: Time-to-live for cached tokens in seconds (default: 1 hour)
        """
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds

        # In-memory TTL cache
        self._memory_cache: cachetools.TTLCache = cachetools.TTLCache(
            maxsize=100,
            ttl=ttl_seconds
        )

        self._setup_cache_dir()

    def _setup_cache_dir(self) -> None:
        """Setup cache directory with restricted permissions."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, mode=0o700)
        os.chmod(self.cache_dir, 0o700)

    def _get_cache_file(self, key: str) -> str:
        """Get cache file path for key.

        Uses SHA256 hash of the key for safe filename generation.
        """
        safe_key = hashlib.sha256(key.encode()).hexdigest()[:16]
        return os.path.join(self.cache_dir, f".{safe_key}.token")

    async def get(self, key: str) -> Optional[Token]:
        """Get token from cache.

        Checks memory cache first, then falls back to file cache.
        Automatically removes expired tokens.

        Args:
            key: Cache key

        Returns:
            Cached Token if valid and not expired, None otherwise
        """
        # Check memory cache first
        if key in self._memory_cache:
            token = self._memory_cache[key]
            if not token.is_expired():
                return token
            else:
                # Remove expired token from memory cache
                del self._memory_cache[key]

        # Check file cache as fallback
        cache_file = self._get_cache_file(key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    token = Token(
                        access_token=data["access_token"],
                        token_type=data["token_type"],
                        expires_in=data["expires_in"],
                        refresh_token=data.get("refresh_token"),
                        scope=data.get("scope"),
                        issued_at=datetime.fromisoformat(data["issued_at"])
                    )

                    if not token.is_expired():
                        # Cache in memory for future access
                        self._memory_cache[key] = token
                        return token
                    else:
                        # Remove expired token from file cache
                        os.remove(cache_file)
            except Exception as e:
                logger.error(f"Failed to read token cache: {e}")

        return None

    async def set(self, key: str, token: Token) -> None:
        """Store token in cache.

        Stores token in both memory cache (with TTL) and file cache (for persistence).

        Args:
            key: Cache key
            token: Token to cache
        """
        # Cache in memory (TTL automatically handled by TTLCache)
        self._memory_cache[key] = token

        # Cache to file for persistence
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, "w") as f:
                json.dump(token.to_dict(), f)
            os.chmod(cache_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to write token cache: {e}")

    async def clear(self, key: str) -> None:
        """Clear cached token.

        Removes token from both memory and file caches.

        Args:
            key: Cache key to clear
        """
        # Remove from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]

        # Remove from file cache
        cache_file = self._get_cache_file(key)
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except Exception as e:
                logger.error(f"Failed to remove cache file: {e}")

    async def clear_all(self) -> None:
        """Clear all cached tokens.

        Removes all tokens from both memory and file caches.
        """
        # Clear memory cache
        self._memory_cache.clear()

        # Clear file cache
        try:
            if os.path.exists(self.cache_dir):
                for filename in os.listdir(self.cache_dir):
                    if filename.startswith(".") and filename.endswith(".token"):
                        cache_file = os.path.join(self.cache_dir, filename)
                        os.remove(cache_file)
        except Exception as e:
            logger.error(f"Failed to clear cache directory: {e}")
