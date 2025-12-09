# Basic Routing Examples

## Example 1: Simple Cost-Optimized Routing

```python
from bifrost_extensions import GatewayClient, RoutingStrategy

async def basic_routing_example():
    """Route a simple prompt with cost optimization."""
    client = GatewayClient()

    response = await client.route(
        messages=[
            {"role": "user", "content": "What is the capital of France?"}
        ],
        strategy=RoutingStrategy.COST_OPTIMIZED
    )

    print(f"Selected Model: {response.model.model_id}")
    print(f"Provider: {response.model.provider}")
    print(f"Estimated Cost: ${response.model.estimated_cost_usd:.6f}")
    print(f"Confidence: {response.confidence:.2%}")

# Run
import asyncio
asyncio.run(basic_routing_example())
```

**Output:**
```
Selected Model: gpt-4o-mini
Provider: openai
Estimated Cost: $0.000150
Confidence: 95.00%
```

---

## Example 2: Multi-Message Conversation

```python
from bifrost_extensions import GatewayClient, RoutingStrategy, Message

async def conversation_routing():
    """Route a multi-turn conversation."""
    client = GatewayClient()

    messages = [
        Message(role="system", content="You are a Python programming expert"),
        Message(role="user", content="How do I read a JSON file?"),
        Message(role="assistant", content="You can use json.load()..."),
        Message(role="user", content="Show me an example with error handling")
    ]

    response = await client.route(
        messages=messages,
        strategy=RoutingStrategy.BALANCED
    )

    print(f"Model: {response.model.model_id}")
    print(f"Reasoning: {response.reasoning}")

asyncio.run(conversation_routing())
```

---

## Example 3: Routing with Constraints

```python
async def constrained_routing():
    """Route with cost and latency constraints."""
    client = GatewayClient()

    response = await client.route(
        messages=[
            {"role": "user", "content": "Analyze this complex system architecture"}
        ],
        strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
        constraints={
            "max_cost_usd": 0.02,
            "max_latency_ms": 1000,
            "required_capabilities": ["function_calling", "json_mode"]
        }
    )

    print(f"Selected: {response.model.model_id}")
    print(f"Cost: ${response.model.estimated_cost_usd:.4f}")
    print(f"Latency: {response.model.estimated_latency_ms}ms")

asyncio.run(constrained_routing())
```

---

## Example 4: Batch Processing

```python
async def batch_routing():
    """Process multiple prompts in parallel."""
    client = GatewayClient()

    prompts = [
        "What is Python?",
        "How do I use async/await?",
        "Explain decorators",
        "What are generators?",
        "How does the GIL work?"
    ]

    # Process all concurrently
    tasks = [
        client.route(
            messages=[{"role": "user", "content": prompt}],
            strategy=RoutingStrategy.COST_OPTIMIZED
        )
        for prompt in prompts
    ]

    responses = await asyncio.gather(*tasks)

    # Analyze results
    total_cost = sum(r.model.estimated_cost_usd for r in responses)
    models_used = {r.model.model_id for r in responses}

    print(f"Processed {len(responses)} prompts")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Models used: {models_used}")

asyncio.run(batch_routing())
```

**Output:**
```
Processed 5 prompts
Total cost: $0.0075
Models used: {'gpt-4o-mini'}
```

---

## Example 5: Error Handling

```python
from bifrost_extensions import ValidationError, RoutingError, TimeoutError

async def error_handling_example():
    """Demonstrate comprehensive error handling."""
    client = GatewayClient()

    try:
        response = await client.route(
            messages=[
                {"role": "user", "content": "Complex task"}
            ],
            strategy=RoutingStrategy.COST_OPTIMIZED,
            constraints={
                "max_cost_usd": 0.0001  # Very restrictive!
            }
        )
    except ValidationError as e:
        print(f"Validation failed: {e.message}")
        print(f"Details: {e.details}")
    except RoutingError as e:
        print(f"Routing failed: {e.message}")
        if "alternatives" in e.details:
            print("Consider these alternatives:")
            for alt in e.details["alternatives"]:
                print(f"  - {alt}")
    except TimeoutError as e:
        print(f"Request timed out after {e.timeout_ms}ms")
    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(error_handling_example())
```

---

## Example 6: Custom Timeout

```python
async def custom_timeout_example():
    """Use custom timeout for routing."""
    client = GatewayClient()

    # For simple tasks, use shorter timeout
    response = await client.route(
        messages=[{"role": "user", "content": "Hello"}],
        strategy=RoutingStrategy.SPEED_OPTIMIZED,
        timeout=5.0  # 5 second timeout
    )

    print(f"Model: {response.model.model_id}")

asyncio.run(custom_timeout_example())
```

---

## Example 7: With Additional Context

```python
async def context_routing():
    """Provide additional context for routing."""
    client = GatewayClient()

    response = await client.route(
        messages=[
            {"role": "user", "content": "Review this SQL query for security"}
        ],
        strategy=RoutingStrategy.BALANCED,
        context={
            "user_id": "user_123",
            "organization_id": "org_456",
            "task_type": "security_review",
            "priority": "high",
            "domain": "database",
            "expertise_required": "sql_injection_detection"
        }
    )

    print(f"Selected: {response.model.model_id}")
    print(f"Reasoning: {response.reasoning}")

asyncio.run(context_routing())
```

---

## Example 8: Health Check

```python
async def health_check_example():
    """Check SDK and routing service health."""
    client = GatewayClient()

    health = await client.health_check()

    print(f"Status: {health['status']}")
    print(f"Version: {health['version']}")
    print(f"Router Available: {health['router_available']}")

    if health["status"] != "healthy":
        print("WARNING: Service degraded!")

asyncio.run(health_check_example())
```

**Output:**
```
Status: healthy
Version: 1.0.0
Router Available: True
```

---

See also:
- [Advanced Examples](./02-advanced-routing.md)
- [Tool Routing Examples](./03-tool-routing.md)
- [Integration Guide](../integration-guide.md)
