"""
Cleanup utilities for E2E tests.

Provides functions to clean up test data after E2E test runs.
"""

import asyncio
import httpx
import os
from typing import List, Optional


BIFROST_URL = os.getenv("E2E_BIFROST_URL", "http://localhost:8000")
GRAPHQL_URL = os.getenv("E2E_GRAPHQL_URL", "http://localhost:8080/graphql")


async def cleanup_test_entities(
    workspace_id: str,
    http_client: Optional[httpx.AsyncClient] = None
) -> None:
    """Clean up test entities from workspace."""
    close_client = False
    if http_client is None:
        http_client = httpx.AsyncClient()
        close_client = True

    try:
        # GraphQL mutation to delete test entities
        mutation = """
        mutation CleanupEntities($workspaceId: ID!) {
            deleteTestEntities(workspaceId: $workspaceId) {
                success
                deletedCount
            }
        }
        """

        response = await http_client.post(
            GRAPHQL_URL,
            json={
                "query": mutation,
                "variables": {"workspaceId": workspace_id}
            }
        )

        if response.status_code == 200:
            result = response.json()
            if "data" in result:
                print(f"Cleaned up test entities: {result['data']}")
        else:
            print(f"Cleanup warning: {response.status_code}")

    except Exception as e:
        print(f"Cleanup error: {e}")
    finally:
        if close_client:
            await http_client.aclose()


async def cleanup_test_memory(
    keys: List[str],
    smartcp_client
) -> None:
    """Clean up test memory entries."""
    for key in keys:
        try:
            await smartcp_client.call_tool(
                name="memory",
                arguments={
                    "action": "delete",
                    "key": key
                }
            )
            print(f"Deleted memory key: {key}")
        except Exception as e:
            print(f"Error deleting key {key}: {e}")


async def cleanup_test_state(smartcp_client) -> None:
    """Clean up test state."""
    try:
        await smartcp_client.call_tool(
            name="state",
            arguments={
                "action": "clear"
            }
        )
        print("Cleared test state")
    except Exception as e:
        print(f"Error clearing state: {e}")


async def cleanup_all(
    workspace_id: str,
    memory_keys: List[str],
    smartcp_client,
    http_client: Optional[httpx.AsyncClient] = None
) -> None:
    """
    Clean up all test data.

    Args:
        workspace_id: Workspace to clean
        memory_keys: Memory keys to delete
        smartcp_client: SmartCP client
        http_client: Optional HTTP client
    """
    print("\n=== Cleanup Started ===")

    await asyncio.gather(
        cleanup_test_entities(workspace_id, http_client),
        cleanup_test_memory(memory_keys, smartcp_client),
        cleanup_test_state(smartcp_client),
        return_exceptions=True
    )

    print("=== Cleanup Completed ===\n")


async def main():
    """CLI entry point for manual cleanup."""
    import sys

    workspace_id = sys.argv[1] if len(sys.argv) > 1 else "test-workspace-123"

    print(f"Cleaning up workspace: {workspace_id}")

    # Cleanup entities via HTTP
    async with httpx.AsyncClient() as client:
        await cleanup_test_entities(workspace_id, client)

    print("Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
