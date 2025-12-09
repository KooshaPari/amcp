"""HTTP/2 Configuration and Server Setup

Provides HTTP/2 support for FastAPI with SSL/TLS, protocol negotiation,
and performance optimizations for streaming.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HTTP2Config:
    """HTTP/2 server configuration."""

    # Protocol settings
    enable_http2: bool = True
    enable_http1: bool = True  # Also enable HTTP/1.1 for compatibility
    
    # SSL/TLS settings
    ssl_enabled: bool = False
    ssl_keyfile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    ssl_version: str = "TLSv1_2"  # TLS 1.2+
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 443 if ssl_enabled else 8000
    workers: int = 1  # For HTTP/2 multiplexing, single worker often sufficient
    
    # Performance tuning
    backlog: int = 2048
    limit_concurrency: int = 500
    limit_max_requests: int = 10000
    timeout_keep_alive: int = 60
    timeout_notify: int = 30
    timeout_graceful_shutdown: int = 15
    
    # HTTP/2 specific
    h2_max_concurrent_streams: int = 100
    h2_max_header_list_size: int = 16384  # 16KB
    h2_flow_control_window: int = 65536  # 64KB
    
    # Logging
    log_level: str = "info"
    access_log: bool = True
    
    # Server type (uvicorn or hypercorn)
    server_type: str = "hypercorn"  # Hypercorn has better HTTP/2 support

    def validate(self) -> None:
        """Validate configuration."""
        if self.ssl_enabled:
            if not self.ssl_keyfile or not self.ssl_certfile:
                raise ValueError(
                    "SSL enabled but keyfile or certfile not provided"
                )
            if not Path(self.ssl_keyfile).exists():
                raise FileNotFoundError(f"SSL key file not found: {self.ssl_keyfile}")
            if not Path(self.ssl_certfile).exists():
                raise FileNotFoundError(f"SSL cert file not found: {self.ssl_certfile}")

    @classmethod
    def from_env(cls) -> "HTTP2Config":
        """Load configuration from environment variables."""
        return cls(
            enable_http2=os.getenv("HTTP2_ENABLED", "true").lower() == "true",
            enable_http1=os.getenv("HTTP1_ENABLED", "true").lower() == "true",
            ssl_enabled=os.getenv("SSL_ENABLED", "false").lower() == "true",
            ssl_keyfile=os.getenv("SSL_KEYFILE"),
            ssl_certfile=os.getenv("SSL_CERTFILE"),
            ssl_ca_certs=os.getenv("SSL_CA_CERTS"),
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "443" if os.getenv("SSL_ENABLED") == "true" else "8000")),
            workers=int(os.getenv("WORKERS", "1")),
            h2_max_concurrent_streams=int(os.getenv("HTTP2_MAX_STREAMS", "100")),
            log_level=os.getenv("LOG_LEVEL", "info"),
            server_type=os.getenv("SERVER_TYPE", "hypercorn"),
        )


class HTTP2ServerFactory:
    """Factory for creating HTTP/2 configured servers."""

    @staticmethod
    def create_uvicorn_config(config: HTTP2Config) -> dict:
        """Create uvicorn configuration dictionary.
        
        Note: uvicorn has limited HTTP/2 support. Hypercorn is recommended.
        """
        uvicorn_config = {
            "host": config.host,
            "port": config.port,
            "log_level": config.log_level,
            "access_log": config.access_log,
            "timeout_keep_alive": config.timeout_keep_alive,
            "timeout_notify": config.timeout_notify,
            "graceful_shutdown_timeout": config.timeout_graceful_shutdown,
            "limit_concurrency": config.limit_concurrency,
            "limit_max_requests": config.limit_max_requests,
        }

        # Add SSL if configured
        if config.ssl_enabled:
            uvicorn_config.update({
                "ssl_keyfile": config.ssl_keyfile,
                "ssl_certfile": config.ssl_certfile,
                "ssl_ca_certs": config.ssl_ca_certs,
            })

        # HTTP/2 support (experimental in uvicorn)
        if config.enable_http2:
            logger.warning(
                "HTTP/2 support in uvicorn is limited. "
                "Consider using hypercorn for full HTTP/2 support."
            )

        return uvicorn_config

    @staticmethod
    def create_hypercorn_config(config: HTTP2Config) -> dict:
        """Create hypercorn configuration dictionary.
        
        Hypercorn provides better HTTP/2 support with proper multiplexing.
        """
        hypercorn_config = {
            "bind": [f"{config.host}:{config.port}"],
            "workers": config.workers,
            "backlog": config.backlog,
            "timeout_keep_alive": config.timeout_keep_alive,
            "timeout_notify": config.timeout_notify,
            "graceful_shutdown_timeout": config.timeout_graceful_shutdown,
            "limit_concurrency": config.limit_concurrency,
            "limit_max_requests": config.limit_max_requests,
            "access_log_format": '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
        }

        # Add SSL if configured
        if config.ssl_enabled:
            hypercorn_config.update({
                "certfile": config.ssl_certfile,
                "keyfile": config.ssl_keyfile,
                "ca_certs": config.ssl_ca_certs,
                "ssl_version": config.ssl_version,
            })

        # HTTP/2 protocol
        if config.enable_http2 and config.enable_http1:
            hypercorn_config["alpn_protocols"] = ["h2", "http/1.1"]
        elif config.enable_http2:
            hypercorn_config["alpn_protocols"] = ["h2"]
        else:
            hypercorn_config["alpn_protocols"] = ["http/1.1"]

        # HTTP/2 specific settings
        if config.enable_http2:
            hypercorn_config.update({
                "h2_max_concurrent_streams": config.h2_max_concurrent_streams,
                "h2_max_header_list_size": config.h2_max_header_list_size,
                "h2_flow_control_window": config.h2_flow_control_window,
            })

        return hypercorn_config

    @staticmethod
    def get_command_line_args(config: HTTP2Config) -> List[str]:
        """Get command-line arguments for server startup.
        
        Usage:
            args = factory.get_command_line_args(config)
            subprocess.run(["hypercorn", "app:app"] + args)
        """
        args = [
            f"--bind={config.host}:{config.port}",
            f"--workers={config.workers}",
            f"--timeout-keep-alive={config.timeout_keep_alive}",
            f"--limit-concurrency={config.limit_concurrency}",
        ]

        if config.ssl_enabled:
            args.extend([
                f"--certfile={config.ssl_certfile}",
                f"--keyfile={config.ssl_keyfile}",
            ])

        if config.enable_http2 and config.enable_http1:
            args.append("--alpn-protocols=h2,http/1.1")
        elif config.enable_http2:
            args.append("--alpn-protocols=h2")

        return args


class HTTP2Middleware:
    """ASGI middleware for HTTP/2 specific optimizations."""

    def __init__(self, app, config: HTTP2Config):
        self.app = app
        self.config = config

    async def __call__(self, scope, receive, send):
        """ASGI middleware entrypoint."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Log HTTP version
        http_version = scope.get("http_version", "1.0")
        logger.debug(f"Request received via HTTP/{http_version}")

        # HTTP/2 specific headers
        if http_version.startswith("2"):
            # Add HTTP/2 performance optimizations
            async def send_with_optimization(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))

                    # Add server header
                    headers.append((b"server", b"SmartCP/2.0"))

                    # Enable compression (gzip) for HTTP/2
                    headers.append((b"vary", b"Accept-Encoding"))

                    message["headers"] = headers

                await send(message)

            await self.app(scope, receive, send_with_optimization)
        else:
            await self.app(scope, receive, send)


def get_server_startup_command(config: HTTP2Config) -> str:
    """Get the command to start the server with HTTP/2.
    
    Examples:
        For hypercorn:
            hypercorn app:app --bind 0.0.0.0:443 --certfile cert.pem --keyfile key.pem
        
        For uvicorn (limited HTTP/2):
            uvicorn app:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
    """
    if config.server_type == "hypercorn":
        args = " ".join(HTTP2ServerFactory.get_command_line_args(config))
        return f"hypercorn app:app {args}"
    else:
        args = ["uvicorn", "app:app"]
        if config.ssl_enabled:
            args.extend([
                f"--ssl-keyfile={config.ssl_keyfile}",
                f"--ssl-certfile={config.ssl_certfile}",
            ])
        args.extend([
            f"--host={config.host}",
            f"--port={config.port}",
        ])
        return " ".join(args)


# Convenience function for FastAPI integration
def create_http2_middleware(app, config: Optional[HTTP2Config] = None) -> HTTP2Middleware:
    """Create HTTP/2 middleware for FastAPI application.
    
    Usage:
        app = FastAPI()
        config = HTTP2Config.from_env()
        http2_middleware = create_http2_middleware(app, config)
        app.add_middleware(HTTP2Middleware, config=config)
    """
    if config is None:
        config = HTTP2Config.from_env()

    return HTTP2Middleware(app, config)


if __name__ == "__main__":
    # Example: Print server startup command
    config = HTTP2Config.from_env()
    config.validate()

    print("=" * 80)
    print("HTTP/2 Configuration")
    print("=" * 80)
    print(f"Server Type: {config.server_type}")
    print(f"Host: {config.host}")
    print(f"Port: {config.port}")
    print(f"HTTP/2 Enabled: {config.enable_http2}")
    print(f"HTTP/1.1 Enabled: {config.enable_http1}")
    print(f"SSL Enabled: {config.ssl_enabled}")
    print(f"Max Concurrent Streams: {config.h2_max_concurrent_streams}")
    print()
    print("Startup Command:")
    print(get_server_startup_command(config))
    print()
