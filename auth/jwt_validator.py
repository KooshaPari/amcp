"""JWT validation and PKCE flow logic for FastMCP authentication."""

import logging
import secrets
from typing import Optional

from smartcp.fastmcp_auth import (
    DCRProvider,
    PKCEProvider,
    Token,
    PKCEChallenge,
)

logger = logging.getLogger(__name__)


class PKCEValidator:
    """Handles PKCE flow validation and initialization."""

    def __init__(self, pkce_provider: Optional[PKCEProvider] = None):
        """Initialize PKCE validator.

        Args:
            pkce_provider: Optional PKCE provider instance
        """
        self._pkce_provider = pkce_provider

    async def initiate_pkce_flow(self) -> Optional[Token]:
        """Initiate PKCE authentication flow.

        Returns:
            Token if successful, None otherwise
        """
        if not self._pkce_provider:
            return None

        try:
            challenge = PKCEChallenge.generate()
            state = secrets.token_urlsafe(32)

            auth_url = self._pkce_provider.get_authorization_url(challenge, state)
            print(f"\n🔐 PKCE Authorization Required\n")
            print(f"  Open this URL in your browser:")
            print(f"  {auth_url}\n")
            print(f"  Waiting for authorization...\n")

            # In production, would use callback handler
            # This is a placeholder for the full PKCE flow
            logger.info("PKCE flow initiated - waiting for callback")
            return None

        except Exception as e:
            logger.error(f"PKCE flow error: {e}")
            return None

    async def refresh_token_via_pkce(
        self, refresh_token: str
    ) -> Optional[Token]:
        """Refresh token using PKCE provider.

        Args:
            refresh_token: The refresh token string

        Returns:
            New Token if successful, None otherwise
        """
        if not self._pkce_provider:
            logger.warning("PKCE provider not available for refresh")
            return None

        try:
            return await self._pkce_provider.refresh_token(refresh_token)
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None


class DeviceCodeValidator:
    """Handles device code flow validation."""

    def __init__(self, dcr_provider: Optional[DCRProvider] = None):
        """Initialize device code validator.

        Args:
            dcr_provider: Optional DCR provider instance
        """
        self._dcr_provider = dcr_provider

    async def initiate_device_code_flow(self) -> Optional[Token]:
        """Initiate device code authentication flow.

        Returns:
            Token if successful, None otherwise
        """
        if not self._dcr_provider:
            return None

        try:
            result = await self._dcr_provider.start_device_flow()
            if result:
                token_str, issued_at = result
                return Token(
                    access_token=token_str,
                    token_type="Bearer",
                    expires_in=3600,
                    issued_at=issued_at,
                )
            return None
        except Exception as e:
            logger.error(f"Device code flow error: {e}")
            return None


class JWTValidator:
    """Combined JWT validator for FastMCP auth flows."""

    def __init__(
        self,
        dcr_provider: Optional[DCRProvider] = None,
        pkce_provider: Optional[PKCEProvider] = None,
    ):
        """Initialize JWT validator with auth providers.

        Args:
            dcr_provider: Optional device code flow provider
            pkce_provider: Optional PKCE flow provider
        """
        self.device_code_validator = DeviceCodeValidator(dcr_provider)
        self.pkce_validator = PKCEValidator(pkce_provider)

    async def validate_cached_token(
        self, cached_token: Optional[Token]
    ) -> bool:
        """Validate if cached token is still valid.

        Args:
            cached_token: The cached token to validate

        Returns:
            True if token is valid and not expired
        """
        if not cached_token:
            return False
        return not cached_token.is_expired()
