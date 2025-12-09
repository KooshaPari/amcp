# Production SDK Quick Reference

## Basic Usage

```python
from bifrost_extensions.resilient_client import ProductionGatewayClient
from bifrost_extensions.models import RoutingStrategy

async with ProductionGatewayClient() as client:
    response = await client.route(
        messages=[{"role": "user", "content": "Hello"}],
        strategy=RoutingStrategy.COST_OPTIMIZED,
    )
```

## Configuration

```python
client = ProductionGatewayClient(
    # Security
    api_key="your-key",  # Or BIFROST_API_KEY env var

    # Performance
    timeout=30.0,
    pool_size=100,

    # Resilience
    max_retries=3,
    rate_limit=100,  # req/sec
    circuit_breaker_threshold=5,
    circuit_breaker_timeout=60.0,

    # Observability
    enable_metrics=True,
    log_level="INFO",
)
```

## Error Handling

```python
from bifrost_extensions.resilience.circuit_breaker import CircuitBreakerError
from bifrost_extensions.resilience.rate_limiter import RateLimitExceeded

try:
    response = await client.route(messages)
except CircuitBreakerError:
    # Circuit open, use fallback
    response = fallback_response()
except RateLimitExceeded as e:
    # Wait and retry
    await asyncio.sleep(e.retry_after)
    response = await client.route(messages)
except Exception as e:
    # Log and alert
    logger.error("routing.failed", exc_info=e)
```

## Health Check

```python
health = await client.health_check()
# {
#   "status": "healthy" | "degraded" | "unhealthy",
#   "circuit_breaker": {"state": "closed", ...},
#   "backend": {"status": "up", "latency_ms": 12.5}
# }
```

## Metrics Export

```python
# Expose via /metrics endpoint
from fastapi import FastAPI

app = FastAPI()

@app.get("/metrics")
async def metrics():
    return await client.get_metrics()
```

## Key Metrics

```promql
# Request rate
rate(bifrost_requests_total[5m])

# Error rate
rate(bifrost_errors_total[5m]) / rate(bifrost_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(bifrost_request_latency_seconds_bucket[5m]))

# Circuit state (0=closed, 1=half_open, 2=open)
bifrost_circuit_breaker_state
```

## Logging

```python
from bifrost_extensions.observability.logging import get_logger

logger = get_logger("my_app")

# Structured logging
logger.info("operation.started", user_id="123", action="fetch")

# With operation context
with logger.operation("fetch_data", user_id="123"):
    data = await fetch_data()
    # Automatically logs start/complete/duration
```

## Security Features

```python
from bifrost_extensions.security.validation import (
    InputValidator,
    OutputValidator,
)

# Input validation
clean_text = InputValidator.sanitize_string(user_input)
email = InputValidator.validate_email(email_input)
url = InputValidator.validate_url(url_input)

# Output redaction
safe_output = OutputValidator.redact_sensitive(data)
# Redacts: api_key, secret, password, token, etc.
```

## Retry Configuration

```python
from bifrost_extensions.resilience.retry import (
    RetryPolicy,
    retry_with_backoff,
)

policy = RetryPolicy(
    max_retries=3,
    initial_delay=1.0,
    max_delay=60.0,
    jitter=True,
)

@retry_with_backoff(policy)
async def flaky_operation():
    return await external_api_call()
```

## Circuit Breaker

```python
from bifrost_extensions.resilience.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    success_threshold=2,
    timeout=60.0,
)

async with breaker:
    result = await risky_operation()
```

## Rate Limiting

```python
from bifrost_extensions.resilience.rate_limiter import TokenBucketLimiter

limiter = TokenBucketLimiter(
    rate=100,  # requests
    period=1.0,  # per second
    burst=200,  # burst capacity
)

await limiter.acquire()  # Wait if needed
if await limiter.try_acquire():  # Non-blocking
    # Proceed
    pass
```

## Best Practices

### 1. Always use context manager
```python
async with ProductionGatewayClient() as client:
    # Use client
    pass
# Automatically closed
```

### 2. Configure appropriate timeouts
```python
# Total timeout = timeout * (max_retries + 1)
client = ProductionGatewayClient(
    timeout=30.0,
    max_retries=3,  # Max 120s total
)
```

### 3. Monitor circuit breaker
```yaml
- alert: CircuitBreakerOpen
  expr: bifrost_circuit_breaker_state == 2
  for: 1m
```

### 4. Use structured logging
```python
logger.info("route.success",
    request_id=request_id,
    model=model_id,
    confidence=confidence
)
```

### 5. Export metrics
```python
@app.get("/metrics")
async def prometheus_metrics():
    return client.get_metrics()
```

## Common Patterns

### Batch Processing
```python
results = await asyncio.gather(
    *[client.route(msg) for msg in messages],
    return_exceptions=True,
)

successful = [r for r in results if not isinstance(r, Exception)]
failed = [r for r in results if isinstance(r, Exception)]
```

### Fallback Strategy
```python
try:
    response = await client.route(messages)
except Exception:
    response = await fallback_client.route(messages)
```

### Caching
```python
cache_key = hash(str(messages))
if cache_key in cache:
    return cache[cache_key]

response = await client.route(messages)
cache[cache_key] = response
return response
```

## Troubleshooting

### Circuit breaker keeps opening
- Check backend health
- Increase `failure_threshold`
- Review error logs
- Check network stability

### High retry count
- Investigate transient errors
- Increase `timeout`
- Check backend capacity
- Review retry policy

### Rate limiting too aggressive
- Increase `rate_limit`
- Increase `burst` capacity
- Check if traffic is bursty

### High latency
- Check backend performance
- Review connection pool size
- Check network latency
- Consider caching

## Environment Variables

```bash
# Required
export BIFROST_API_KEY="your-api-key"

# Optional
export LOG_LEVEL="INFO"
export BIFROST_URL="http://localhost:8000"
export POOL_SIZE="100"
export RATE_LIMIT="100"
```

## Testing

```bash
# Run all tests
pytest tests/sdk/bifrost/ -v

# With coverage
pytest tests/sdk/bifrost/ --cov=bifrost_extensions --cov-report=html

# Run example
python bifrost_extensions/examples/production_example.py
```

## Support

- **Docs**: `README_PRODUCTION.md`
- **Examples**: `examples/production_example.py`
- **Tests**: `tests/sdk/bifrost/`
- **Summary**: `docs/sdk/PRODUCTION_HARDENING_SUMMARY.md`
