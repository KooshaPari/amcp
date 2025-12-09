"""FastMCP Enhanced Authentication Provider with DCR and PKCE support."""

import logging
import os
from typing import Any, Dict, Optional

from fastmcp.server.auth import AuthProvider
from auth.oauth_providers import DCRProvider, PKCEProvider
from auth.oauth_models import Token

from smartcp.auth.jwt_validator import JWTValidator
from smartcp.auth.session_manager import SessionManager

logger = logging.getLogger(__name__)


class FastMCPAuthEnhancedProvider(AuthenticationProvider):
    """Enhanced OAuth provider for FastMCP with DCR and PKCE support.

    Provides automatic authentication flows and token caching.
    """

    def __init__(
        self,
        client_id: str,
        auth_server_url: str,
        client_secret: Optional[str] = None,
        flow_type: str = "device_code",
        cache_dir: str = ".mcp_token_cache",
        enable_fallback: bool = True,
    ):
        """Initialize enhanced auth provider.

        Args:
            client_id: OAuth client ID
            auth_server_url: Authorization server URL
            client_secret: OAuth client secret (optional for public clients)
            flow_type: Flow type - "device_code", "pkce", or "auto"
            cache_dir: Token cache directory
            enable_fallback: Enable provider fallback mechanism
        """
        self.client_id = client_id
        self.auth_server_url = auth_server_url
        self.client_secret = client_secret or os.getenv("OAUTH_CLIENT_SECRET", "")
        self.flow_type = flow_type
        self.enable_fallback = enable_fallback

        # Initialize session manager
        self.session_manager = SessionManager(cache_dir)

        # Initialize auth providers
        self._dcr_provider: Optional[DCRProvider] = None
        self._pkce_provider: Optional[PKCEProvider] = None
        self._initialize_providers()

        # Initialize JWT validator
        self.validator = JWTValidator(self._dcr_provider, self._pkce_provider)

        logger.info(f"FastMCP Enhanced Auth Provider initialized (flow={flow_type})")

    def _initialize_providers(self) -> None:
        """Initialize authentication providers based on flow type."""
        if self.flow_type in ("device_code", "auto"):
            self._dcr_provider = DCRProvider(
                client_id=self.client_id,
                client_secret=self.client_secret,
                auth_server_url=self.auth_server_url,
            )

        if self.flow_type in ("pkce", "auto"):
            redirect_uri = os.getenv(
                "OAUTH_REDIRECT_URI", "http://localhost:8080/callback"
            )
            self._pkce_provider = PKCEProvider(
                client_id=self.client_id,
                client_secret=self.client_secret,
                auth_server_url=self.auth_server_url,
                redirect_uri=redirect_uri,
            )

    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate using available credentials or initiate auth flow.

        Supports:
        1. Pre-existing token in credentials
        2. Cached token
        3. Automatic device code flow
        4. PKCE flow with manual authorization

        Args:
            credentials: Authentication credentials dict

        Returns:
            True if authentication successful
        """
        # Check for pre-existing token
        if "access_token" in credentials:
            self.session_manager.set_current_token(credentials["access_token"])
            logger.info("Using provided access token")
            return True

        # Try to get cached token
        cached_token = await self.session_manager.get_cached_token()
        if cached_token and not cached_token.is_expired():
            self.session_manager.set_current_token(cached_token.access_token)
            logger.info("Using cached access token")
            return True

        # Initiate device code flow if available
        if self._dcr_provider:
            logger.info("Initiating device code flow")
            try:
                token = await self.validator.device_code_validator.initiate_device_code_flow()
                if token:
                    await self.session_manager.cache_token(token)
                    return True
            except Exception as e:
                logger.error(f"Device code flow failed: {e}")
                if not self.enable_fallback:
                    return False

        # Initiate PKCE flow if available
        if self._pkce_provider:
            logger.info("Initiating PKCE flow")
            try:
                token = await self.validator.pkce_validator.initiate_pkce_flow()
                if token:
                    await self.session_manager.cache_token(token)
                    return True
            except Exception as e:
                logger.error(f"PKCE flow failed: {e}")

        logger.error("All authentication flows failed")
        return False

    async def authorize(self, user: str, resource: str) -> bool:
        """Authorize access to resource.

        Args:
            user: User identifier
            resource: Resource to access

        Returns:
            True if authorized
        """
        if not self.session_manager.has_valid_token():
            logger.warning("No valid token available for authorization")
            return False

        # In real implementation, would validate token scope against resource
        logger.info(f"User {user} authorized for {resource}")
        return True

    async def refresh_token(self) -> bool:
        """Attempt to refresh current token.

        Returns:
            True if refresh successful
        """
        cached_token = await self.session_manager.get_cached_token()
        if not cached_token or not cached_token.refresh_token:
            logger.warning("No cached token or refresh token available")
            return False

        if not self._pkce_provider:
            logger.warning("PKCE provider not available for refresh")
            return False

        try:
            new_token = await self.validator.pkce_validator.refresh_token_via_pkce(
                cached_token.refresh_token
            )
            if new_token:
                await self.session_manager.refresh_session(new_token)
                logger.info("Token refreshed successfully")
                return True
        except Exception as e:
            logger.error(f"Token refresh error: {e}")

        return False

    def get_token(self) -> Optional[str]:
        """Get current access token.

        Returns:
            Current token string or None
        """
        return self.session_manager.get_current_token()

    def clear_cache(self) -> None:
        """Clear all cached tokens.

        Uses synchronous blocking operation for sync contexts.
        """
        from smartcp.auth.session_manager import SyncSessionManager

        sync_manager = SyncSessionManager(self.session_manager)
        sync_manager.clear_cache_blocking()
