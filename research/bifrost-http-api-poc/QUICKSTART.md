# Bifrost HTTP API - Quick Start Guide

## 5-Minute Setup

### 1. Start the API Server

```bash
# Navigate to project directory
cd /Users/kooshapari/temp-PRODVERCEL/485/API/smartcp

# Activate environment (if needed)
source .venv/bin/activate

# Start server
python bifrost_api/run_server.py --reload --port 8000
```

You should see:
```
Starting Bifrost API server on 0.0.0.0:8000
Workers: 1
Reload: True
Log level: info

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
Starting Bifrost API server...
INFO:     Application startup complete.
```

### 2. Test the API

Open a new terminal and test:

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","version":"1.0.0"}

# Test routing endpoint (with auth)
curl -X POST http://localhost:8000/v1/route \
  -H "X-API-Key: test_key_123456" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Write Python code"}],
    "strategy": "balanced"
  }'
```

### 3. Use the SDK

```python
import asyncio
from bifrost_extensions import GatewayClient, RoutingStrategy

async def main():
    # Create client (HTTP mode)
    client = GatewayClient(
        api_key="test_key_123456",
        base_url="http://localhost:8000",
        use_http=True  # This is the default in Week 2+
    )

    # Route a request
    response = await client.route(
        messages=[
            {"role": "user", "content": "Write a Python function"}
        ],
        strategy=RoutingStrategy.BALANCED
    )

    print(f"Selected model: {response.model.model_id}")
    print(f"Provider: {response.model.provider}")
    print(f"Estimated cost: ${response.model.estimated_cost_usd:.4f}")

asyncio.run(main())
```

### 4. Run Examples

```bash
# Make sure server is running first
python examples/bifrost_http_example.py
```

## Common Commands

### Start Server

```bash
# Development (auto-reload)
python bifrost_api/run_server.py --reload

# Production (multiple workers)
python bifrost_api/run_server.py --workers 4

# Custom port
python bifrost_api/run_server.py --port 8080

# Debug logging
python bifrost_api/run_server.py --reload --log-level debug
```

### Test Endpoints

```bash
# Health check (no auth required)
curl http://localhost:8000/health

# Route request
curl -X POST http://localhost:8000/v1/route \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"strategy":"balanced"}'

# Tool routing
curl -X POST http://localhost:8000/v1/route-tool \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"action":"search docs","available_tools":["web_search","doc_search"]}'

# Classification
curl -X POST http://localhost:8000/v1/classify \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Write Python code","categories":["simple","complex"]}'

# Usage stats
curl "http://localhost:8000/v1/usage?start_date=2025-12-01&end_date=2025-12-02" \
  -H "X-API-Key: your_api_key"
```

### Run Tests

```bash
# Unit tests (no server needed)
pytest tests/unit/ -v

# Integration tests (start server first)
python bifrost_api/run_server.py --port 8000 &
pytest tests/integration/test_bifrost_http_api.py -v
```

## API Overview

### Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/health` | Health check | ❌ |
| `POST` | `/v1/route` | Route to optimal model | ✅ |
| `POST` | `/v1/route-tool` | Route to optimal tool | ✅ |
| `POST` | `/v1/classify` | Classify prompt | ✅ |
| `GET` | `/v1/usage` | Get usage statistics | ✅ |

### Authentication

Include API key in header:

```bash
# Option 1: X-API-Key header
-H "X-API-Key: your_api_key"

# Option 2: Authorization header
-H "Authorization: Bearer your_api_key"
```

### Rate Limits

- **Limit:** 100 requests per minute per API key
- **Window:** 60 seconds (rolling)
- **Response headers:**
  - `X-RateLimit-Limit`: 100
  - `X-RateLimit-Remaining`: 95
  - `X-RateLimit-Reset`: 1733169600

## Environment Variables

```bash
# Optional: Set API key
export BIFROST_API_KEY="your_api_key_here"

# Optional: Set API URL
export BIFROST_API_URL="http://localhost:8000"
```

## Troubleshooting

### Server won't start

**Error:** `Address already in use`

```bash
# Find process
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
python bifrost_api/run_server.py --port 8001
```

### Import errors

**Error:** `ModuleNotFoundError: No module named 'bifrost_api'`

```bash
# Install in development mode
pip install -e .

# Or ensure PYTHONPATH includes project root
export PYTHONPATH=/Users/kooshapari/temp-PRODVERCEL/485/API/smartcp:$PYTHONPATH
```

### Connection refused

**Error:** `Connection refused to http://localhost:8000`

```bash
# Make sure server is running
python bifrost_api/run_server.py --reload
```

### 401 Unauthorized

**Error:** `401 Unauthorized: Missing API key`

```bash
# Include API key in request
curl -H "X-API-Key: test_key_123456" ...
```

### 429 Rate Limited

**Error:** `429 Too Many Requests`

**Solution:** Wait 60 seconds or use different API key

## Next Steps

1. **Read the documentation:** `bifrost_api/README.md`
2. **Explore examples:** `examples/bifrost_http_example.py`
3. **Run tests:** `pytest tests/integration/ -v`
4. **Check implementation:** `BIFROST_HTTP_API_IMPLEMENTATION.md`

## Quick Reference

```python
# Basic routing
from bifrost_extensions import GatewayClient, RoutingStrategy

client = GatewayClient(api_key="...", use_http=True)

response = await client.route(
    messages=[{"role": "user", "content": "..."}],
    strategy=RoutingStrategy.BALANCED
)

# Tool routing
decision = await client.route_tool(
    action="search docs",
    available_tools=["web_search", "doc_search"]
)

# Classification
result = await client.classify(
    prompt="Write code",
    categories=["simple", "complex"]
)

# Health check
health = await client.health_check()
```

## Support

For issues, see:
- Documentation: `bifrost_api/README.md`
- Implementation details: `BIFROST_HTTP_API_IMPLEMENTATION.md`
- Examples: `examples/bifrost_http_example.py`
- Tests: `tests/integration/test_bifrost_http_api.py`

Happy routing! 🚀
