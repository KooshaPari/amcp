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

__all__ = [
    "__version__",
]
