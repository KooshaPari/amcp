"""SmartCP MCP Server.

Main server module that wires together all components for the
HTTP stateless MCP server with bearer token authentication.
"""

import logging
import os
from typing import Any, Optional

from auth.context import UserContextProvider
from auth.middleware import AuthMiddleware, create_auth_middleware
from auth.token import JWTConfig, TokenValidator, create_token_validator
from config.settings import SmartCPSettings, get_settings
from smartcp.infrastructure.state import StateAdapter, create_state_adapter
from smartcp.bifrost_client import BifrostClient, BifrostClientConfig
from middleware.resource_access_enforcement import (
    ResourceAccessEnforcementMiddleware,
)
from services.executor import UserScopedExecutor, create_executor_service
from services.memory import UserScopedMemory, create_memory_service
from tools import register_execute_tool, register_memory_tool, register_state_tools

logger = logging.getLogger(__name__)


class SmartCPServer:
    """SmartCP MCP Server.

    Provides an HTTP stateless MCP server with:
    - Bearer token authentication
    - User-scoped state management
    - Sandboxed code execution
    - Persistent memory across requests

    Usage:
        # Create server
        server = SmartCPServer.create()

        # Get FastMCP instance for tool registration
        mcp = server.mcp

        # Get FastAPI app for HTTP serving
        app = server.create_fastapi_app()

        # Or run directly
        server.run()
    """

    def __init__(
        self,
        settings: SmartCPSettings,
        mcp: Any,
        bifrost_client: Optional[BifrostClient],
        state: StateAdapter,
        memory: UserScopedMemory,
        executor: UserScopedExecutor,
        token_validator: TokenValidator,
    ):
        """Initialize server with all dependencies.

        Args:
            settings: Application settings
            mcp: FastMCP server instance
            state: State adapter (delegates to Bifrost)
            memory: Memory service
            executor: Executor service
            token_validator: JWT token validator
        """
        self.settings = settings
        self.mcp = mcp
        self.bifrost_client = bifrost_client
        self.state = state
        self.memory = memory
        self.executor = executor
        self.token_validator = token_validator

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all MCP tools."""
        register_execute_tool(self.mcp, self.executor)
        register_memory_tools(self.mcp, self.memory)
        register_state_tools(self.mcp, self.state)

        logger.info("All MCP tools registered")

    def create_fastapi_app(self) -> Any:
        """Create FastAPI application with authentication.

        Returns:
            Configured FastAPI application
        """
        from fastapi import FastAPI

        # Get the underlying Starlette app from FastMCP
        app = self.mcp.http_app()

        # Wrap in FastAPI for additional features
        fastapi_app = FastAPI(
            title="SmartCP MCP Server",
            description="MCP server with user-scoped state management",
            version=self.settings.version,
        )

        # Mount MCP routes
        fastapi_app.mount("/mcp", app)

        # Add resource access enforcement middleware (Phase 5.1 remediation)
        # Prevents direct DB imports and ensures bifrost delegation
        fastapi_app.add_middleware(
            ResourceAccessEnforcementMiddleware,
            enforce=False,  # Audit mode by default, set True in strict env
            log_violations=True,
        )

        # Add authentication middleware
        auth_middleware = create_auth_middleware(
            token_validator=self.token_validator,
            skip_paths={"/health", "/healthz", "/ready", "/metrics"},
            require_auth=True,
        )
        fastapi_app.add_middleware(auth_middleware)

        # Add health endpoints
        @fastapi_app.get("/health")
        @fastapi_app.get("/healthz")
        async def health_check():
            return {"status": "healthy", "version": self.settings.version}

        @fastapi_app.get("/ready")
        async def readiness_check():
            backend_status = "unknown"
            if self.bifrost_client:
                healthy = await self.bifrost_client.health()
                backend_status = "connected" if healthy else "disconnected"
            else:
                backend_status = "not_configured"

            return {
                "status": "ready" if backend_status == "connected" else "degraded",
                "backend": backend_status,
                "version": self.settings.version,
            }

        return fastapi_app

    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = False,
    ) -> None:
        """Run the server.

        Args:
            host: Host to bind to
            port: Port to listen on
            reload: Enable hot reload for development
        """
        import uvicorn

        app = self.create_fastapi_app()

        logger.info(f"Starting SmartCP MCP Server on {host}:{port}")

        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
        )

    @classmethod
    def create(
        cls,
        settings: Optional[SmartCPSettings] = None,
    ) -> "SmartCPServer":
        """Factory method to create a fully configured server.

        Args:
            settings: Optional settings (loaded from env if not provided)

        Returns:
            Configured SmartCPServer instance
        """
        # Load settings
        if settings is None:
            settings = get_settings()

        logger.info(
            "Creating SmartCP server",
            extra={
                "environment": settings.environment,
                "log_level": settings.server.log_level,
            },
        )

        # Create FastMCP server
        try:
            from fastmcp import FastMCP
        except ImportError as e:
            raise ImportError(
                "FastMCP is required. Install with: pip install fastmcp"
            ) from e

        mcp = FastMCP(
            name="smartcp",
            stateless=True,  # HTTP stateless mode
        )

        # Create infrastructure
        bifrost_client = None
        if settings.bifrost.url:
            bifrost_config = BifrostClientConfig(
                url=settings.bifrost.url,
                api_key=settings.bifrost.api_key or os.environ.get("BIFROST_API_KEY"),
                timeout_seconds=settings.bifrost.timeout_seconds,
            )
            bifrost_client = BifrostClient(bifrost_config)

        # StateAdapter delegates to Bifrost for all storage operations
        state = create_state_adapter(
            bifrost_client=bifrost_client, use_memory=bifrost_client is None
        )

        # Create services
        memory = create_memory_service(state_adapter=state)
        executor = create_executor_service(
            memory=memory,
            bifrost_client=bifrost_client,
        )

        # Create auth - use defaults if not configured
        token_validator = create_token_validator(
            secret_key=os.environ.get("JWT_SECRET", ""),
            algorithm="HS256",
            issuer=settings.auth.jwt_issuer or "",
            audience=settings.auth.jwt_audience or "",
        )

        return cls(
            settings=settings,
            mcp=mcp,
            bifrost_client=bifrost_client,
            state=state,
            memory=memory,
            executor=executor,
            token_validator=token_validator,
        )


# Module-level factory function for easy imports
def create_server(settings: Optional[SmartCPSettings] = None) -> SmartCPServer:
    """Create a SmartCP server instance.

    Args:
        settings: Optional settings

    Returns:
        Configured SmartCPServer
    """
    return SmartCPServer.create(settings)


# Vercel/ASGI entrypoint
def create_app() -> Any:
    """Create ASGI application for serverless deployment.

    Returns:
        FastAPI application
    """
    server = create_server()
    return server.create_fastapi_app()


# Development entrypoint
if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run server
    server = create_server()

    # Get port from environment or default
    port = int(os.environ.get("PORT", 8000))
    reload = "--reload" in sys.argv

    server.run(port=port, reload=reload)
