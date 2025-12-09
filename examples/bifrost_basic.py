"""
Basic Bifrost Extensions SDK Example

Demonstrates:
- Model routing with different strategies
- Tool routing
- Classification
- Error handling

Prerequisites:
- Bifrost Extensions SDK installed: pip install -e .
- BIFROST_API_KEY environment variable set (optional for local dev)

Run:
    python examples/bifrost_basic.py
"""

import asyncio
from bifrost_extensions import (
    GatewayClient,
    RoutingStrategy,
    ValidationError,
    RoutingError,
)


async def example_model_routing():
    """Example: Model routing with different strategies."""
    print("=" * 60)
    print("Example 1: Model Routing")
    print("=" * 60)

    client = GatewayClient()

    # Cost-optimized routing
    print("\n1. Cost-Optimized Routing:")
    response = await client.route(
        messages=[{"role": "user", "content": "Write a simple Python function"}],
        strategy=RoutingStrategy.COST_OPTIMIZED,
    )
    print(f"   Model: {response.model.model_id}")
    print(f"   Provider: {response.model.provider}")
    print(f"   Est. Cost: ${response.model.estimated_cost_usd:.4f}")
    print(f"   Confidence: {response.confidence:.2%}")

    # Performance-optimized routing
    print("\n2. Performance-Optimized Routing:")
    response = await client.route(
        messages=[{"role": "user", "content": "Complex code refactoring task"}],
        strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
    )
    print(f"   Model: {response.model.model_id}")
    print(f"   Provider: {response.model.provider}")
    print(f"   Est. Latency: {response.model.estimated_latency_ms:.0f}ms")

    # Balanced routing with constraints
    print("\n3. Balanced Routing with Constraints:")
    response = await client.route(
        messages=[{"role": "user", "content": "Moderate complexity task"}],
        strategy=RoutingStrategy.BALANCED,
        constraints={"max_cost_usd": 0.01, "max_latency_ms": 500},
    )
    print(f"   Model: {response.model.model_id}")
    print(f"   Provider: {response.model.provider}")


async def example_tool_routing():
    """Example: Tool routing."""
    print("\n" + "=" * 60)
    print("Example 2: Tool Routing")
    print("=" * 60)

    client = GatewayClient()

    decision = await client.route_tool(
        action="search for Python documentation on async/await",
        available_tools=["web_search", "doc_search", "semantic_search"],
    )

    print(f"\nAction: search for Python documentation")
    print(f"Recommended Tool: {decision.recommended_tool}")
    print(f"Confidence: {decision.confidence:.2%}")
    if decision.reasoning:
        print(f"Reasoning: {decision.reasoning}")


async def example_classification():
    """Example: Prompt classification."""
    print("\n" + "=" * 60)
    print("Example 3: Prompt Classification")
    print("=" * 60)

    client = GatewayClient()

    prompts = [
        "Write a hello world program",
        "Refactor this legacy codebase to use modern patterns",
        "Add type hints to this function",
    ]

    for prompt in prompts:
        result = await client.classify(
            prompt=prompt, categories=["simple", "moderate", "complex"]
        )
        print(f"\nPrompt: {prompt}")
        print(f"Category: {result.category}")
        print(f"Complexity: {result.complexity}")
        print(f"Confidence: {result.confidence:.2%}")


async def example_error_handling():
    """Example: Error handling."""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)

    client = GatewayClient()

    # Validation error
    try:
        await client.route(messages=[{"role": "invalid"}])  # Missing content
    except ValidationError as e:
        print(f"\n✓ Caught ValidationError: {e.message}")

    # Timeout error
    try:
        await client.route(
            messages=[{"role": "user", "content": "Test"}], timeout=0.001  # 1ms
        )
    except RoutingError as e:
        print(f"\n✓ Caught RoutingError: {e.message}")


async def example_health_check():
    """Example: Health check."""
    print("\n" + "=" * 60)
    print("Example 5: Health Check")
    print("=" * 60)

    client = GatewayClient()

    health = await client.health_check()
    print(f"\nSDK Status: {health['status']}")
    print(f"Version: {health['version']}")
    print(f"Router Available: {health['router_available']}")


async def main():
    """Run all examples."""
    print("\n🚀 Bifrost Extensions SDK - Basic Examples\n")

    await example_model_routing()
    await example_tool_routing()
    await example_classification()
    await example_error_handling()
    await example_health_check()

    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
