"""
Wait for all services to be healthy before running E2E tests.

Checks health of:
- Bifrost Gateway (HTTP)
- Go GraphQL Backend (HTTP/GraphQL)
- MLX gRPC Service (gRPC health check)
- SmartCP MCP Server (stdio or HTTP)
"""

import asyncio
import os
import time
import httpx
import grpc
from typing import Optional


BIFROST_URL = os.getenv("E2E_BIFROST_URL", "http://localhost:8000")
GRAPHQL_URL = os.getenv("E2E_GRAPHQL_URL", "http://localhost:8080/graphql")
GRPC_URL = os.getenv("E2E_GRPC_URL", "localhost:8001")
SMARTCP_HTTP_URL = os.getenv("E2E_SMARTCP_HTTP_URL", "http://localhost:8002")


async def wait_for_bifrost(timeout: int = 60) -> bool:
    """Wait for Bifrost Gateway to be ready."""
    print("⏳ Waiting for Bifrost Gateway...")
    start = time.time()

    async with httpx.AsyncClient() as client:
        while time.time() - start < timeout:
            try:
                response = await client.get(f"{BIFROST_URL}/health")
                if response.status_code == 200:
                    print("✅ Bifrost Gateway is ready")
                    return True
            except (httpx.ConnectError, httpx.TimeoutException):
                pass

            await asyncio.sleep(2)

    print("❌ Bifrost Gateway timeout")
    return False


async def wait_for_graphql(timeout: int = 60) -> bool:
    """Wait for Go GraphQL backend to be ready."""
    print("⏳ Waiting for GraphQL Backend...")
    start = time.time()

    async with httpx.AsyncClient() as client:
        # Try introspection query
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """

        while time.time() - start < timeout:
            try:
                response = await client.post(
                    GRAPHQL_URL,
                    json={"query": query}
                )
                if response.status_code == 200:
                    result = response.json()
                    if "data" in result:
                        print("✅ GraphQL Backend is ready")
                        return True
            except (httpx.ConnectError, httpx.TimeoutException):
                pass

            await asyncio.sleep(2)

    print("❌ GraphQL Backend timeout")
    return False


async def wait_for_grpc(timeout: int = 60) -> bool:
    """Wait for MLX gRPC service to be ready."""
    print("⏳ Waiting for gRPC Service...")
    start = time.time()

    while time.time() - start < timeout:
        try:
            # Try to connect and perform health check
            channel = grpc.aio.insecure_channel(GRPC_URL)

            # Use standard gRPC health check protocol
            try:
                from grpc_health.v1 import health_pb2, health_pb2_grpc

                health_stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest()
                response = await health_stub.Check(request)

                if response.status == health_pb2.HealthCheckResponse.SERVING:
                    print("✅ gRPC Service is ready")
                    await channel.close()
                    return True
            except ImportError:
                # Fallback: just check if channel is ready
                await channel.channel_ready()
                print("✅ gRPC Service is ready (basic check)")
                await channel.close()
                return True

        except (grpc.aio.AioRpcError, Exception):
            pass

        await asyncio.sleep(2)

    print("❌ gRPC Service timeout")
    return False


async def wait_for_smartcp_http(timeout: int = 60) -> bool:
    """Wait for SmartCP HTTP endpoint (if available)."""
    print("⏳ Waiting for SmartCP HTTP...")
    start = time.time()

    async with httpx.AsyncClient() as client:
        while time.time() - start < timeout:
            try:
                response = await client.get(f"{SMARTCP_HTTP_URL}/health")
                if response.status_code == 200:
                    print("✅ SmartCP HTTP is ready")
                    return True
            except (httpx.ConnectError, httpx.TimeoutException):
                pass

            await asyncio.sleep(2)

    print("⚠️  SmartCP HTTP not available (stdio only?)")
    return True  # Not critical if using stdio


async def wait_for_smartcp_stdio(timeout: int = 60) -> bool:
    """Wait for SmartCP stdio mode to be ready."""
    print("⏳ Checking SmartCP stdio availability...")

    # Check if server.py exists
    import os.path
    if not os.path.exists("server.py"):
        print("❌ server.py not found")
        return False

    print("✅ SmartCP stdio ready (server.py exists)")
    return True


async def wait_for_all_services(timeout: int = 60) -> bool:
    """
    Wait for all services to be ready.

    Returns:
        True if all critical services are ready
    """
    print("\n" + "=" * 60)
    print("Waiting for services to be ready...")
    print("=" * 60 + "\n")

    results = await asyncio.gather(
        wait_for_bifrost(timeout),
        wait_for_graphql(timeout),
        wait_for_grpc(timeout),
        wait_for_smartcp_stdio(timeout),
        wait_for_smartcp_http(timeout),
        return_exceptions=True
    )

    # Check critical services (first 4)
    critical_ok = all(results[:4])

    if critical_ok:
        print("\n✅ All critical services are ready\n")
        return True
    else:
        print("\n❌ Some critical services failed to start\n")
        return False


async def main():
    """CLI entry point for testing service health."""
    success = await wait_for_all_services(timeout=60)
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
