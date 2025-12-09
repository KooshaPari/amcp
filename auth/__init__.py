"""SmartCP Authentication Package.

Provides bearer token authentication with JWT validation,
UserContext extraction for HTTP stateless operation,
and FastMCP enhanced authentication with DCR/PKCE flows.
"""

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
from .server import (
    FastMCPAuthEnhancedServer,
    create_smartcp_server_with_auth,
)
from .session_manager import SessionManager
from .jwt_validator import JWTValidator

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
