"""FastAPI dependencies for authentication and authorization.

Provides dependency functions for route handlers to access
authenticated user context and enforce permissions.
"""

import logging
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from smartcp.auth.context import get_request_context
from smartcp.services.models import UserContext

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme for FastAPI
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UserContext:
    """FastAPI dependency to get current UserContext.

    Use this in route handlers to get the authenticated user context.

    Example:
        @router.get("/items")
        async def list_items(user_ctx: UserContext = Depends(get_current_user_context)):
            return await service.list_items(user_ctx)

    Args:
        request: FastAPI request
        credentials: Optional bearer credentials

    Returns:
        UserContext for current request

    Raises:
        HTTPException: If no valid context is available
    """
    # First try request state (set by middleware)
    if hasattr(request.state, "user_context"):
        return request.state.user_context

    # Then try context var (set by middleware or manually)
    ctx = get_request_context()
    if ctx is not None:
        return ctx

    # No context available
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "message": "No authenticated user context available",
                "type": "authentication_error",
                "code": "no_context",
            }
        },
    )


def require_auth(permissions: Optional[list[str]] = None) -> Callable:
    """FastAPI dependency factory for permission-based authorization.

    Use this to require specific permissions on routes.

    Example:
        @router.post("/admin/action")
        async def admin_action(
            user_ctx: UserContext = Depends(require_auth(["admin:write"]))
        ):
            return await do_admin_action(user_ctx)

    Args:
        permissions: Required permissions (user must have all)

    Returns:
        Dependency function that validates permissions
    """
    required_permissions = permissions or []

    async def check_permissions(
        user_ctx: UserContext = Depends(get_current_user_context),
    ) -> UserContext:
        """Check if user has required permissions."""
        for perm in required_permissions:
            if not user_ctx.has_permission(perm):
                logger.warning(
                    "Permission denied",
                    extra={
                        "user_id": user_ctx.user_id,
                        "required_permission": perm,
                        "user_permissions": user_ctx.permissions,
                        "request_id": user_ctx.request_id,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "message": f"Permission denied: requires '{perm}'",
                            "type": "authorization_error",
                            "code": "permission_denied",
                        }
                    },
                )
        return user_ctx

    return check_permissions


def get_optional_user_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[UserContext]:
    """FastAPI dependency to get optional UserContext.

    Returns UserContext if available, None otherwise.
    Useful for routes that work with or without authentication.

    Example:
        @router.get("/public-items")
        async def list_items(
            user_ctx: Optional[UserContext] = Depends(get_optional_user_context)
        ):
            # Adjust behavior based on whether user is authenticated
            if user_ctx:
                return await service.list_items(user_ctx.user_id)
            return await service.list_public_items()

    Args:
        request: FastAPI request
        credentials: Optional bearer credentials

    Returns:
        UserContext if available, None otherwise
    """
    # Try request state (set by middleware)
    if hasattr(request.state, "user_context"):
        return request.state.user_context

    # Try context var (set by middleware or manually)
    ctx = get_request_context()
    if ctx is not None:
        return ctx

    # No context available, return None
    return None


def require_roles(roles: list[str]) -> Callable:
    """FastAPI dependency factory for role-based authorization.

    Use this to require specific roles on routes.

    Example:
        @router.post("/admin/users")
        async def create_user(
            user_ctx: UserContext = Depends(require_roles(["admin"]))
        ):
            return await do_admin_action(user_ctx)

    Args:
        roles: Required roles (user must have at least one)

    Returns:
        Dependency function that validates roles
    """
    required_roles = roles

    async def check_roles(
        user_ctx: UserContext = Depends(get_current_user_context),
    ) -> UserContext:
        """Check if user has required roles."""
        if not user_ctx.roles:
            logger.warning(
                "Role check failed: user has no roles",
                extra={
                    "user_id": user_ctx.user_id,
                    "required_roles": required_roles,
                    "request_id": user_ctx.request_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "message": f"Access denied: requires one of {required_roles}",
                        "type": "authorization_error",
                        "code": "role_required",
                    }
                },
            )

        has_role = any(role in user_ctx.roles for role in required_roles)
        if not has_role:
            logger.warning(
                "Role check failed",
                extra={
                    "user_id": user_ctx.user_id,
                    "required_roles": required_roles,
                    "user_roles": user_ctx.roles,
                    "request_id": user_ctx.request_id,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "message": f"Access denied: requires one of {required_roles}",
                        "type": "authorization_error",
                        "code": "role_required",
                    }
                },
            )

        return user_ctx

    return check_roles
