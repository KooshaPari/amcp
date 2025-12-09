"""Example usage of Bifrost SDK with HTTP API."""

import asyncio
import os

from bifrost_extensions import GatewayClient, RoutingStrategy
from bifrost_extensions.exceptions import (
    AuthenticationError,
    RateLimitError,
    RoutingError,
    TimeoutError,
)


async def basic_routing_example():
    """Basic routing example."""
    print("=" * 60)
    print("Basic Routing Example")
    print("=" * 60)

    # Create client (HTTP mode by default)
    client = GatewayClient(
        api_key=os.getenv("BIFROST_API_KEY", "demo_key_123"),
        base_url="http://localhost:8000",
        use_http=True,  # Use HTTP API (default in Week 2+)
    )

    try:
        # Route a simple request
        response = await client.route(
            messages=[
                {"role": "user", "content": "Write a Python function to parse JSON"}
            ],
            strategy=RoutingStrategy.BALANCED,
        )

        print(f"✓ Selected model: {response.model.model_id}")
        print(f"✓ Provider: {response.model.provider}")
        print(f"✓ Estimated cost: ${response.model.estimated_cost_usd:.4f}")
        print(f"✓ Estimated latency: {response.model.estimated_latency_ms}ms")
        print(f"✓ Confidence: {response.confidence:.2f}")
        if response.reasoning:
            print(f"✓ Reasoning: {response.reasoning}")

    except RoutingError as e:
        print(f"✗ Routing failed: {e.message}")


async def strategy_comparison_example():
    """Compare different routing strategies."""
    print("\n" + "=" * 60)
    print("Strategy Comparison Example")
    print("=" * 60)

    client = GatewayClient(
        api_key=os.getenv("BIFROST_API_KEY", "demo_key_123"),
        base_url="http://localhost:8000",
    )

    messages = [
        {"role": "user", "content": "Explain quantum computing in simple terms"}
    ]

    strategies = [
        RoutingStrategy.COST_OPTIMIZED,
        RoutingStrategy.PERFORMANCE_OPTIMIZED,
        RoutingStrategy.SPEED_OPTIMIZED,
        RoutingStrategy.BALANCED,
    ]

    for strategy in strategies:
        try:
            response = await client.route(messages=messages, strategy=strategy)

            print(f"\nStrategy: {strategy.value}")
            print(f"  Model: {response.model.model_id}")
            print(f"  Cost: ${response.model.estimated_cost_usd:.4f}")
            print(f"  Latency: {response.model.estimated_latency_ms}ms")
            print(f"  Confidence: {response.confidence:.2f}")

        except RoutingError as e:
            print(f"  ✗ Failed: {e.message}")


async def tool_routing_example():
    """Tool routing example."""
    print("\n" + "=" * 60)
    print("Tool Routing Example")
    print("=" * 60)

    client = GatewayClient(
        api_key=os.getenv("BIFROST_API_KEY", "demo_key_123"),
        base_url="http://localhost:8000",
    )

    try:
        # Route to best tool for action
        decision = await client.route_tool(
            action="search for Python documentation",
            available_tools=["web_search", "doc_search", "code_search"],
        )

        print(f"✓ Recommended tool: {decision.recommended_tool}")
        print(f"✓ Confidence: {decision.confidence:.2f}")
        if decision.reasoning:
            print(f"✓ Reasoning: {decision.reasoning}")

    except RoutingError as e:
        print(f"✗ Tool routing failed: {e.message}")


async def classification_example():
    """Classification example."""
    print("\n" + "=" * 60)
    print("Classification Example")
    print("=" * 60)

    client = GatewayClient(
        api_key=os.getenv("BIFROST_API_KEY", "demo_key_123"),
        base_url="http://localhost:8000",
    )

    prompts = [
        "What is 2+2?",
        "Write a Python function to parse JSON",
        "Explain the theory of relativity in detail",
    ]

    for prompt in prompts:
        try:
            result = await client.classify(
                prompt=prompt,
                categories=["simple", "moderate", "complex"],
            )

            print(f"\nPrompt: {prompt[:50]}...")
            print(f"  Category: {result.category}")
            print(f"  Complexity: {result.complexity}")
            print(f"  Confidence: {result.confidence:.2f}")

        except RoutingError as e:
            print(f"  ✗ Failed: {e.message}")


async def error_handling_example():
    """Error handling example."""
    print("\n" + "=" * 60)
    print("Error Handling Example")
    print("=" * 60)

    # Invalid API key
    print("\n1. Invalid API key:")
    client = GatewayClient(
        api_key="invalid_key",
        base_url="http://localhost:8000",
    )

    try:
        await client.route(
            messages=[{"role": "user", "content": "Hello"}],
            strategy=RoutingStrategy.BALANCED,
        )
    except AuthenticationError as e:
        print(f"  ✓ Caught AuthenticationError: {e.message}")

    # Timeout
    print("\n2. Request timeout:")
    client = GatewayClient(
        api_key=os.getenv("BIFROST_API_KEY", "demo_key_123"),
        base_url="http://localhost:8000",
        timeout=0.001,  # Very short timeout
    )

    try:
        await client.route(
            messages=[{"role": "user", "content": "Hello"}],
            strategy=RoutingStrategy.BALANCED,
        )
    except TimeoutError as e:
        print(f"  ✓ Caught TimeoutError: {e.message} ({e.timeout_ms}ms)")

    # Rate limiting (would require many requests)
    print("\n3. Rate limiting:")
    print("  (Skipped - requires 100+ requests)")


async def context_manager_example():
    """Context manager example."""
    print("\n" + "=" * 60)
    print("Context Manager Example")
    print("=" * 60)

    # Automatic cleanup
    async with GatewayClient(
        api_key=os.getenv("BIFROST_API_KEY", "demo_key_123"),
        base_url="http://localhost:8000",
    ) as client:
        response = await client.route(
            messages=[{"role": "user", "content": "Hello, world!"}],
            strategy=RoutingStrategy.BALANCED,
        )

        print(f"✓ Model selected: {response.model.model_id}")
        print("✓ HTTP client will be closed automatically")

    print("✓ Context exited, resources cleaned up")


async def health_check_example():
    """Health check example."""
    print("\n" + "=" * 60)
    print("Health Check Example")
    print("=" * 60)

    client = GatewayClient(
        api_key=os.getenv("BIFROST_API_KEY", "demo_key_123"),
        base_url="http://localhost:8000",
    )

    try:
        health = await client.health_check()

        print("✓ API Health Status:")
        print(f"  Status: {health.get('status', 'unknown')}")
        print(f"  Version: {health.get('version', 'unknown')}")
        print(f"  Service: {health.get('service', 'unknown')}")

    except RoutingError as e:
        print(f"✗ Health check failed: {e.message}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Bifrost SDK - HTTP API Examples")
    print("=" * 60)
    print("\nNOTE: Start the API server first:")
    print("  python bifrost_api/run_server.py --reload")
    print()

    # Wait for user confirmation
    input("Press Enter to continue...")

    try:
        await basic_routing_example()
        await strategy_comparison_example()
        await tool_routing_example()
        await classification_example()
        await error_handling_example()
        await context_manager_example()
        await health_check_example()

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
