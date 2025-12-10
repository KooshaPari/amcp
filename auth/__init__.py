"""SmartCP Authentication Module.

Provides JWT token validation and authentication middleware.
"""

from smartcp.auth.token import (
    JWTConfig,
    TokenPayload,
    TokenValidationError,
    TokenValidator,
    create_token_validator,
)
from smartcp.auth.middleware import (
    AuthMiddleware,
    create_auth_middleware,
    generate_request_id,
    get_request_id,
    get_user_context,
)

__all__ = [
    # Token validation
    "JWTConfig",
    "TokenPayload",
    "TokenValidationError",
    "TokenValidator",
    "create_token_validator",
    # Middleware
    "AuthMiddleware",
    "create_auth_middleware",
    "generate_request_id",
    "get_request_id",
    "get_user_context",
]
