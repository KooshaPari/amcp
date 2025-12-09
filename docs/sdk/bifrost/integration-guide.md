# Bifrost Extensions Integration Guide

Practical guide for integrating the Bifrost Extensions SDK into your applications.

## Table of Contents

- [FastAPI Integration](#fastapi-integration)
- [Flask Integration](#flask-integration)
- [Django Integration](#django-integration)
- [Async Frameworks](#async-frameworks)
- [Multi-Tenant Applications](#multi-tenant-applications)
- [Cost Tracking](#cost-tracking)
- [Error Handling Strategies](#error-handling-strategies)
- [Performance Optimization](#performance-optimization)
- [Testing](#testing)

---

## FastAPI Integration

Integrate Bifrost into FastAPI applications for intelligent LLM routing.

### Basic Setup

```python
from fastapi import FastAPI, Depends, HTTPException
from bifrost_extensions import GatewayClient, RoutingStrategy, RoutingError
from pydantic import BaseModel
from typing import List

app = FastAPI(title="My LLM App")

# Dependency: Shared client
def get_bifrost_client() -> GatewayClient:
    return GatewayClient()

class ChatRequest(BaseModel):
    messages: List[dict]
    strategy: str = "balanced"

class ChatResponse(BaseModel):
    model: str
    provider: str
    estimated_cost: float

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    client: GatewayClient = Depends(get_bifrost_client)
):
    try:
        response = await client.route(
            messages=request.messages,
            strategy=RoutingStrategy(request.strategy)
        )

        return ChatResponse(
            model=response.model.model_id,
            provider=response.model.provider,
            estimated_cost=response.model.estimated_cost_usd
        )
    except RoutingError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### With Dependency Injection

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Initialize shared client on startup
    app.state.bifrost_client = GatewayClient()
    yield
    # Cleanup (if needed)

app = FastAPI(lifespan=lifespan)

async def get_client(request: Request) -> GatewayClient:
    return request.app.state.bifrost_client

@app.post("/chat")
async def chat(
    request: ChatRequest,
    client: GatewayClient = Depends(get_client)
):
    response = await client.route(...)
    return response
```

### With Request Context

```python
from fastapi import Request

@app.post("/chat")
async def chat(
    request: ChatRequest,
    http_request: Request,
    client: GatewayClient = Depends(get_client)
):
    # Add request context for better routing
    context = {
        "user_id": http_request.state.user_id,  # From auth middleware
        "request_id": http_request.headers.get("X-Request-ID"),
        "user_agent": http_request.headers.get("User-Agent"),
    }

    response = await client.route(
        messages=request.messages,
        strategy=RoutingStrategy(request.strategy),
        context=context
    )

    return response
```

---

## Flask Integration

Integrate with Flask applications (requires async support via Quart or async_to_sync).

### With Quart (Async Flask)

```python
from quart import Quart, request, jsonify
from bifrost_extensions import GatewayClient, RoutingStrategy

app = Quart(__name__)

# Global client (initialized once)
bifrost_client = GatewayClient()

@app.route("/chat", methods=["POST"])
async def chat():
    data = await request.get_json()

    try:
        response = await bifrost_client.route(
            messages=data["messages"],
            strategy=RoutingStrategy(data.get("strategy", "balanced"))
        )

        return jsonify({
            "model": response.model.model_id,
            "provider": response.model.provider,
            "cost": response.model.estimated_cost_usd
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
```

### With Standard Flask (Sync)

```python
from flask import Flask, request, jsonify
import asyncio
from bifrost_extensions import GatewayClient

app = Flask(__name__)
bifrost_client = GatewayClient()

def run_async(coro):
    """Helper to run async function in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    try:
        response = run_async(
            bifrost_client.route(
                messages=data["messages"],
                strategy=RoutingStrategy(data.get("strategy", "balanced"))
            )
        )

        return jsonify({
            "model": response.model.model_id,
            "cost": response.model.estimated_cost_usd
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

## Django Integration

Integrate with Django applications.

### Views

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import asyncio
import json
from bifrost_extensions import GatewayClient, RoutingStrategy

# Global client
bifrost_client = GatewayClient()

def run_async(coro):
    """Run async in sync Django view."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@csrf_exempt
def chat_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)

        response = run_async(
            bifrost_client.route(
                messages=data["messages"],
                strategy=RoutingStrategy(data.get("strategy", "balanced"))
            )
        )

        return JsonResponse({
            "model": response.model.model_id,
            "provider": response.model.provider,
            "cost": response.model.estimated_cost_usd
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
```

### With Django REST Framework

```python
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bifrost_extensions import GatewayClient, RoutingStrategy
import asyncio

class ChatView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bifrost_client = GatewayClient()

    def post(self, request):
        try:
            response = asyncio.run(
                self.bifrost_client.route(
                    messages=request.data["messages"],
                    strategy=RoutingStrategy(
                        request.data.get("strategy", "balanced")
                    )
                )
            )

            return Response({
                "model": response.model.model_id,
                "cost": response.model.estimated_cost_usd
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

---

## Async Frameworks

### With aiohttp

```python
from aiohttp import web
from bifrost_extensions import GatewayClient, RoutingStrategy

async def chat_handler(request):
    client = request.app["bifrost_client"]
    data = await request.json()

    try:
        response = await client.route(
            messages=data["messages"],
            strategy=RoutingStrategy(data.get("strategy", "balanced"))
        )

        return web.json_response({
            "model": response.model.model_id,
            "cost": response.model.estimated_cost_usd
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def init_app():
    app = web.Application()
    app["bifrost_client"] = GatewayClient()
    app.router.add_post("/chat", chat_handler)
    return app

if __name__ == "__main__":
    web.run_app(init_app())
```

### With Sanic

```python
from sanic import Sanic, response
from bifrost_extensions import GatewayClient, RoutingStrategy

app = Sanic("MyApp")
app.ctx.bifrost_client = GatewayClient()

@app.post("/chat")
async def chat(request):
    client = app.ctx.bifrost_client
    data = request.json

    try:
        resp = await client.route(
            messages=data["messages"],
            strategy=RoutingStrategy(data.get("strategy", "balanced"))
        )

        return response.json({
            "model": resp.model.model_id,
            "cost": resp.model.estimated_cost_usd
        })
    except Exception as e:
        return response.json({"error": str(e)}, status=500)
```

---

## Multi-Tenant Applications

Handle multiple tenants/organizations with different routing policies.

### Tenant-Specific Strategies

```python
from bifrost_extensions import GatewayClient, RoutingStrategy
from typing import Dict

class TenantRouter:
    def __init__(self):
        self.client = GatewayClient()
        self.tenant_strategies: Dict[str, RoutingStrategy] = {
            "free_tier": RoutingStrategy.COST_OPTIMIZED,
            "pro_tier": RoutingStrategy.BALANCED,
            "enterprise_tier": RoutingStrategy.PERFORMANCE_OPTIMIZED,
        }
        self.tenant_constraints: Dict[str, dict] = {
            "free_tier": {"max_cost_usd": 0.01},
            "pro_tier": {"max_cost_usd": 0.05},
            "enterprise_tier": {},  # No constraints
        }

    async def route_for_tenant(
        self,
        tenant_id: str,
        messages: list,
    ):
        # Get tenant info from database
        tenant = await get_tenant(tenant_id)
        tier = tenant.tier

        # Use tier-specific strategy and constraints
        strategy = self.tenant_strategies.get(tier, RoutingStrategy.BALANCED)
        constraints = self.tenant_constraints.get(tier, {})

        # Add tenant context
        context = {
            "tenant_id": tenant_id,
            "tier": tier,
            "organization": tenant.organization_id,
        }

        response = await self.client.route(
            messages=messages,
            strategy=strategy,
            constraints=constraints,
            context=context
        )

        # Track usage for tenant
        await track_tenant_usage(
            tenant_id=tenant_id,
            model=response.model.model_id,
            cost=response.model.estimated_cost_usd
        )

        return response

# Usage in FastAPI
router = TenantRouter()

@app.post("/chat/{tenant_id}")
async def chat(tenant_id: str, request: ChatRequest):
    response = await router.route_for_tenant(
        tenant_id=tenant_id,
        messages=request.messages
    )
    return response
```

### Per-User Rate Limiting

```python
from collections import defaultdict
import time

class RateLimitedRouter:
    def __init__(self):
        self.client = GatewayClient()
        self.user_requests = defaultdict(list)
        self.rate_limits = {
            "free": 10,      # 10 requests per minute
            "pro": 100,      # 100 requests per minute
            "enterprise": 1000,
        }

    async def route_with_rate_limit(
        self,
        user_id: str,
        tier: str,
        messages: list,
    ):
        # Check rate limit
        now = time.time()
        user_reqs = self.user_requests[user_id]

        # Remove requests older than 1 minute
        user_reqs = [req_time for req_time in user_reqs if now - req_time < 60]
        self.user_requests[user_id] = user_reqs

        # Check if over limit
        limit = self.rate_limits.get(tier, 10)
        if len(user_reqs) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit} requests per minute"
            )

        # Record this request
        user_reqs.append(now)

        # Route normally
        return await self.client.route(messages=messages)
```

---

## Cost Tracking

Track and analyze LLM costs across your application.

### Database Schema

```sql
CREATE TABLE llm_usage (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id VARCHAR(255),
    tenant_id VARCHAR(255),
    model_id VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    strategy VARCHAR(100),
    estimated_cost_usd DECIMAL(10, 6),
    actual_cost_usd DECIMAL(10, 6),
    latency_ms INTEGER,
    tokens_used INTEGER,
    request_metadata JSONB,
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id),
    INDEX idx_tenant_id (tenant_id)
);
```

### Usage Tracker

```python
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class UsageTracker:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    async def track_usage(
        self,
        user_id: str,
        tenant_id: str,
        routing_response,
        actual_cost: float = None,
        latency_ms: int = None,
        tokens_used: int = None,
        metadata: dict = None,
    ):
        session = self.Session()
        try:
            usage = Usage(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                tenant_id=tenant_id,
                model_id=routing_response.model.model_id,
                provider=routing_response.model.provider,
                estimated_cost_usd=routing_response.model.estimated_cost_usd,
                actual_cost_usd=actual_cost,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                request_metadata=metadata,
            )
            session.add(usage)
            session.commit()
        finally:
            session.close()

    async def get_cost_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "model",
    ):
        session = self.Session()
        try:
            # SQL query to aggregate costs
            query = f"""
                SELECT
                    {group_by},
                    COUNT(*) as request_count,
                    SUM(estimated_cost_usd) as total_estimated_cost,
                    SUM(actual_cost_usd) as total_actual_cost,
                    AVG(latency_ms) as avg_latency_ms
                FROM llm_usage
                WHERE timestamp BETWEEN :start_date AND :end_date
                GROUP BY {group_by}
                ORDER BY total_estimated_cost DESC
            """
            results = session.execute(query, {
                "start_date": start_date,
                "end_date": end_date
            })
            return results.fetchall()
        finally:
            session.close()
```

### Cost Monitoring Middleware

```python
from fastapi import Request
import time

class CostTrackingMiddleware:
    def __init__(self, app, tracker: UsageTracker):
        self.app = app
        self.tracker = tracker

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.time()

        # Store routing response in request state
        async def send_wrapper(message):
            if message["type"] == "http.response.body":
                # Track usage after response sent
                if hasattr(scope["state"], "routing_response"):
                    latency_ms = int((time.time() - start_time) * 1000)
                    await self.tracker.track_usage(
                        user_id=scope["state"].user_id,
                        tenant_id=scope["state"].tenant_id,
                        routing_response=scope["state"].routing_response,
                        latency_ms=latency_ms,
                    )
            await send(message)

        await self.app(scope, receive, send_wrapper)

# Add to FastAPI
app.add_middleware(CostTrackingMiddleware, tracker=usage_tracker)
```

---

## Error Handling Strategies

### Graceful Degradation

```python
from bifrost_extensions import RoutingError, TimeoutError

async def route_with_fallback(
    client: GatewayClient,
    messages: list,
    fallback_model: str = "gpt-4o-mini"
):
    try:
        # Try optimal routing
        response = await client.route(
            messages=messages,
            strategy=RoutingStrategy.BALANCED
        )
        return response
    except RoutingError as e:
        # Routing failed - use fallback
        logger.warning(f"Routing failed, using fallback: {e}")
        return await use_fallback_model(messages, fallback_model)
    except TimeoutError:
        # Timeout - use fastest model
        logger.warning("Routing timed out, using fast fallback")
        return await use_fallback_model(messages, "gpt-4o-mini")
```

### Retry with Exponential Backoff

```python
import asyncio
from typing import Optional

async def route_with_retry(
    client: GatewayClient,
    messages: list,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Optional[RoutingResponse]:
    for attempt in range(max_retries):
        try:
            response = await client.route(messages=messages)
            return response
        except RoutingError as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                raise
            # Exponential backoff
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
            await asyncio.sleep(delay)
```

---

## Performance Optimization

### Connection Pooling

```python
from bifrost_extensions import GatewayClient

# Single global client (reuse connections)
bifrost_client = GatewayClient()

# Not recommended: Creating new client per request
# async def bad_pattern():
#     client = GatewayClient()  # Don't do this
#     return await client.route(...)

# Recommended: Reuse global client
async def good_pattern():
    return await bifrost_client.route(...)
```

### Batch Processing

```python
async def process_batch(prompts: List[str]):
    client = GatewayClient()

    # Process all prompts concurrently
    tasks = [
        client.route(
            messages=[{"role": "user", "content": prompt}],
            strategy=RoutingStrategy.COST_OPTIMIZED
        )
        for prompt in prompts
    ]

    responses = await asyncio.gather(*tasks)
    return responses

# Process 100 prompts in parallel
responses = await process_batch(prompts)
```

### Caching

```python
from functools import lru_cache
import hashlib

class CachedRouter:
    def __init__(self):
        self.client = GatewayClient()
        self.cache = {}

    def _cache_key(self, messages: list, strategy: str) -> str:
        content = str(messages) + strategy
        return hashlib.md5(content.encode()).hexdigest()

    async def route_cached(
        self,
        messages: list,
        strategy: RoutingStrategy,
        ttl_seconds: int = 300,
    ):
        key = self._cache_key(messages, strategy.value)

        # Check cache
        if key in self.cache:
            cached_response, timestamp = self.cache[key]
            if time.time() - timestamp < ttl_seconds:
                return cached_response

        # Cache miss - route and cache
        response = await self.client.route(
            messages=messages,
            strategy=strategy
        )

        self.cache[key] = (response, time.time())
        return response
```

---

## Testing

### Unit Testing

```python
import pytest
from bifrost_extensions import GatewayClient, RoutingStrategy

@pytest.mark.asyncio
async def test_basic_routing():
    client = GatewayClient()

    response = await client.route(
        messages=[{"role": "user", "content": "test"}],
        strategy=RoutingStrategy.COST_OPTIMIZED
    )

    assert response.model.model_id is not None
    assert response.confidence >= 0.0
    assert response.confidence <= 1.0

@pytest.mark.asyncio
async def test_routing_with_constraints():
    client = GatewayClient()

    response = await client.route(
        messages=[{"role": "user", "content": "test"}],
        strategy=RoutingStrategy.BALANCED,
        constraints={"max_cost_usd": 0.01}
    )

    assert response.model.estimated_cost_usd <= 0.01
```

### Integration Testing

```python
from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_chat_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "strategy": "cost_optimized"
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    assert "cost" in data
```

### Mocking

```python
from unittest.mock import AsyncMock, patch
from bifrost_extensions import RoutingResponse, ModelInfo

@pytest.mark.asyncio
async def test_with_mock():
    # Mock routing response
    mock_response = RoutingResponse(
        model=ModelInfo(
            model_id="gpt-4o-mini",
            provider="openai",
            estimated_cost_usd=0.001,
            estimated_latency_ms=100
        ),
        confidence=0.95
    )

    with patch("bifrost_extensions.GatewayClient.route") as mock_route:
        mock_route.return_value = mock_response

        client = GatewayClient()
        response = await client.route(messages=[...])

        assert response.model.model_id == "gpt-4o-mini"
        mock_route.assert_called_once()
```

---

See also:
- [API Reference](./api-reference.md)
- [Examples](./examples/)
- [Architecture](./architecture.md)
