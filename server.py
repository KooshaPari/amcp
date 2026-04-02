"""SmartCP MCP Server.

Thin delegation server that exposes Bifrost via MCP protocol.
"""

import logging
import os
from typing import Any, Optional

from smartcp.runtime import AgentRuntime

from auth.middleware import create_auth_middleware
from auth.token import TokenValidator, create_token_validator
from bifrost_client import BifrostClient, BifrostClientConfig
from config.settings import SmartCPSettings, get_settings
from middleware.resource_access_enforcement import (
    ResourceAccessEnforcementMiddleware,
)
from tools.execute import register_execute_tool, set_runtime

logger = logging.getLogger(__name__)


class SmartCPServer:
    """SmartCP MCP Server - thin delegation to Bifrost.

    Provides HTTP stateless MCP server with bearer token authentication
    and delegation to Bifrost backend.

    Usage:
        server = SmartCPServer.create()
        app = server.create_fastapi_app()
        server.run()
    """

    def __init__(
        self,
        settings: SmartCPSettings,
        mcp: Any,
        runtime: AgentRuntime,
        bifrost_client: Optional[BifrostClient],
        token_validator: TokenValidator,
    ):
        """Initialize server with dependencies.

        Args:
            settings: Application settings
            mcp: FastMCP server instance
            runtime: AgentRuntime for code execution
            bifrost_client: Client for Bifrost backend delegation
            token_validator: JWT token validator
        """
        self.settings = settings
        self.mcp = mcp
        self.runtime = runtime
        self.bifrost_client = bifrost_client
        self.token_validator = token_validator

        # Wire runtime to tools module
        set_runtime(runtime)

        logger.info("SmartCP MCP Server initialized with AgentRuntime")

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
            description="MCP server with agent runtime and user-scoped state management",
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
                "status": "ready" if backend_status != "disconnected" else "degraded",
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

        # Create AgentRuntime
        runtime = AgentRuntime()

        # Register MCP tools (this will call set_runtime internally)
        try:
            register_execute_tool(mcp)
        except ImportError as e:
            logger.warning(
                "Failed to register execute tool",
                extra={"error": str(e)},
            )

        # Create Bifrost client for backend delegation
        bifrost_client = None
        if settings.bifrost.url:
            bifrost_config = BifrostClientConfig(
                url=settings.bifrost.url,
                api_key=settings.bifrost.api_key or os.environ.get("BIFROST_API_KEY"),
                timeout_seconds=settings.bifrost.timeout_seconds,
            )
            bifrost_client = BifrostClient(bifrost_config)

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
            runtime=runtime,
            bifrost_client=bifrost_client,
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
