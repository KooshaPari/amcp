"""SmartCP Authentication Package.

Provides bearer token authentication with JWT validation,
UserContext extraction for HTTP stateless operation,
and FastMCP enhanced authentication with DCR/PKCE flows.

Uses lazy imports to avoid circular dependencies.
"""

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """Lazy load modules to avoid import-time dependency issues."""
    if name == "AuthMiddleware":
        from smartcp.auth.middleware import AuthMiddleware
        return AuthMiddleware
    elif name == "create_auth_middleware":
        from smartcp.auth.middleware import create_auth_middleware
        return create_auth_middleware
    elif name == "get_current_user_context":
        from smartcp.auth.decorators import get_current_user_context
        return get_current_user_context
    elif name == "require_auth":
        from smartcp.auth.decorators import require_auth
        return require_auth
    elif name == "TokenValidator":
        from smartcp.auth.token import TokenValidator
        return TokenValidator
    elif name == "JWTConfig":
        from smartcp.auth.token import JWTConfig
        return JWTConfig
    elif name == "TokenPayload":
        from smartcp.auth.token import TokenPayload
        return TokenPayload
    elif name == "create_token_validator":
        from smartcp.auth.token import create_token_validator
        return create_token_validator
    elif name == "UserContextProvider":
        from smartcp.auth.context import UserContextProvider
        return UserContextProvider
    elif name == "RequestContextManager":
        from smartcp.auth.context import RequestContextManager
        return RequestContextManager
    elif name == "get_request_context":
        from smartcp.auth.context import get_request_context
        return get_request_context
    elif name == "set_request_context":
        from smartcp.auth.context import set_request_context
        return set_request_context
    elif name == "FastMCPAuthEnhancedProvider":
        from smartcp.auth.provider import FastMCPAuthEnhancedProvider
        return FastMCPAuthEnhancedProvider
    elif name == "FastMCPAuthEnhancedServer":
        from smartcp.auth.server import FastMCPAuthEnhancedServer
        return FastMCPAuthEnhancedServer
    elif name == "create_smartcp_server_with_auth":
        from smartcp.auth.server import create_smartcp_server_with_auth
        return create_smartcp_server_with_auth
    elif name == "SessionManager":
        from smartcp.auth.session_manager import SessionManager
        return SessionManager
    elif name == "JWTValidator":
        from smartcp.auth.jwt_validator import JWTValidator
        return JWTValidator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
