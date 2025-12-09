"""
Error flow E2E tests.

Tests error handling and system resilience:
- Error detection and recovery
- Performance under load
- Throughput and latency testing
"""

import pytest
import asyncio


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.integration
async def test_error_recovery_flow(
    bifrost_client,
    smartcp_stdio_client,
    track_performance
):
    """
    Test: Error handling and recovery across services.

    Flow:
    1. Execute tool that fails
    2. Detect error
    3. Route to recovery tool
    4. Execute recovery
    5. Verify recovery
    """
    stop = track_performance("error_recovery")

    # Step 1: Execute tool that will fail
    try:
        await smartcp_stdio_client.call_tool(
            name="execute",
            arguments={
                "command": "nonexistent_command_xyz",
                "cwd": None
            }
        )
    except Exception as error:
        # Step 2: Error detected
        print(f"Error detected: {error}")

        # Step 3: Route to recovery
        routing = await bifrost_client.route_request(
            prompt="Handle command execution error",
            context={"error": str(error)}
        )

        # Step 4: Execute recovery tool
        recovery_result = await smartcp_stdio_client.call_tool(
            name="execute",
            arguments={
                "command": "echo 'Recovery executed'",
                "cwd": None
            }
        )

        # Step 5: Verify recovery
        assert recovery_result.content

    duration = stop()

    print(f"Error recovery: {duration:.3f}s")


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.integration
async def test_performance_under_load(
    bifrost_client,
    smartcp_stdio_client,
    track_performance
):
    """
    Test: System performance under load.

    Execute many operations to test:
    - Throughput
    - Latency under load
    - Error rates
    - Resource usage
    """
    stop = track_performance("performance_load_test")

    async def operation(i: int):
        # Mix of operations
        if i % 3 == 0:
            return await bifrost_client.route_request(
                prompt=f"Operation {i}",
                context={}
            )
        elif i % 3 == 1:
            return await smartcp_stdio_client.call_tool(
                name="execute",
                arguments={"command": f"echo '{i}'", "cwd": None}
            )
        else:
            return await bifrost_client.query_tools(limit=10)

    # Execute 50 operations
    tasks = [operation(i) for i in range(50)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = stop()

    successes = [r for r in results if not isinstance(r, Exception)]
    success_rate = len(successes) / len(results) * 100

    print(f"Load test: {len(results)} ops in {duration:.3f}s")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Throughput: {len(results) / duration:.1f} ops/s")

    # Performance assertions
    assert success_rate >= 90, f"Success rate too low: {success_rate:.1f}%"
    assert duration < 60.0, f"Load test too slow: {duration:.3f}s"
