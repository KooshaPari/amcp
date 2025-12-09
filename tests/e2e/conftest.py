"""E2E test fixtures for live service testing.

Provides fixtures for testing all services running together locally:
- Bifrost Gateway (localhost:8000)
- Go GraphQL Backend (localhost:8080)
- MLX gRPC Service (localhost:8001)
- SmartCP MCP Server

Note: Common fixtures like event_loop are imported from tests/fixtures via
root conftest.py. This module provides E2E-specific fixtures only.
"""

import asyncio
import os
import pytest
import httpx
from typing import AsyncGenerator, Generator
from pathlib import Path

# Test configuration
BIFROST_URL = os.getenv("E2E_BIFROST_URL", "http://localhost:8000")
GRAPHQL_URL = os.getenv("E2E_GRAPHQL_URL", "http://localhost:8080/graphql")
GRPC_URL = os.getenv("E2E_GRPC_URL", "localhost:8001")
SMARTCP_STDIO = os.getenv("E2E_SMARTCP_STDIO", "true")
TIMEOUT = int(os.getenv("E2E_TIMEOUT", "30"))


@pytest.fixture(scope="session")
async def wait_for_services():
    """Wait for all services to be healthy before running tests."""
    from tests.e2e.utils.wait_for_services import wait_for_all_services

    await wait_for_all_services(timeout=60)
    yield
    # No cleanup needed - services keep running


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide HTTP client for API calls."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        yield client


@pytest.fixture
async def bifrost_client(wait_for_services, http_client):
    """Provide Bifrost Gateway client."""
    from infrastructure.bifrost.client import BifrostClient

    client = BifrostClient(url=BIFROST_URL, timeout=TIMEOUT)
    await client.connect()
    yield client
    await client.disconnect()


@pytest.fixture
async def graphql_client(wait_for_services, http_client):
    """Provide GraphQL client for Go backend."""
    from services.bifrost import GraphQLSubscriptionClient, ConnectionConfig

    config = ConnectionConfig(url=GRAPHQL_URL.replace("http://", "ws://"))
    client = GraphQLSubscriptionClient(config)
    await client.connect()
    yield client
    await client.disconnect()


@pytest.fixture
async def smartcp_stdio_client(wait_for_services):
    """Provide SmartCP MCP client (stdio mode)."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@pytest.fixture
async def smartcp_http_client(wait_for_services, http_client):
    """Provide SmartCP HTTP client for SSE transport."""
    # Assumes SmartCP also exposes HTTP/SSE endpoint
    smartcp_url = os.getenv("E2E_SMARTCP_HTTP_URL", "http://localhost:8002")
    yield {
        "client": http_client,
        "base_url": smartcp_url
    }


@pytest.fixture
def cleanup_test_data():
    """Clean up test data after each test."""
    cleanup_tasks = []

    def register_cleanup(coro):
        cleanup_tasks.append(coro)

    yield register_cleanup

    # Run cleanup tasks
    loop = asyncio.get_event_loop()
    for task in cleanup_tasks:
        try:
            loop.run_until_complete(task)
        except Exception as e:
            print(f"Cleanup error: {e}")


@pytest.fixture
def test_workspace_id():
    """Provide test workspace ID."""
    return os.getenv("E2E_TEST_WORKSPACE_ID", "test-workspace-123")


@pytest.fixture
def test_user_id():
    """Provide test user ID."""
    return os.getenv("E2E_TEST_USER_ID", "test-user-123")


# Performance tracking
@pytest.fixture
def track_performance():
    """Track performance metrics for E2E tests."""
    import time

    metrics = {}

    def track(operation: str):
        start = time.perf_counter()

        def stop():
            duration = time.perf_counter() - start
            metrics[operation] = duration
            return duration

        return stop

    yield track

    # Print metrics at end
    if metrics:
        print("\n=== Performance Metrics ===")
        for op, duration in sorted(metrics.items(), key=lambda x: x[1], reverse=True):
            print(f"{op}: {duration:.3f}s")


# Error injection for resilience testing
@pytest.fixture
def inject_failure():
    """Inject failures for resilience testing."""
    failures = {}

    def set_failure(service: str, fail: bool):
        failures[service] = fail

    def should_fail(service: str) -> bool:
        return failures.get(service, False)

    yield {
        "set": set_failure,
        "check": should_fail
    }
