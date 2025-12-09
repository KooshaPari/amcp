"""Session and token caching management for FastMCP authentication."""

import asyncio
import logging
from typing import Optional

from smartcp.fastmcp_auth import Token, TokenCache

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages authentication sessions and token lifecycle."""

    def __init__(self, cache_dir: str = ".mcp_token_cache"):
        """Initialize session manager.

        Args:
            cache_dir: Directory for token cache storage
        """
        self.cache = TokenCache(cache_dir)
        self._current_token: Optional[str] = None

    async def get_cached_token(self) -> Optional[Token]:
        """Retrieve cached authentication token.

        Returns:
            Cached Token if valid and not expired, None otherwise
        """
        try:
            cached_token = await self.cache.get("mcp_auth_token")
            if cached_token and not cached_token.is_expired():
                logger.info("Using cached access token")
                return cached_token
        except Exception as e:
            logger.warning(f"Failed to retrieve cached token: {e}")
        return None

    async def cache_token(self, token: Token) -> None:
        """Cache an authentication token.

        Args:
            token: Token to cache
        """
        try:
            await self.cache.set("mcp_auth_token", token)
            self._current_token = token.access_token
            logger.info("Token cached successfully")
        except Exception as e:
            logger.error(f"Failed to cache token: {e}")

    def set_current_token(self, token_str: str) -> None:
        """Set the current active token.

        Args:
            token_str: Token string to set as current
        """
        self._current_token = token_str
        logger.info("Current token updated")

    def get_current_token(self) -> Optional[str]:
        """Get the current active token.

        Returns:
            Current token string or None
        """
        return self._current_token

    def has_valid_token(self) -> bool:
        """Check if a valid token is currently available.

        Returns:
            True if valid token exists
        """
        return self._current_token is not None

    async def clear_cache(self) -> None:
        """Clear all cached tokens and reset session.

        This is a synchronous-blocking operation wrapped for async context.
        """
        try:
            # Clear cache (async operation)
            await self.cache.clear("mcp_auth_token")
            self._current_token = None
            logger.info("Authentication cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    async def refresh_session(self, new_token: Token) -> None:
        """Refresh the current session with a new token.

        Args:
            new_token: New token to use for session
        """
        await self.cache_token(new_token)
        self._current_token = new_token.access_token

    async def invalidate_session(self) -> None:
        """Invalidate the current session.

        Clears all cached tokens and resets the current token.
        """
        await self.clear_cache()
        self._current_token = None
        logger.info("Session invalidated")

    async def validate_and_refresh_if_needed(
        self, cached_token: Optional[Token], refresh_callback=None
    ) -> bool:
        """Validate token and attempt refresh if expired.

        Args:
            cached_token: Token to validate
            refresh_callback: Optional async callback to refresh token

        Returns:
            True if token is valid (or was refreshed), False otherwise
        """
        if not cached_token:
            return False

        if not cached_token.is_expired():
            return True

        # Token expired, attempt refresh
        if refresh_callback:
            try:
                new_token = await refresh_callback()
                if new_token:
                    await self.refresh_session(new_token)
                    return True
            except Exception as e:
                logger.error(f"Token refresh callback failed: {e}")

        return False


class SyncSessionManager:
    """Synchronous wrapper for session management operations.

    Provides blocking operations for sync contexts (e.g., sync constructors).
    """

    def __init__(self, session_manager: SessionManager):
        """Initialize sync wrapper.

        Args:
            session_manager: Underlying async session manager
        """
        self._async_manager = session_manager

    def clear_cache_blocking(self) -> None:
        """Synchronously clear all cached tokens.

        Uses asyncio.run() to execute the async clear operation.
        """
        try:
            asyncio.run(self._async_manager.clear_cache())
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
