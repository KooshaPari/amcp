"""FastAPI application for Bifrost HTTP API."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Optional OpenTelemetry instrumentation
try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    FastAPIInstrumentor = None

from bifrost_api import routes
from bifrost_api.middleware import (
    auth_middleware,
    rate_limit_middleware,
    request_id_middleware,
)


tracer = trace.get_tracer(__name__) if OPENTELEMETRY_AVAILABLE else None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    print("Starting Bifrost API server...")
    yield
    # Shutdown
    print("Shutting down Bifrost API server...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Bifrost API",
        description="HTTP API for Bifrost Smart LLM Gateway",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(auth_middleware)
    app.middleware("http")(rate_limit_middleware)

    # Add OpenTelemetry instrumentation (if available)
    if OPENTELEMETRY_AVAILABLE and FastAPIInstrumentor:
        FastAPIInstrumentor.instrument_app(app)

    # Include routes
    app.include_router(routes.router, prefix="/v1", tags=["routing"])

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "1.0.0"}

    return app


# Create default app instance
app = create_app()
