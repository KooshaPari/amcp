"""Routing request handling for GatewayClient."""

import asyncio
from typing import Optional, Dict, Any, List

from opentelemetry import trace
from pydantic import ValidationError as PydanticValidationError

from bifrost_extensions.models import (
    RoutingStrategy,
    RoutingRequest,
    RoutingResponse,
    Message,
)
from bifrost_extensions.exceptions import (
    ValidationError,
    TimeoutError,
    RoutingError,
)
from bifrost_extensions.client.internal_router import (
    route_with_internal_router,
)

tracer = trace.get_tracer(__name__)


async def route(
    messages: List[Message] | List[Dict[str, str]],
    strategy: RoutingStrategy = RoutingStrategy.BALANCED,
    constraints: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
    http_client=None,
    internal_router=None,
    default_timeout: float = 30.0,
) -> RoutingResponse:
    """
    Route request to optimal model.

    Args:
        messages: Conversation messages
        strategy: Routing optimization strategy
        constraints: Optional constraints (max cost, latency, etc.)
        context: Additional context for routing
        timeout: Optional timeout override
        http_client: HTTP client for API calls
        internal_router: Internal router fallback
        default_timeout: Default timeout if not overridden

    Returns:
        RoutingResponse with selected model and metadata

    Raises:
        ValidationError: If request is invalid
        RoutingError: If routing fails
        TimeoutError: If operation times out
    """
    # Set up span attributes
    span = trace.get_current_span()
    span.set_attribute("routing.strategy", strategy.value)
    span.set_attribute("routing.message_count", len(messages))

    # Validate request
    try:
        # Convert dict messages to Message objects if needed
        if messages and isinstance(messages[0], dict):
            messages = [Message(**msg) for msg in messages]

        request = RoutingRequest(
            messages=messages,
            strategy=strategy,
            constraints=constraints,
            context=context,
        )
    except PydanticValidationError as e:
        raise ValidationError(
            f"Invalid routing request: {e}",
            details={"validation_errors": e.errors()},
        )

    # Execute with timeout
    timeout_val = timeout or default_timeout
    try:
        response = await asyncio.wait_for(
            _execute_routing(
                request, http_client, internal_router
            ),
            timeout=timeout_val,
        )

        span.set_attribute("routing.model", response.model.model_id)
        span.set_attribute("routing.confidence", response.confidence)

        return response

    except asyncio.TimeoutError:
        raise TimeoutError(
            f"Routing timed out after {timeout_val}s",
            timeout_ms=timeout_val * 1000,
        )


async def _execute_routing(
    request: RoutingRequest,
    http_client,
    internal_router,
) -> RoutingResponse:
    """
    Execute routing logic.

    Uses HTTP client if available, falls back to internal router.
    """
    # Use HTTP client
    if http_client:
        try:
            # Convert Message objects to dicts
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ]

            # Call HTTP API
            return await http_client.route(
                messages=messages,
                strategy=request.strategy.value,
                constraints=request.constraints,
                context=request.context,
            )

        except Exception as e:
            raise RoutingError(
                f"HTTP routing failed: {e}",
                details={"error": str(e)},
            )

    # Fallback to internal router
    if not internal_router:
        raise RoutingError(
            "Router not initialized",
            details={
                "reason": "Neither HTTP client nor RoutingService available"
            },
        )

    return await route_with_internal_router(internal_router, request)
