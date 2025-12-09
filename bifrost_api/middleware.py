"""Middleware for Bifrost API - Auth, rate limiting, tracing."""

import time
import uuid
from typing import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from bifrost_extensions.exceptions import AuthenticationError, RateLimitError


# Simple in-memory rate limiter (replace with Redis in production)
_rate_limit_cache: dict[str, list[float]] = {}


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    """Add request ID to all requests."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def auth_middleware(request: Request, call_next: Callable) -> Response:
    """Validate API key authentication."""
    # Skip auth for health check
    if request.url.path == "/health":
        return await call_next(request)

    # Get API key from header
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    # Remove "Bearer " prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]

    # Validate API key (simplified - use proper validation in production)
    # For now, just check it exists and isn't empty
    if not api_key or len(api_key) < 10:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Store API key in request state for later use
    request.state.api_key = api_key

    return await call_next(request)


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """Rate limit requests per API key."""
    # Skip rate limiting for health check
    if request.url.path == "/health":
        return await call_next(request)

    api_key = getattr(request.state, "api_key", None)
    if not api_key:
        # Auth middleware should have caught this
        return await call_next(request)

    # Simple token bucket rate limiter
    # Rate: 100 requests per minute
    rate_limit = 100
    window_seconds = 60
    current_time = time.time()

    # Get or create rate limit entry
    if api_key not in _rate_limit_cache:
        _rate_limit_cache[api_key] = []

    # Clean old requests outside window
    _rate_limit_cache[api_key] = [
        timestamp
        for timestamp in _rate_limit_cache[api_key]
        if current_time - timestamp < window_seconds
    ]

    # Check rate limit
    if len(_rate_limit_cache[api_key]) >= rate_limit:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(window_seconds)},
        )

    # Record this request
    _rate_limit_cache[api_key].append(current_time)

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(rate_limit)
    response.headers["X-RateLimit-Remaining"] = str(
        rate_limit - len(_rate_limit_cache[api_key])
    )
    response.headers["X-RateLimit-Reset"] = str(int(current_time + window_seconds))

    return response
