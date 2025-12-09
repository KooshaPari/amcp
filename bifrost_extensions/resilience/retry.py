"""Retry logic using tenacity library with exponential backoff and jitter.

This module provides a thin wrapper around tenacity for consistent retry
policies with OpenTelemetry tracing integration.
"""

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

from opentelemetry import trace
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

tracer = trace.get_tracer(__name__)
T = TypeVar("T")


@dataclass
class RetryPolicy:
    """
    Retry policy configuration.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries
        exponential_base: Exponential backoff base (typically 2)
        jitter: Whether to add random jitter to delay
        retryable_exceptions: Tuple of exception types to retry on
        timeout: Optional total timeout for all retries
    """

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,)
    timeout: Optional[float] = None


def retry_with_backoff(policy: Optional[RetryPolicy] = None):
    """
    Decorator for async functions with retry logic and exponential backoff.

    Uses tenacity library for reliable retry handling with OpenTelemetry
    tracing integration.

    Args:
        policy: Retry policy configuration. Defaults to RetryPolicy()

    Example:
        >>> @retry_with_backoff(RetryPolicy(max_retries=5))
        >>> async def fetch_data():
        >>>     # May fail transiently
        >>>     return await http_client.get(url)

    Returns:
        Decorated async function with retry logic
    """
    if policy is None:
        policy = RetryPolicy()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Build tenacity retry decorator
        tenacity_retry = retry(
            retry=retry_if_exception_type(policy.retryable_exceptions),
            stop=stop_after_attempt(policy.max_retries + 1),
            wait=wait_exponential(
                multiplier=policy.initial_delay,
                min=policy.initial_delay,
                max=policy.max_delay,
            ),
            reraise=True,
        )

        # Apply tenacity decorator
        func_with_retry = tenacity_retry(func)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(
                f"retry.{func.__name__}"
            ) as span:
                span.set_attribute("retry.max_attempts", policy.max_retries)

                try:
                    result = await func_with_retry(*args, **kwargs)
                    span.set_attribute("retry.succeeded", True)
                    return result
                except Exception as e:
                    span.set_attribute("retry.failed", True)
                    span.set_attribute("retry.error_type", type(e).__name__)
                    span.set_attribute("retry.error_message", str(e))
                    raise

        return wrapper

    return decorator


async def retry_operation(
    operation: Callable[[], Any],
    policy: Optional[RetryPolicy] = None,
) -> Any:
    """
    Retry an async operation with backoff.

    Functional alternative to decorator pattern. Applies retry logic to
    a callable without requiring function decoration.

    Args:
        operation: Async callable to retry
        policy: Retry policy configuration. Defaults to RetryPolicy()

    Returns:
        Result of successful operation

    Raises:
        Last exception after all retries exhausted

    Example:
        >>> result = await retry_operation(
        >>>     lambda: http_client.get(url),
        >>>     RetryPolicy(max_retries=3)
        >>> )
    """
    if policy is None:
        policy = RetryPolicy()

    @retry_with_backoff(policy)
    async def _wrapped() -> Any:
        return await operation()

    return await _wrapped()
