# Bifrost HTTP API

HTTP API layer for Bifrost SDK to replace direct router_core imports.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ HTTP (Week 2+)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GatewayClient (SDK)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  BifrostHTTPClient                                       │  │
│  │  - Retry logic (exponential backoff)                    │  │
│  │  - Timeout handling                                     │  │
│  │  - Connection pooling                                   │  │
│  │  - Error mapping (HTTP → SDK exceptions)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ POST /v1/route
                           │ POST /v1/route-tool
                           │ POST /v1/classify
                           │ GET  /v1/usage
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Bifrost API (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Middleware Stack                                        │  │
│  │  1. Request ID (trace correlation)                       │  │
│  │  2. Auth (API key validation)                            │  │
│  │  3. Rate Limiting (token bucket)                         │  │
│  │  4. OpenTelemetry (distributed tracing)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Routes                                              │  │
│  │  - /v1/route → model selection                           │  │
│  │  - /v1/route-tool → tool selection                       │  │
│  │  - /v1/classify → prompt classification                  │  │
│  │  - /v1/usage → usage statistics                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Internal
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  router_core.RoutingService                     │
│  - Classification                                               │
│  - Model selection                                              │
│  - Cost estimation                                              │
│  - Performance tracking                                         │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
bifrost_api/
├── __init__.py          # Package exports
├── app.py               # FastAPI application
├── routes.py            # API endpoints
├── middleware.py        # Auth, rate limiting, tracing
└── dependencies.py      # Dependency injection

bifrost_extensions/
├── client.py            # GatewayClient (updated)
└── http_client.py       # HTTP client wrapper (NEW)
```

## API Endpoints

### POST /v1/route
Route request to optimal model.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Write Python code"}
  ],
  "strategy": "balanced",
  "constraints": {"max_latency_ms": 500},
  "context": {}
}
```

**Response:**
```json
{
  "model": {
    "model_id": "gpt-4",
    "provider": "openai",
    "estimated_cost_usd": 0.03,
    "estimated_latency_ms": 200
  },
  "confidence": 0.95,
  "reasoning": "Selected for code generation capability",
  "request_id": "req_abc123"
}
```

### POST /v1/route-tool
Route action to optimal tool.

**Request:**
```json
{
  "action": "search for Python documentation",
  "available_tools": ["web_search", "doc_search"],
  "context": {}
}
```

**Response:**
```json
{
  "recommended_tool": "doc_search",
  "confidence": 0.85,
  "reasoning": "Matched 'documentation' keyword",
  "request_id": "req_def456"
}
```

### POST /v1/classify
Classify prompt.

**Request:**
```json
{
  "prompt": "Write a Python function to parse JSON",
  "categories": ["simple", "moderate", "complex"]
}
```

**Response:**
```json
{
  "category": "simple",
  "confidence": 0.9,
  "complexity": "low",
  "request_id": "req_ghi789"
}
```

### GET /v1/usage
Get usage statistics.

**Query Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `group_by`: Grouping dimension (model, provider, user)

**Response:**
```json
{
  "total_requests": 1000,
  "total_cost_usd": 15.50,
  "avg_latency_ms": 250.0,
  "requests_by_model": {
    "gpt-4": 500,
    "claude-3": 300,
    "gemini-pro": 200
  },
  "cost_by_model": {
    "gpt-4": 12.00,
    "claude-3": 2.50,
    "gemini-pro": 1.00
  }
}
```

## Authentication

All endpoints require API key authentication via header:

```
X-API-Key: your_api_key_here
```

Or:

```
Authorization: Bearer your_api_key_here
```

## Rate Limiting

- **Limit:** 100 requests per minute per API key
- **Window:** 60 seconds (rolling)
- **Response headers:**
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Unix timestamp when window resets

When rate limit exceeded:
```json
{
  "detail": "Rate limit exceeded"
}
```
Response code: 429 Too Many Requests
Retry-After header: Seconds to wait

## Error Handling

### Error Response Format
```json
{
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "request_id": "req_xyz",
  "details": {}
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing API key |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Server error |

## Running the API Server

### Development

```bash
# Install dependencies
pip install fastapi uvicorn httpx opentelemetry-instrumentation-fastapi

# Run server
uvicorn bifrost_api.app:app --reload --port 8000

# Or use the app instance directly
python -m bifrost_api.app
```

### Production

```bash
# Use gunicorn with uvicorn workers
gunicorn bifrost_api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile -
```

## Using the HTTP Client

### Basic Usage

```python
from bifrost_extensions import GatewayClient

# Create client with HTTP enabled (default in Week 2+)
client = GatewayClient(
    api_key="your_api_key",
    base_url="http://localhost:8000",
    use_http=True  # Default: True
)

# Route request
response = await client.route(
    messages=[{"role": "user", "content": "Hello"}],
    strategy="balanced"
)

print(response.model.model_id)
```

### Advanced Configuration

```python
# Custom timeout and retries
client = GatewayClient(
    api_key="your_api_key",
    base_url="https://api.bifrost.ai",
    timeout=60.0,       # Request timeout in seconds
    max_retries=5,      # Maximum retry attempts
    use_http=True
)

# With constraints
response = await client.route(
    messages=[...],
    strategy="performance_optimized",
    constraints={
        "max_latency_ms": 200,
        "max_cost_usd": 0.05
    }
)
```

### Error Handling

```python
from bifrost_extensions.exceptions import (
    RoutingError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    ValidationError
)

try:
    response = await client.route(...)
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after_seconds}s")
except TimeoutError as e:
    print(f"Request timed out after {e.timeout_ms}ms")
except RoutingError as e:
    print(f"Routing failed: {e.message}")
```

### Context Manager

```python
# Automatic cleanup
async with GatewayClient(api_key="...") as client:
    response = await client.route(...)
# HTTP client is closed automatically
```

## Performance Considerations

### Connection Pooling

The HTTP client uses connection pooling for better performance:

- **Max connections:** 100
- **Max keepalive connections:** 20
- **Connection reuse:** Automatic

### Retry Strategy

Exponential backoff for transient failures:

```python
# Attempt 1: Immediate
# Attempt 2: 1 second delay
# Attempt 3: 2 seconds delay
# Attempt 4: 4 seconds delay
# ...up to max_retries
```

### Timeout Handling

- **Default:** 30 seconds
- **Per-request override:** Use `timeout` parameter
- **Recommended:** Increase for complex routing scenarios

```python
# Override timeout for specific request
response = await client.route(
    messages=[...],
    timeout=60.0  # 60 seconds
)
```

## Monitoring

### OpenTelemetry Tracing

Automatic distributed tracing via OpenTelemetry:

- **Trace context propagation:** Via HTTP headers
- **Span attributes:**
  - `routing.strategy`
  - `routing.message_count`
  - `request.id`
  - `routing.model` (in response)
  - `routing.confidence` (in response)

### Request IDs

Every request gets a unique ID for correlation:

```python
# Client-provided ID
import uuid
headers = {"X-Request-ID": str(uuid.uuid4())}

# Or auto-generated by server
# Response includes: X-Request-ID header
```

## Migration from Direct Imports

### Before (Week 1)
```python
from router.router_core.application import RoutingService

client = GatewayClient(use_http=False)  # Uses RoutingService directly
```

### After (Week 2+)
```python
# No router_core imports needed!

client = GatewayClient(use_http=True)  # Uses HTTP API
```

## Testing

### Unit Tests
```bash
pytest tests/unit/test_bifrost_client.py
```

### Integration Tests
```bash
# Start API server first
uvicorn bifrost_api.app:app --port 8000

# Run integration tests
pytest tests/integration/test_bifrost_api.py
```

### Performance Tests
```bash
pytest tests/performance/test_bifrost_latency.py
```

## Next Steps (Week 3)

1. **Remove direct router_core imports** from GatewayClient
2. **Add caching** for repeated routing requests
3. **Implement circuit breaker** for resilience
4. **Add metrics collection** (Prometheus)
5. **Deploy to production** infrastructure

## Troubleshooting

### Connection Refused

```
Error: Connection refused to http://localhost:8000
```

**Solution:** Start the API server:
```bash
uvicorn bifrost_api.app:app --port 8000
```

### Invalid API Key

```
401 Unauthorized: Invalid API key
```

**Solution:** Set valid API key:
```bash
export BIFROST_API_KEY="your_api_key_here"
```

### Rate Limit Exceeded

```
429 Too Many Requests: Rate limit exceeded
```

**Solution:** Wait for rate limit window to reset (60 seconds) or upgrade API tier.

### Timeout Errors

```
TimeoutError: Request timed out after 30.0s
```

**Solution:** Increase timeout:
```python
client = GatewayClient(timeout=60.0)
```

## License

MIT License - See LICENSE file for details.
