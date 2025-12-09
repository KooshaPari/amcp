"""SmartCP Authentication Package.

Provides bearer token authentication with JWT validation,
UserContext extraction for HTTP stateless operation,
and FastMCP enhanced authentication with DCR/PKCE flows.
"""

import logging
from typing import Optional

# FastMCP 2.13+ provides these directly
from fastmcp import FastMCP

# Re-export from submodules for clean public API
from .middleware import AuthMiddleware, create_auth_middleware
from .decorators import get_current_user_context, require_auth
from .token import (
    TokenValidator,
    JWTConfig,
    TokenPayload,
    create_token_validator,
)
from .context import (
    UserContextProvider,
    RequestContextManager,
    get_request_context,
    set_request_context,
)
from .provider import FastMCPAuthEnhancedProvider
from .session_manager import SessionManager
from .jwt_validator import JWTValidator

logger = logging.getLogger(__name__)


# FastMCP Enhanced Authentication Server
class FastMCPAuthEnhancedServer:
    """Mixin for FastMCP213Server adding enhanced authentication.

    Usage:
        server = FastMCPAuthEnhancedServer(config)
        await server.authenticate()
    """

    def __init__(self, *args, **kwargs):
        """Initialize mixin.

        Args:
            *args: Positional arguments for parent class
            **kwargs: Keyword arguments for parent class
        """
        super().__init__(*args, **kwargs)
        self._auth_enhanced: Optional[FastMCPAuthEnhancedProvider] = None

    def setup_enhanced_auth(
        self,
        client_id: str,
        auth_server_url: str,
        client_secret: Optional[str] = None,
        flow_type: str = "device_code",
        **kwargs,
    ) -> "FastMCPAuthEnhancedServer":
        """Setup enhanced authentication.

        Args:
            client_id: OAuth client ID
            auth_server_url: Authorization server URL
            client_secret: OAuth client secret
            flow_type: Authentication flow type
            **kwargs: Additional options

        Returns:
            Self for chaining
        """
        self._auth_enhanced = FastMCPAuthEnhancedProvider(
            client_id=client_id,
            auth_server_url=auth_server_url,
            client_secret=client_secret,
            flow_type=flow_type,
            **kwargs,
        )
        self.set_auth_provider(self._auth_enhanced)
        return self

    async def authenticate(self) -> bool:
        """Perform authentication.

        Returns:
            True if successful
        """
        if not self._auth_enhanced:
            logger.error("Enhanced auth not configured")
            return False

        return await self._auth_enhanced.authenticate({})


def create_smartcp_server_with_auth(
    name: str,
    client_id: str,
    auth_server_url: str,
    transport: str = "stdio",
    flow_type: str = "device_code",
    **kwargs,
):
    """Factory function to create SmartCP server with enhanced auth.

    Args:
        name: Server name
        client_id: OAuth client ID
        auth_server_url: Authorization server URL
        transport: Transport type
        flow_type: Authentication flow type
        **kwargs: Additional options

    Returns:
        Configured FastMCP server with enhanced auth
    """
    transport_map = {
        "stdio": TransportType.STDIO,
        "sse": TransportType.SSE,
        "http": TransportType.HTTP,
    }

    config = ServerConfig(
        name=name,
        transport=transport_map.get(transport, TransportType.STDIO),
    )

    # Create a hybrid class
    class SmartCPServerWithAuth(FastMCPAuthEnhancedServer, FastMCP213Server):
        """Combined server with auth support."""

        pass

    server = SmartCPServerWithAuth(config)
    server.setup_enhanced_auth(
        client_id=client_id,
        auth_server_url=auth_server_url,
        flow_type=flow_type,
        **kwargs,
    )

    return server

__all__ = [
    # Middleware
    "AuthMiddleware",
    "create_auth_middleware",
    "get_current_user_context",
    "require_auth",
    # Token validation
    "TokenValidator",
    "JWTConfig",
    "TokenPayload",
    "create_token_validator",
    # Context management
    "UserContextProvider",
    "RequestContextManager",
    "get_request_context",
    "set_request_context",
    # FastMCP Enhanced Auth
    "FastMCPAuthEnhancedProvider",
    "FastMCPAuthEnhancedServer",
    "create_smartcp_server_with_auth",
    "SessionManager",
    "JWTValidator",
]
