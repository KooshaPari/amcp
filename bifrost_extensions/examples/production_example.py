"""Production-ready example with all resilience patterns."""

import asyncio
from bifrost_extensions.resilient_client.client import ProductionGatewayClient
from bifrost_extensions.models import RoutingStrategy


async def main():
    """Demonstrate production-ready client usage."""

    # Initialize production client with full resilience
    async with ProductionGatewayClient(
        # Security
        api_key="your-api-key",  # Or from BIFROST_API_KEY env var

        # Connection pooling
        pool_size=100,

        # Retry configuration
        max_retries=3,
        timeout=30.0,

        # Rate limiting (100 req/sec, 200 burst)
        rate_limit=100,
        rate_limit_period=1.0,

        # Circuit breaker (open after 5 failures, recover after 60s)
        circuit_breaker_threshold=5,
        circuit_breaker_timeout=60.0,

        # Observability
        enable_metrics=True,
        log_level="INFO",
    ) as client:

        print("=== Production Gateway Client Demo ===\n")

        # 1. Health check
        print("1. Checking service health...")
        health = await client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Circuit: {health['circuit_breaker']['state']}")
        print(f"   Backend: {health.get('backend', {}).get('status', 'unknown')}\n")

        # 2. Simple routing with automatic resilience
        print("2. Routing request (with retry, rate limiting, circuit breaker)...")
        try:
            response = await client.route(
                messages=[
                    {"role": "user", "content": "Write a Python function to sort a list"}
                ],
                strategy=RoutingStrategy.COST_OPTIMIZED,
            )
            print(f"   Selected model: {response.model.model_id}")
            print(f"   Provider: {response.model.provider}")
            print(f"   Estimated cost: ${response.model.estimated_cost_usd:.6f}")
            print(f"   Confidence: {response.confidence:.2%}\n")
        except Exception as e:
            print(f"   Error: {e}\n")

        # 3. Batch requests (rate limited automatically)
        print("3. Sending batch requests (rate limited to 100/sec)...")
        tasks = []
        for i in range(10):
            task = client.route(
                messages=[
                    {"role": "user", "content": f"Request {i+1}"}
                ],
                strategy=RoutingStrategy.BALANCED,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if not isinstance(r, Exception))
        print(f"   Completed: {successful}/10 requests\n")

        # 4. Error handling demonstration
        print("4. Demonstrating error recovery...")
        try:
            # This will trigger input validation
            await client.route(
                messages=[
                    {"role": "invalid_role", "content": "test"}
                ],
            )
        except Exception as e:
            print(f"   Caught validation error: {type(e).__name__}")
            print(f"   Client continues to work (no crash)\n")

        # 5. Export metrics (Prometheus format)
        print("5. Exporting Prometheus metrics...")
        metrics = await client.get_metrics()
        lines = metrics.split("\n")
        print(f"   Collected {len([l for l in lines if l and not l.startswith('#')])} metrics")
        print("   Sample metrics:")
        for line in lines[:5]:
            if line and not line.startswith("#"):
                print(f"     {line}")
        print()

        print("=== Demo Complete ===")
        print("\nResilience features demonstrated:")
        print("  ✓ Automatic retry with exponential backoff")
        print("  ✓ Circuit breaker protection")
        print("  ✓ Token bucket rate limiting")
        print("  ✓ Connection pooling (httpx)")
        print("  ✓ Input validation and sanitization")
        print("  ✓ Output validation")
        print("  ✓ Structured JSON logging")
        print("  ✓ Prometheus metrics")
        print("  ✓ OpenTelemetry tracing")
        print("  ✓ Health checks")


if __name__ == "__main__":
    asyncio.run(main())
