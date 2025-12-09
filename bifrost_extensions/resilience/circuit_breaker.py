"""Circuit breaker pattern for fault tolerance using pybreaker."""

from enum import Enum
from typing import Any, Callable, Optional

import pybreaker
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit is open."""

    def __init__(self, state: CircuitState, message: str):
        self.state = state
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit breaker wrapper around pybreaker.CircuitBreaker.

    Implements the Circuit Breaker pattern:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing if service recovered

    Example:
        >>> breaker = CircuitBreaker(
        >>>     failure_threshold=5,
        >>>     timeout=60.0
        >>> )
        >>>
        >>> async def risky_operation():
        >>>     async with breaker:
        >>>         return await external_api_call()
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
        name: str = "circuit_breaker",
    ):
        """Initialize circuit breaker with pybreaker backend."""
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        # Create pybreaker CircuitBreaker instance
        # Note: pybreaker's success_threshold is for half-open state recovery
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=failure_threshold,
            reset_timeout=timeout,
            success_threshold=success_threshold,
            exclude=None,  # Don't exclude any exceptions, we handle them in call()
            listeners=None,
            name=name,
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        state_class_name = self._breaker.state.__class__.__name__
        if "Open" in state_class_name:
            return CircuitState.OPEN
        elif "HalfOpen" in state_class_name:
            return CircuitState.HALF_OPEN
        else:
            return CircuitState.CLOSED

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._breaker.fail_counter

    @property
    def success_count(self) -> int:
        """Get current success count in half-open state."""
        return self._breaker.success_counter

    async def call(self, func: Callable[[], Any]) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Async callable to execute

        Returns:
            Result of function call

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Original exception if function fails
        """
        with tracer.start_as_current_span(
            f"circuit_breaker.{self.name}"
        ) as span:
            span.set_attribute("circuit_breaker.state", self.state.value)
            span.set_attribute("circuit_breaker.failure_count", self.failure_count)

            try:
                # Use pybreaker's call_async for async functions
                # pybreaker handles all state transitions internally
                result = await self._breaker.call_async(func)
                span.set_attribute("circuit_breaker.success", True)
                return result

            except pybreaker.CircuitBreakerError as e:
                # Circuit is open - convert to our CircuitBreakerError
                span.set_attribute("circuit_breaker.rejected", True)
                span.record_exception(e)
                raise CircuitBreakerError(
                    self.state,
                    f"Circuit breaker '{self.name}' is {self.state.value}",
                ) from e

            except self.expected_exception as e:
                # Expected failure - pybreaker will track it
                span.set_attribute("circuit_breaker.failure", True)
                span.record_exception(e)
                raise

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            # Success - nothing to do, pybreaker already tracked it
            return False

        if exc_type is CircuitBreakerError:
            # Don't re-raise, our custom error
            return False

        if isinstance(exc_val, self.expected_exception):
            # Expected exception - pybreaker will track via call_async
            # But when using context manager directly, we need to record failure
            # This is for manual circuit breaker usage without call()
            try:
                # Manually increment failure count
                state_class_name = self._breaker.state.__class__.__name__
                if "Open" not in state_class_name:
                    # Only increment if not already open
                    self._breaker.fail_counter += 1
                    if self._breaker.fail_counter >= self._breaker.fail_max:
                        self._breaker.state = self._breaker.open()
            except Exception:
                pass

        return False

    async def reset(self) -> None:
        """Manually reset circuit to closed state."""
        self._breaker.close()

    def get_metrics(self) -> dict[str, Any]:
        """
        Get circuit breaker metrics.

        Returns:
            Dictionary with current metrics
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "timeout": self.timeout,
            "last_failure_time": None,  # Not available in pybreaker
        }
