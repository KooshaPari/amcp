"""SmartCP Middleware.

Provides cross-cutting concerns for the MCP server.
"""

from middleware.resource_access_enforcement import (
    ResourceAccessEnforcementMiddleware,
)

__all__ = ["ResourceAccessEnforcementMiddleware"]
