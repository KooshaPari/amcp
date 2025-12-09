"""HTTP/2 Enhanced FastAPI Application Wrapper

Wraps FastAPI app with HTTP/2 support, streaming optimizations,
and protocol negotiation.
"""

import logging
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .http2_config import HTTP2Config, HTTP2Middleware, create_http2_middleware
from .streaming import get_streaming_pipeline
from .fastapi_integration import create_streaming_router

logger = logging.getLogger(__name__)


class HTTP2App:
    """Wrapper for FastAPI application with HTTP/2 support."""

    def __init__(
        self,
        app: FastAPI,
        http2_config: Optional[HTTP2Config] = None,
        enable_streaming: bool = True,
    ):
        """Initialize HTTP/2 enhanced FastAPI app.

        Args:
            app: FastAPI application instance
            http2_config: HTTP/2 configuration (uses environment if not provided)
            enable_streaming: Whether to enable streaming routes
        """
        self.app = app
        self.http2_config = http2_config or HTTP2Config.from_env()
        self.enable_streaming = enable_streaming

        # Validate config
        try:
            self.http2_config.validate()
        except Exception as e:
            logger.warning(f"HTTP/2 config validation issue: {e}")

    def setup(self) -> FastAPI:
        """Setup HTTP/2 support and return configured app.

        Returns:
            Configured FastAPI application
        """
        logger.info(
            f"Setting up HTTP/2 app (HTTP/2: {self.http2_config.enable_http2}, "
            f"SSL: {self.http2_config.ssl_enabled})"
        )

        # 1. Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 2. Add compression middleware (efficient for HTTP/2)
        self.app.add_middleware(
            GZipMiddleware,
            minimum_size=1000,
        )

        # 3. Add HTTP/2 middleware
        self.app.add_middleware(
            HTTP2Middleware,
            config=self.http2_config,
        )

        # 4. Add streaming routes if enabled
        if self.enable_streaming:
            self._setup_streaming_routes()

        # 5. Add health check endpoint
        self._add_health_endpoint()

        # 6. Add protocol info endpoint
        self._add_protocol_info_endpoint()

        logger.info("HTTP/2 app setup complete")
        return self.app

    def _setup_streaming_routes(self) -> None:
        """Setup streaming routes for SSE support."""
        try:
            streaming_router = create_streaming_router()
            self.app.include_router(streaming_router)
            logger.info("Streaming routes registered")
        except Exception as e:
            logger.error(f"Failed to setup streaming routes: {e}")

    def _add_health_endpoint(self) -> None:
        """Add HTTP/2 health check endpoint."""
        @self.app.get("/health/http2")
        async def http2_health():
            """HTTP/2 specific health check."""
            pipeline = get_streaming_pipeline()
            return {
                "status": "healthy",
                "http2_enabled": self.http2_config.enable_http2,
                "http1_enabled": self.http2_config.enable_http1,
                "ssl_enabled": self.http2_config.ssl_enabled,
                "streaming_active_streams": pipeline.get_stream_count(),
                "max_concurrent_streams": self.http2_config.h2_max_concurrent_streams,
            }

    def _add_protocol_info_endpoint(self) -> None:
        """Add protocol information endpoint."""
        @self.app.get("/info/protocol")
        async def protocol_info():
            """Get server protocol information."""
            return {
                "server": "SmartCP",
                "version": "2.0",
                "http2": {
                    "enabled": self.http2_config.enable_http2,
                    "max_concurrent_streams": self.http2_config.h2_max_concurrent_streams,
                    "max_header_list_size": self.http2_config.h2_max_header_list_size,
                    "flow_control_window": self.http2_config.h2_flow_control_window,
                },
                "http1": {
                    "enabled": self.http2_config.enable_http1,
                },
                "ssl": {
                    "enabled": self.http2_config.ssl_enabled,
                    "version": self.http2_config.ssl_version if self.http2_config.ssl_enabled else None,
                },
                "streaming": {
                    "enabled": self.enable_streaming,
                },
            }

    def get_startup_info(self) -> dict:
        """Get server startup information and command."""
        from .http2_config import get_server_startup_command

        return {
            "host": self.http2_config.host,
            "port": self.http2_config.port,
            "server_type": self.http2_config.server_type,
            "http2_enabled": self.http2_config.enable_http2,
            "ssl_enabled": self.http2_config.ssl_enabled,
            "startup_command": get_server_startup_command(self.http2_config),
        }


def setup_http2_app(
    app: FastAPI,
    http2_config: Optional[HTTP2Config] = None,
    enable_streaming: bool = True,
) -> FastAPI:
    """Setup FastAPI app with HTTP/2 support.

    Usage:
        from fastapi import FastAPI
        from optimization import setup_http2_app

        app = FastAPI()
        app = setup_http2_app(app)
    """
    http2_app = HTTP2App(app, http2_config, enable_streaming)
    return http2_app.setup()
