"""SmartCP - User-Scoped MCP Server.

SmartCP provides an HTTP stateless MCP server with:
- Bearer token authentication (Supabase JWT)
- User-scoped state management
- Sandboxed Python code execution
- Persistent memory across requests

Quick Start:
    from smartcp import create_server

    # Create and run server
    server = create_server()
    server.run()

For serverless deployment (Vercel):
    from smartcp.server import create_app
    app = create_app()

Package Structure:
    smartcp/
    ├── auth/           # Authentication (JWT, middleware, context)
    ├── config/         # Configuration schemas
    ├── infrastructure/ # External adapters (Supabase, state)
    ├── migrations/     # Database migrations
    ├── models/         # Pydantic schemas
    ├── services/       # Business logic (memory, executor)
    └── tools/          # MCP tool implementations
"""

__version__ = "0.1.0"
__author__ = "SmartCP Team"

# Main exports - commented out to avoid import errors during pytest
# These will be fixed when package structure is properly set up
# from server import SmartCPServer, create_server, create_app

# Auth exports - commented out temporarily
# from auth import (
#     AuthMiddleware,
#     TokenValidator,
#     JWTConfig,
#     TokenPayload,
#     UserContextProvider,
#     RequestContextManager,
#     get_request_context,
#     set_request_context,
#     get_current_user_context,
#     require_auth,
# )

# Model exports - commented out (models don't exist yet)
# from models.schemas import (
#     UserContext,
#     ExecuteCodeRequest,
#     ExecuteCodeResponse,
#     ExecutionLanguage,
#     ExecutionStatus,
# )

# Service exports - commented out temporarily
# from services import (
#     UserScopedMemory,
#     UserScopedExecutor,
#     MemoryType,
#     MemoryItem,
#     create_memory_service,
#     create_executor_service,
# )

# Infrastructure exports - commented out temporarily
# from infrastructure import (
#     SupabaseAdapter,
#     SupabaseConfig,
#     StateAdapter,
#     SupabaseStateAdapter,
#     create_supabase_adapter,
#     create_state_adapter,
# )

__all__ = [
    # Version
    "__version__",
    # Server - commented out temporarily
    # "SmartCPServer",
    # "create_server",
    # "create_app",
    # Auth - commented out temporarily
    # "AuthMiddleware",
    # "TokenValidator",
    # "JWTConfig",
    # "TokenPayload",
    # "UserContextProvider",
    # "RequestContextManager",
    # "get_request_context",
    # "set_request_context",
    # "get_current_user_context",
    # "require_auth",
    # Models - commented out temporarily
    # "UserContext",
    # "ExecuteCodeRequest",
    # "ExecuteCodeResponse",
    # "ExecutionLanguage",
    # "ExecutionStatus",
    # Services - commented out temporarily
    # "UserScopedMemory",
    # "UserScopedExecutor",
    # "MemoryType",
    # "MemoryItem",
    # "create_memory_service",
    # "create_executor_service",
    # Infrastructure - commented out temporarily
    # "SupabaseAdapter",
    # "SupabaseConfig",
    # "StateAdapter",
    # "SupabaseStateAdapter",
    # "create_supabase_adapter",
    # "create_state_adapter",
]
