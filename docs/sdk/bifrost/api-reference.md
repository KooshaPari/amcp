# Bifrost Extensions API Reference

Complete API reference for the Bifrost Extensions SDK.

## Table of Contents

- [GatewayClient](#gatewayclient)
  - [Constructor](#constructor)
  - [route()](#route)
  - [route_tool()](#route_tool)
  - [classify()](#classify)
  - [get_usage()](#get_usage)
  - [health_check()](#health_check)
- [Models](#models)
  - [RoutingStrategy](#routingstrategy)
  - [Message](#message)
  - [RoutingRequest](#routingrequest)
  - [RoutingResponse](#routingresponse)
  - [ModelInfo](#modelinfo)
  - [ToolRoutingDecision](#toolroutingdecision)
  - [ClassificationResult](#classificationresult)
  - [UsageStats](#usagestats)
- [Exceptions](#exceptions)

---

## GatewayClient

Main client for Bifrost routing operations.

### Constructor

```python
GatewayClient(
    api_key: Optional[str] = None,
    base_url: str = "http://localhost:8000",
    timeout: float = 30.0,
    max_retries: int = 3,
)
```

Initialize the Bifrost Gateway Client.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `api_key` | `Optional[str]` | `None` | Bifrost API key. If not provided, reads from `BIFROST_API_KEY` environment variable. |
| `base_url` | `str` | `"http://localhost:8000"` | Bifrost API base URL. |
| `timeout` | `float` | `30.0` | Request timeout in seconds. |
| `max_retries` | `int` | `3` | Maximum retry attempts for failed requests. |

**Returns:** `GatewayClient` instance

**Example:**

```python
from bifrost_extensions import GatewayClient

# With API key
client = GatewayClient(api_key="your-api-key")

# From environment variable
import os
os.environ["BIFROST_API_KEY"] = "your-api-key"
client = GatewayClient()

# With custom configuration
client = GatewayClient(
    base_url="https://api.bifrost.ai",
    timeout=60.0,
    max_retries=5
)
```

---

### route()

```python
async def route(
    messages: List[Message] | List[Dict[str, str]],
    strategy: RoutingStrategy = RoutingStrategy.BALANCED,
    constraints: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
) -> RoutingResponse
```

Route request to optimal model based on strategy and constraints.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `messages` | `List[Message]` or `List[Dict]` | *required* | Conversation messages. Can be `Message` objects or dicts with `role` and `content` keys. |
| `strategy` | `RoutingStrategy` | `BALANCED` | Routing optimization strategy. |
| `constraints` | `Optional[Dict[str, Any]]` | `None` | Optional constraints for routing (max cost, latency, etc.). |
| `context` | `Optional[Dict[str, Any]]` | `None` | Additional context for routing decision. |
| `timeout` | `Optional[float]` | `None` | Override default timeout for this request. |

**Returns:** `RoutingResponse` with selected model and metadata

**Raises:**
- `ValidationError`: If request is invalid (empty messages, invalid strategy, etc.)
- `RoutingError`: If routing fails (no models meet constraints, etc.)
- `TimeoutError`: If operation times out
- `AuthenticationError`: If API key is invalid

**Examples:**

**Basic routing:**
```python
response = await client.route(
    messages=[
        {"role": "user", "content": "Write a Python function"}
    ],
    strategy=RoutingStrategy.COST_OPTIMIZED
)

print(response.model.model_id)  # "gpt-4o-mini"
print(response.confidence)  # 0.92
```

**With constraints:**
```python
response = await client.route(
    messages=[
        {"role": "system", "content": "You are a Python expert"},
        {"role": "user", "content": "Review this code for bugs"}
    ],
    strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
    constraints={
        "max_cost_usd": 0.05,
        "max_latency_ms": 1000,
        "required_capabilities": ["function_calling"]
    }
)
```

**With context:**
```python
response = await client.route(
    messages=[
        {"role": "user", "content": "Analyze this SQL query"}
    ],
    strategy=RoutingStrategy.BALANCED,
    context={
        "user_id": "user_123",
        "task_type": "sql_analysis",
        "database": "postgresql",
        "priority": "high"
    }
)
```

**Multi-turn conversation:**
```python
from bifrost_extensions import Message

messages = [
    Message(role="system", content="You are a helpful assistant"),
    Message(role="user", content="What is Python?"),
    Message(role="assistant", content="Python is a programming language..."),
    Message(role="user", content="Show me an example")
]

response = await client.route(
    messages=messages,
    strategy=RoutingStrategy.BALANCED
)
```

---

### route_tool()

```python
async def route_tool(
    action: str,
    available_tools: List[str],
    context: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
) -> ToolRoutingDecision
```

Route action to optimal tool based on capabilities and context.

**Status:** Coming in v1.1

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `action` | `str` | *required* | Action description (e.g., "search for documentation"). |
| `available_tools` | `List[str]` | *required* | List of available tool names. |
| `context` | `Optional[Dict[str, Any]]` | `None` | Optional context for routing decision. |
| `timeout` | `Optional[float]` | `None` | Override default timeout. |

**Returns:** `ToolRoutingDecision` with recommended tool and metadata

**Raises:**
- `ValidationError`: If action is empty or no tools provided
- `RoutingError`: If routing fails
- `TimeoutError`: If operation times out

**Examples:**

**Basic tool routing:**
```python
decision = await client.route_tool(
    action="search for Python documentation",
    available_tools=["web_search", "doc_search", "semantic_search"]
)

print(decision.recommended_tool)  # "doc_search"
print(decision.confidence)  # 0.87
print(decision.reasoning)  # "Doc search is specialized for documentation..."
```

**With context:**
```python
decision = await client.route_tool(
    action="find recent news about AI",
    available_tools=["web_search", "news_api", "reddit_search"],
    context={
        "user_preferences": {"preferred_sources": ["arxiv", "techcrunch"]},
        "recency_requirement": "last_7_days"
    }
)
```

---

### classify()

```python
async def classify(
    prompt: str,
    categories: Optional[List[str]] = None,
    timeout: Optional[float] = None,
) -> ClassificationResult
```

Classify prompt for routing optimization and analytics.

**Status:** Coming in v1.1

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `prompt` | `str` | *required* | Prompt to classify. |
| `categories` | `Optional[List[str]]` | `None` | Target categories (or auto-detect if None). |
| `timeout` | `Optional[float]` | `None` | Override default timeout. |

**Returns:** `ClassificationResult` with category and confidence

**Raises:**
- `ValidationError`: If prompt is empty
- `RoutingError`: If classification fails
- `TimeoutError`: If operation times out

**Examples:**

**Auto-detect category:**
```python
result = await client.classify(
    prompt="Write a Python function to parse JSON"
)

print(result.category)  # "code_generation"
print(result.complexity)  # "simple"
print(result.confidence)  # 0.91
```

**With predefined categories:**
```python
result = await client.classify(
    prompt="Explain how quantum computing works",
    categories=["simple", "moderate", "complex", "expert"]
)

print(result.category)  # "complex"
print(result.subcategories)  # ["physics", "computer_science"]
```

---

### get_usage()

```python
async def get_usage(
    start_date: date | str,
    end_date: date | str,
    group_by: str = "model",
    timeout: Optional[float] = None,
) -> UsageStats
```

Get usage statistics and cost analytics.

**Status:** Coming in v1.2

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `start_date` | `date` or `str` | *required* | Start date (YYYY-MM-DD format if string). |
| `end_date` | `date` or `str` | *required* | End date (YYYY-MM-DD format if string). |
| `group_by` | `str` | `"model"` | Grouping dimension: `"model"`, `"provider"`, `"user"`, `"date"`. |
| `timeout` | `Optional[float]` | `None` | Override default timeout. |

**Returns:** `UsageStats` with aggregated metrics

**Raises:**
- `ValidationError`: If dates are invalid
- `RoutingError`: If retrieval fails
- `TimeoutError`: If operation times out

**Examples:**

**Daily usage:**
```python
from datetime import date, timedelta

today = date.today()
yesterday = today - timedelta(days=1)

stats = await client.get_usage(
    start_date=yesterday,
    end_date=today,
    group_by="model"
)

print(f"Total requests: {stats.total_requests}")
print(f"Total cost: ${stats.total_cost_usd:.2f}")
print(f"Average latency: {stats.avg_latency_ms}ms")

for model, count in stats.requests_by_model.items():
    cost = stats.cost_by_model[model]
    print(f"{model}: {count} requests, ${cost:.4f}")
```

**Monthly usage by provider:**
```python
stats = await client.get_usage(
    start_date="2025-11-01",
    end_date="2025-11-30",
    group_by="provider"
)

for provider, count in stats.requests_by_model.items():
    print(f"{provider}: {count} requests")
```

---

### health_check()

```python
async def health_check() -> Dict[str, Any]
```

Check SDK and routing service health.

**Returns:** Health status dictionary

**Example:**

```python
health = await client.health_check()

print(health["status"])  # "healthy" or "degraded" or "unhealthy"
print(health["version"])  # "1.0.0"
print(health["router_available"])  # True/False

# Example response:
{
    "status": "healthy",
    "version": "1.0.0",
    "router_available": True,
    "latency_ms": 5.2,
    "uptime_seconds": 3600.0
}
```

---

## Models

### RoutingStrategy

Enum for routing optimization strategies.

```python
class RoutingStrategy(str, Enum):
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    SPEED_OPTIMIZED = "speed_optimized"
    BALANCED = "balanced"
    PARETO = "pareto"
```

**Values:**

| Value | Description |
|-------|-------------|
| `COST_OPTIMIZED` | Minimize cost while meeting quality requirements |
| `PERFORMANCE_OPTIMIZED` | Maximize output quality |
| `SPEED_OPTIMIZED` | Minimize latency |
| `BALANCED` | Balance cost, speed, and quality |
| `PARETO` | Multi-objective Pareto optimization |

---

### Message

Chat message model.

```python
class Message(BaseModel):
    role: str  # "user", "assistant", or "system"
    content: str
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `role` | `str` | Message role (`"user"`, `"assistant"`, or `"system"`) |
| `content` | `str` | Message content |

**Example:**

```python
from bifrost_extensions import Message

message = Message(role="user", content="Hello, world!")
```

---

### RoutingRequest

Request for model routing.

```python
class RoutingRequest(BaseModel):
    messages: List[Message]
    strategy: RoutingStrategy = RoutingStrategy.BALANCED
    constraints: Optional[RoutingConstraints] = None
    context: Optional[Dict[str, Any]] = None
```

**Note:** Usually you don't need to create this manually; the `route()` method does it for you.

---

### RoutingResponse

Response from model routing.

```python
class RoutingResponse(BaseModel):
    model: ModelInfo
    confidence: float  # 0.0 to 1.0
    reasoning: Optional[str] = None
    alternatives: Optional[List[ModelInfo]] = None
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `model` | `ModelInfo` | Selected model information |
| `confidence` | `float` | Routing confidence (0.0 to 1.0) |
| `reasoning` | `Optional[str]` | Explanation of routing decision |
| `alternatives` | `Optional[List[ModelInfo]]` | Alternative model suggestions |

**Example:**

```python
response = await client.route(...)

print(f"Model: {response.model.model_id}")
print(f"Provider: {response.model.provider}")
print(f"Cost: ${response.model.estimated_cost_usd:.4f}")
print(f"Latency: {response.model.estimated_latency_ms}ms")
print(f"Confidence: {response.confidence:.2f}")

if response.reasoning:
    print(f"Reasoning: {response.reasoning}")

if response.alternatives:
    print("\nAlternatives:")
    for alt in response.alternatives:
        print(f"- {alt.model_id} (${alt.estimated_cost_usd:.4f})")
```

---

### ModelInfo

Information about a selected model.

```python
class ModelInfo(BaseModel):
    model_id: str
    provider: str
    estimated_cost_usd: float
    estimated_latency_ms: float
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | `str` | Model identifier (e.g., `"gpt-4o-mini"`) |
| `provider` | `str` | Provider name (e.g., `"openai"`) |
| `estimated_cost_usd` | `float` | Estimated cost in USD |
| `estimated_latency_ms` | `float` | Estimated latency in milliseconds |

---

### ToolRoutingDecision

Decision from tool routing.

```python
class ToolRoutingDecision(BaseModel):
    recommended_tool: str
    confidence: float  # 0.0 to 1.0
    reasoning: Optional[str] = None
    alternatives: Optional[List[str]] = None
```

---

### ClassificationResult

Result from prompt classification.

```python
class ClassificationResult(BaseModel):
    category: str
    confidence: float  # 0.0 to 1.0
    subcategories: Optional[List[str]] = None
    complexity: Optional[str] = None  # "simple", "moderate", or "complex"
```

---

### UsageStats

Usage statistics.

```python
class UsageStats(BaseModel):
    total_requests: int
    total_cost_usd: float
    avg_latency_ms: float
    requests_by_model: Dict[str, int]
    cost_by_model: Dict[str, float]
```

---

## Exceptions

All exceptions inherit from `BifrostError`.

### BifrostError

Base exception for all Bifrost SDK errors.

```python
class BifrostError(Exception):
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.details = details or {}
        self.cause = cause
```

### RoutingError

Raised when routing operation fails.

**Common Causes:**
- No models meet the specified constraints
- Internal routing service error
- Model catalog unavailable

**Example:**

```python
try:
    response = await client.route(
        messages=[...],
        constraints={"max_cost_usd": 0.0001}  # Too restrictive
    )
except RoutingError as e:
    print(f"Routing failed: {e.message}")
    if "alternatives" in e.details:
        print("Suggested alternatives:", e.details["alternatives"])
```

### ValidationError

Raised when request validation fails.

**Common Causes:**
- Empty messages list
- Invalid strategy
- Malformed constraints
- Invalid timeout value

**Example:**

```python
try:
    response = await client.route(messages=[])  # Empty!
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Details: {e.details}")
```

### TimeoutError

Raised when operation times out.

**Example:**

```python
try:
    response = await client.route(
        messages=[...],
        timeout=0.001  # Very short timeout
    )
except TimeoutError as e:
    print(f"Timeout: {e.message}")
    print(f"Timeout value: {e.timeout_ms}ms")
```

### AuthenticationError

Raised when API key is invalid or missing.

**Example:**

```python
try:
    client = GatewayClient(api_key="invalid-key")
    response = await client.route(...)
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
```

---

## Type Annotations

The SDK is fully typed for use with mypy, pyright, and other type checkers:

```python
from bifrost_extensions import GatewayClient, RoutingResponse

async def get_best_model(prompt: str) -> RoutingResponse:
    client: GatewayClient = GatewayClient()
    response: RoutingResponse = await client.route(
        messages=[{"role": "user", "content": prompt}]
    )
    return response
```

---

## Async Context Manager

Use `GatewayClient` as an async context manager for automatic cleanup:

```python
from bifrost_extensions import GatewayClient

async with GatewayClient() as client:
    response = await client.route(
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(response.model.model_id)

# Client automatically closed
```

---

See also:
- [Integration Guide](./integration-guide.md)
- [Examples](./examples/)
- [Architecture](./architecture.md)
