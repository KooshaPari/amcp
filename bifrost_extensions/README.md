# Bifrost Extensions SDK

**Version:** 1.0.0 (Alpha - Week 1)
**Status:** 🚧 Under Development (Phase 4)

Production-grade SDK for intelligent LLM routing, tool routing, classification, and cost optimization.

---

## Quick Start

### Installation

```bash
# Development installation (local)
pip install -e .

# Production (when published)
pip install bifrost-extensions
```

### Basic Usage

```python
from bifrost_extensions import GatewayClient, RoutingStrategy

# Initialize client
client = GatewayClient()

# Route to optimal model
response = await client.route(
    messages=[
        {"role": "user", "content": "Analyze this Python code"}
    ],
    strategy=RoutingStrategy.COST_OPTIMIZED
)

print(f"Model: {response.model.model_id}")
print(f"Provider: {response.model.provider}")
print(f"Est. Cost: ${response.model.estimated_cost_usd:.4f}")
print(f"Confidence: {response.confidence:.2f}")
```

---

## Features

### ✅ Model Routing (Week 1)

Route LLM requests to optimal models based on strategy:

- **COST_OPTIMIZED**: Minimize cost while meeting quality requirements
- **PERFORMANCE_OPTIMIZED**: Maximize output quality
- **SPEED_OPTIMIZED**: Minimize latency
- **BALANCED**: Balance cost, speed, and quality
- **PARETO**: Multi-objective optimization

```python
# Cost-optimized routing
response = await client.route(
    messages=[{"role": "user", "content": "Simple task"}],
    strategy=RoutingStrategy.COST_OPTIMIZED,
    constraints={"max_cost_usd": 0.01}
)
```

### ⏳ Tool Routing (Week 2)

Route actions to optimal tools:

```python
decision = await client.route_tool(
    action="search for documentation",
    available_tools=["web_search", "doc_search", "semantic_search"]
)

print(f"Recommended: {decision.recommended_tool}")
print(f"Confidence: {decision.confidence}")
```

### ⏳ Classification (Week 2)

Classify prompts for routing optimization:

```python
result = await client.classify(
    prompt="Write a Python function to parse JSON"
)

print(f"Category: {result.category}")
print(f"Complexity: {result.complexity}")
```

### ⏳ Usage Tracking (Week 3)

Track costs and usage:

```python
stats = await client.get_usage(
    start_date="2025-12-01",
    end_date="2025-12-02",
    group_by="model"
)

print(f"Total requests: {stats.total_requests}")
print(f"Total cost: ${stats.total_cost_usd:.2f}")
```

---

## Architecture

### Current (Week 1 - Direct Integration)

```
GatewayClient
    ↓ Direct import
router/router_core/
    (Internal routing logic)
```

### Target (Week 2+ - HTTP API)

```
GatewayClient
    ↓ HTTP Client
Bifrost HTTP API
    ↓ Uses
router/router_core/
    (Internal routing logic)
```

---

## Development Status

### Week 1: Foundation ✅ (Current)
- [x] Package structure
- [x] GatewayClient API design
- [x] Pydantic models (request/response)
- [x] Exception hierarchy
- [x] OpenTelemetry spans
- [x] Unit tests (20 tests, all passing)
- [x] Basic documentation

### Week 2: Core Features (In Progress)
- [ ] Implement actual routing (use internal router)
- [ ] Tool routing logic
- [ ] Classification logic
- [ ] HTTP client (replace direct imports)
- [ ] Integration tests

### Week 3: Production Hardening
- [ ] Usage tracking
- [ ] Retry logic with exponential backoff
- [ ] Circuit breakers
- [ ] Performance benchmarks
- [ ] Load testing (1000 req/sec)

### Week 4: Finalization
- [ ] Decompose oversized files from router_core
- [ ] Complete documentation
- [ ] API examples (10+ use cases)
- [ ] Release candidate

---

## Testing

```bash
# Run unit tests
pytest tests/sdk/bifrost/ -v

# Run with coverage
pytest tests/sdk/bifrost/ --cov=bifrost_extensions

# Run specific test
pytest tests/sdk/bifrost/test_client.py::TestGatewayClient::test_route_basic -v
```

**Current Coverage:** 20 tests, all passing ✅

---

## API Reference

### GatewayClient

Main client for Bifrost routing operations.

#### `__init__(api_key, base_url, timeout, max_retries)`

Initialize the client.

**Args:**
- `api_key` (str, optional): Bifrost API key (or from `BIFROST_API_KEY` env)
- `base_url` (str): API base URL (default: `http://localhost:8000`)
- `timeout` (float): Request timeout seconds (default: 30.0)
- `max_retries` (int): Max retry attempts (default: 3)

#### `async route(messages, strategy, constraints, context, timeout)`

Route request to optimal model.

**Args:**
- `messages` (List[Message | Dict]): Conversation messages
- `strategy` (RoutingStrategy): Optimization strategy
- `constraints` (Dict, optional): Routing constraints
- `context` (Dict, optional): Additional context
- `timeout` (float, optional): Timeout override

**Returns:** `RoutingResponse` with selected model

**Raises:**
- `ValidationError`: Invalid request
- `RoutingError`: Routing failed
- `TimeoutError`: Operation timed out

#### `async route_tool(action, available_tools, context, timeout)`

Route action to optimal tool.

**Returns:** `ToolRoutingDecision` with recommended tool

#### `async classify(prompt, categories, timeout)`

Classify prompt.

**Returns:** `ClassificationResult` with category and confidence

#### `async get_usage(start_date, end_date, group_by, timeout)`

Get usage statistics.

**Returns:** `UsageStats` with aggregated metrics

#### `async health_check()`

Check SDK health.

**Returns:** Health status dictionary

---

## Error Handling

All errors inherit from `BifrostError`:

```python
from bifrost_extensions import (
    BifrostError,
    RoutingError,
    ValidationError,
    TimeoutError,
    AuthenticationError,
)

try:
    response = await client.route(messages=[...])
except ValidationError as e:
    print(f"Invalid request: {e.message}")
except RoutingError as e:
    print(f"Routing failed: {e.message}")
    print(f"Details: {e.details}")
except TimeoutError as e:
    print(f"Timed out: {e.message}")
```

---

## Observability

Built-in OpenTelemetry tracing:

```python
from opentelemetry import trace

# All operations create spans:
# - gateway.route
# - gateway.route_tool
# - gateway.classify
# - gateway.get_usage

# View traces in your observability platform
```

---

## Contributing

See `CLAUDE.md` for development guidelines.

**Week 2 Focus:**
- Implement actual routing logic
- Wire up internal router/router_core
- Add HTTP client layer
- Integration testing

---

## License

MIT
