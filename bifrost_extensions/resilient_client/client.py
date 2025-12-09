"""Production-hardened Bifrost SDK client with full resilience."""

import asyncio
import httpx
import os
from typing import Any, Dict, List, Optional

from opentelemetry import trace

from bifrost_extensions.models import (
    RoutingStrategy,
    RoutingRequest,
    RoutingResponse,
    Message,
)
from bifrost_extensions.exceptions import AuthenticationError

# Resilience patterns
from bifrost_extensions.resilience.retry import (
    RetryPolicy,
    retry_with_backoff,
)
from bifrost_extensions.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
)
from bifrost_extensions.resilience.rate_limiter import (
    TokenBucketLimiter,
    RateLimitExceeded,
)

# Security
from bifrost_extensions.security.auth import (
    APIKeyValidator,
    generate_request_id,
)
from bifrost_extensions.security.validation import validate_output

# Observability
from bifrost_extensions.observability.logging import (
    get_logger,
    AuditLogger,
)
from bifrost_extensions.observability.metrics import get_metrics_collector

# Internal modules
from .http_executor import execute_routing
from .validation import validate_messages
from .health import perform_health_check

tracer = trace.get_tracer(__name__)


class ProductionGatewayClient:
    """
    Production-hardened Bifrost Gateway Client.

    Features:
    - Exponential backoff retry with jitter
    - Circuit breaker pattern
    - Token bucket rate limiting
    - Connection pooling (httpx)
    - API key validation
    - Input/output sanitization
    - Structured JSON logging
    - Prometheus metrics
    - OpenTelemetry tracing
    - Health checks

    Args:
        api_key: Bifrost API key
        base_url: Bifrost API URL
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        rate_limit: Requests per second
        circuit_breaker_threshold: Failures before opening circuit
        enable_metrics: Enable Prometheus metrics collection
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Example:
        >>> client = ProductionGatewayClient(
        >>>     rate_limit=100,
        >>>     circuit_breaker_threshold=5
        >>> )
        >>>
        >>> # Automatic retry, rate limiting, circuit breaking
        >>> response = await client.route(
        >>>     messages=[{"role": "user", "content": "Hello"}],
        >>>     strategy=RoutingStrategy.COST_OPTIMIZED
        >>> )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit: int = 100,
        rate_limit_period: float = 1.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0,
        enable_metrics: bool = True,
        log_level: str = "INFO",
        pool_size: int = 100,
    ):
        """Initialize production client."""
        # Configuration
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.enable_metrics = enable_metrics

        # Security: API key validation
        self.api_key = api_key or os.getenv("BIFROST_API_KEY")
        self._api_key_validator = APIKeyValidator(self.api_key)

        # Logging
        self.logger = get_logger("bifrost.client", level=log_level)
        self.audit_logger = AuditLogger(get_logger("bifrost.audit"))

        # Metrics initialization
        self._init_metrics(enable_metrics)

        # Resilience: Retry policy
        self._retry_policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=(
                httpx.RequestError,
                httpx.TimeoutException,
            ),
            timeout=timeout * (max_retries + 1),
        )

        # Resilience: Circuit breaker
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            success_threshold=2,
            timeout=circuit_breaker_timeout,
            expected_exception=Exception,
            name="bifrost_gateway",
        )

        # Resilience: Rate limiter
        self._rate_limiter = TokenBucketLimiter(
            rate=rate_limit,
            period=rate_limit_period,
            burst=rate_limit * 2,  # Allow 2x burst
        )

        # Connection pooling: httpx client with limits
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=pool_size,
                max_keepalive_connections=pool_size // 2,
            ),
            headers={
                "User-Agent": "BifrostSDK/1.0 (Production)",
                "Accept": "application/json",
            },
        )

    def _init_metrics(self, enable_metrics: bool) -> None:
        """Initialize metrics collectors."""
        if not enable_metrics:
            return

        self.metrics = get_metrics_collector()
        self._requests_total = self.metrics.counter(
            "bifrost_requests_total", "Total requests to Bifrost"
        )
        self._request_latency = self.metrics.histogram(
            "bifrost_request_latency_seconds", "Request latency"
        )
        self._circuit_state = self.metrics.gauge(
            "bifrost_circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=half_open, 2=open)"
        )
        self._rate_limit_hits = self.metrics.counter(
            "bifrost_rate_limit_hits_total", "Rate limit hits"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.close()

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self._http_client.aclose()
        self.logger.info("client.closed")

    @retry_with_backoff()
    async def route(
        self,
        messages: List[Message] | List[Dict[str, str]],
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        constraints: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> RoutingResponse:
        """Route request to optimal model with full resilience.

        Includes retry, circuit breaker, rate limiting, validation, and metrics.

        Raises:
            ValidationError, RoutingError, TimeoutError, AuthenticationError,
            CircuitBreakerError, RateLimitExceeded
        """
        request_id = generate_request_id()

        with tracer.start_as_current_span("route") as span:
            span.set_attribute("request.id", request_id)
            span.set_attribute("routing.strategy", strategy.value)

            # Security: Validate API key
            self._api_key_validator.validate(self.api_key)

            # Security: Validate and sanitize input
            messages = validate_messages(messages)

            # Rate limiting
            try:
                await self._rate_limiter.acquire()
            except RateLimitExceeded as e:
                if self.enable_metrics:
                    self._rate_limit_hits.inc()
                self.logger.warning(
                    "rate_limit.exceeded",
                    request_id=request_id,
                    retry_after=e.retry_after,
                )
                raise

            # Metrics: Track request
            if self.enable_metrics:
                self._requests_total.inc(
                    labels={
                        "strategy": strategy.value,
                        "method": "route",
                    }
                )

            # Build request
            request = RoutingRequest(
                messages=messages,
                strategy=strategy,
                constraints=constraints,
                context=context,
            )

            # Execute through circuit breaker
            try:
                async with self._circuit_breaker:
                    response = await execute_routing(
                        self._http_client,
                        self.base_url,
                        self.api_key,
                        request,
                        timeout or self.timeout,
                        request_id,
                    )

                # Security: Validate output
                response_dict = response.model_dump()
                validated = validate_output(response_dict, redact=False)
                response = RoutingResponse(**validated)

                # Logging
                self.logger.info(
                    "route.success",
                    request_id=request_id,
                    model=response.model.model_id,
                    confidence=response.confidence,
                )

                return response

            except CircuitBreakerError as e:
                # Update metrics
                if self.enable_metrics:
                    self._circuit_state.set(
                        2.0 if e.state.value == "open" else 1.0
                    )

                self.logger.error(
                    "circuit_breaker.open",
                    request_id=request_id,
                    state=e.state.value,
                )
                raise

            except Exception as e:
                self.logger.error(
                    "route.error",
                    request_id=request_id,
                    exc_info=e,
                )
                raise

    async def health_check(self) -> Dict[str, Any]:
        """Check client and service health with circuit breaker metrics."""
        return await perform_health_check(
            self.base_url,
            self._http_client,
            self._circuit_breaker,
        )

    async def get_metrics(self) -> str:
        """Export Prometheus-formatted metrics."""
        if not self.enable_metrics:
            return ""

        return self.metrics.export_prometheus()
