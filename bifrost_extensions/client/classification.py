"""Classification handler for GatewayClient."""

import asyncio
from typing import Optional, List

from opentelemetry import trace

from bifrost_extensions.models import (
    ClassificationRequest,
    ClassificationResult,
)
from bifrost_extensions.exceptions import (
    ValidationError,
    TimeoutError,
    RoutingError,
)
from bifrost_extensions.client.internal_router import (
    classify_with_internal_router,
)

tracer = trace.get_tracer(__name__)


async def classify(
    prompt: str,
    categories: Optional[List[str]] = None,
    timeout: Optional[float] = None,
    http_client=None,
    default_timeout: float = 30.0,
) -> ClassificationResult:
    """
    Classify prompt.

    Args:
        prompt: Prompt to classify
        categories: Optional target categories (or auto-detect)
        timeout: Optional timeout override
        http_client: HTTP client for API calls
        default_timeout: Default timeout if not overridden

    Returns:
        ClassificationResult with category and confidence

    Raises:
        ValidationError: If request is invalid
        RoutingError: If classification fails
        TimeoutError: If operation times out
    """
    if not prompt:
        raise ValidationError("Prompt cannot be empty")

    request = ClassificationRequest(prompt=prompt, categories=categories)

    timeout_val = timeout or default_timeout
    try:
        result = await asyncio.wait_for(
            _execute_classification(request, http_client),
            timeout=timeout_val,
        )
        return result
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"Classification timed out after {timeout_val}s",
            timeout_ms=timeout_val * 1000,
        )


async def _execute_classification(
    request: ClassificationRequest,
    http_client,
) -> ClassificationResult:
    """
    Execute classification logic.

    Uses HTTP client if available, falls back to internal router.
    """
    # Try HTTP client first
    if http_client:
        try:
            return await http_client.classify(
                prompt=request.prompt,
                categories=request.categories,
            )
        except Exception:
            # Fall through to internal router fallback
            pass

    # Fallback to internal router
    return await classify_with_internal_router(request)
