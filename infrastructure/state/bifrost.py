"""Bifrost GraphQL-backed state adapter implementation."""

import json
import logging
from typing import Any, Optional

from smartcp.infrastructure.state.adapter import StateAdapter
from smartcp.infrastructure.state.errors import BifrostStateError, StateError
from smartcp.models.schemas import UserContext

logger = logging.getLogger(__name__)


class BifrostStateAdapter(StateAdapter):
    """Bifrost GraphQL-backed state adapter.

    Delegates all state operations to Bifrost via GraphQL.
    Supports TTL through server-side expiration management.

    Uses Bifrost GraphQL operations:
    - GetState query: Retrieve single state value
    - SetState mutation: Store or update state value
    - DeleteState mutation: Remove state value
    - ListState query: List keys with optional prefix filter
    """

    def __init__(self, bifrost_client):
        """Initialize with Bifrost GraphQL client.

        Args:
            bifrost_client: BifrostClient instance for GraphQL operations
        """
        self.client = bifrost_client

    async def get(
        self,
        user_ctx: UserContext,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get a state value for the user via Bifrost GraphQL.

        Args:
            user_ctx: User context for scoping
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        try:
            query = """
            query GetState(
                $userId: ID!,
                $deviceId: ID!,
                $key: String!
            ) {
              state(userId: $userId, deviceId: $deviceId, key: $key) {
                key
                value
                ttl
              }
            }
            """

            variables = {
                "userId": user_ctx.user_id,
                "deviceId": user_ctx.device_id or user_ctx.metadata.get("device_id", "default"),
                "key": key,
            }

            result = await self.client.query(query, variables)
            state_data = result.get("state")

            if not state_data:
                logger.debug(
                    "State key not found",
                    extra={
                        "user_id": user_ctx.user_id,
                        "key": key,
                        "request_id": user_ctx.request_id,
                    },
                )
                return default

            # Parse stored value
            value = state_data.get("value")
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return value

        except (ValueError, Exception) as e:
            logger.error(
                "Failed to get state",
                extra={
                    "user_id": user_ctx.user_id,
                    "key": key,
                    "error": str(e),
                    "request_id": user_ctx.request_id,
                },
            )
            raise BifrostStateError(str(e), "get", e) from e

    async def set(
        self,
        user_ctx: UserContext,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a state value for the user via Bifrost GraphQL.

        Args:
            user_ctx: User context for scoping
            key: State key
            value: Value to store (must be JSON-serializable)
            ttl: Optional time-to-live in seconds
        """
        try:
            mutation = """
            mutation SetState(
                $userId: ID!,
                $deviceId: ID!,
                $sessionId: ID,
                $projectId: ID,
                $key: String!,
                $value: JSON!,
                $ttl: Int
            ) {
              setState(
                userId: $userId,
                deviceId: $deviceId,
                sessionId: $sessionId,
                projectId: $projectId,
                key: $key,
                value: $value,
                ttl: $ttl
              ) {
                key
                value
                ttl
              }
            }
            """

            # Serialize value to JSON if needed
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = json.dumps({"data": value})

            variables = {
                "userId": user_ctx.user_id,
                "deviceId": user_ctx.device_id or user_ctx.metadata.get("device_id", "default"),
                "sessionId": user_ctx.session_id or user_ctx.metadata.get("session_id"),
                "projectId": user_ctx.project_id
                or user_ctx.workspace_id
                or user_ctx.metadata.get("project_id"),
                "key": key,
                "value": serialized_value,
                "ttl": ttl,
            }

            await self.client.mutate(mutation, variables)

            logger.debug(
                "State value set",
                extra={
                    "user_id": user_ctx.user_id,
                    "key": key,
                    "ttl": ttl,
                    "request_id": user_ctx.request_id,
                },
            )

        except (ValueError, Exception) as e:
            logger.error(
                "Failed to set state",
                extra={
                    "user_id": user_ctx.user_id,
                    "key": key,
                    "error": str(e),
                    "request_id": user_ctx.request_id,
                },
            )
            raise BifrostStateError(str(e), "set", e) from e

    async def delete(
        self,
        user_ctx: UserContext,
        key: str,
    ) -> bool:
        """Delete a state key via Bifrost GraphQL.

        Args:
            user_ctx: User context for scoping
            key: State key to delete

        Returns:
            True if key was deleted, False if not found
        """
        try:
            mutation = """
            mutation DeleteState(
                $userId: ID!,
                $deviceId: ID!,
                $key: String!
            ) {
              deleteState(
                userId: $userId,
                deviceId: $deviceId,
                key: $key
              ) {
                success
              }
            }
            """

            variables = {
                "userId": user_ctx.user_id,
                "deviceId": user_ctx.device_id or user_ctx.metadata.get("device_id", "default"),
                "key": key,
            }

            result = await self.client.mutate(mutation, variables)
            delete_result = result.get("deleteState", {})
            deleted = delete_result.get("success", False)

            logger.debug(
                "State key deleted" if deleted else "State key not found for deletion",
                extra={
                    "user_id": user_ctx.user_id,
                    "key": key,
                    "deleted": deleted,
                    "request_id": user_ctx.request_id,
                },
            )

            return deleted

        except (ValueError, Exception) as e:
            logger.error(
                "Failed to delete state",
                extra={
                    "user_id": user_ctx.user_id,
                    "key": key,
                    "error": str(e),
                    "request_id": user_ctx.request_id,
                },
            )
            raise BifrostStateError(str(e), "delete", e) from e

    async def exists(
        self,
        user_ctx: UserContext,
        key: str,
    ) -> bool:
        """Check if a state key exists.

        Args:
            user_ctx: User context for scoping
            key: State key to check

        Returns:
            True if key exists and is not expired
        """
        value = await self.get(user_ctx, key, default=None)
        return value is not None

    async def list_keys(
        self,
        user_ctx: UserContext,
        prefix: Optional[str] = None,
    ) -> list[str]:
        """List all state keys for the user via Bifrost GraphQL.

        Args:
            user_ctx: User context for scoping
            prefix: Optional key prefix filter

        Returns:
            List of matching keys
        """
        try:
            query = """
            query ListState(
                $userId: ID!,
                $deviceId: ID!,
                $prefix: String
            ) {
              listState(
                userId: $userId,
                deviceId: $deviceId,
                prefix: $prefix
              ) {
                items {
                  key
                }
              }
            }
            """

            variables = {
                "userId": user_ctx.user_id,
                "deviceId": user_ctx.device_id or user_ctx.metadata.get("device_id", "default"),
                "prefix": prefix,
            }

            result = await self.client.query(query, variables)
            list_result = result.get("listState", {})
            items = list_result.get("items", [])

            keys = [item["key"] for item in items]

            logger.debug(
                "Listed state keys",
                extra={
                    "user_id": user_ctx.user_id,
                    "prefix": prefix,
                    "count": len(keys),
                    "request_id": user_ctx.request_id,
                },
            )

            return keys

        except (ValueError, Exception) as e:
            logger.error(
                "Failed to list state keys",
                extra={
                    "user_id": user_ctx.user_id,
                    "prefix": prefix,
                    "error": str(e),
                    "request_id": user_ctx.request_id,
                },
            )
            raise BifrostStateError(str(e), "list", e) from e

    async def clear(
        self,
        user_ctx: UserContext,
        prefix: Optional[str] = None,
    ) -> int:
        """Clear all state for the user via Bifrost GraphQL.

        Args:
            user_ctx: User context for scoping
            prefix: Optional key prefix to limit deletion

        Returns:
            Number of keys deleted
        """
        try:
            if prefix:
                # Get keys first then delete individually
                keys = await self.list_keys(user_ctx, prefix=prefix)
                count = 0
                for key in keys:
                    if await self.delete(user_ctx, key):
                        count += 1
                return count
            else:
                # Delete all user state
                keys = await self.list_keys(user_ctx)
                count = 0
                for key in keys:
                    if await self.delete(user_ctx, key):
                        count += 1
                return count

        except (ValueError, Exception) as e:
            logger.error(
                "Failed to clear state",
                extra={
                    "user_id": user_ctx.user_id,
                    "prefix": prefix,
                    "error": str(e),
                    "request_id": user_ctx.request_id,
                },
            )
            raise BifrostStateError(str(e), "clear", e) from e

    async def get_many(
        self,
        user_ctx: UserContext,
        keys: list[str],
    ) -> dict[str, Any]:
        """Get multiple state values at once via Bifrost GraphQL.

        Args:
            user_ctx: User context for scoping
            keys: List of state keys

        Returns:
            Dictionary of key -> value (missing keys omitted)
        """
        try:
            result = {}
            for key in keys:
                try:
                    value = await self.get(user_ctx, key)
                    if value is not None:
                        result[key] = value
                except StateError:
                    # Skip keys that fail to retrieve
                    pass

            return result

        except (ValueError, Exception) as e:
            logger.error(
                "Failed to get multiple state values",
                extra={
                    "user_id": user_ctx.user_id,
                    "keys": keys,
                    "error": str(e),
                    "request_id": user_ctx.request_id,
                },
            )
            raise BifrostStateError(str(e), "get_many", e) from e

    async def set_many(
        self,
        user_ctx: UserContext,
        items: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Set multiple state values at once via Bifrost GraphQL.

        Args:
            user_ctx: User context for scoping
            items: Dictionary of key -> value to set
            ttl: Optional TTL for all items
        """
        for key, value in items.items():
            await self.set(user_ctx, key, value, ttl=ttl)

    async def increment(
        self,
        user_ctx: UserContext,
        key: str,
        amount: int = 1,
    ) -> int:
        """Increment a numeric state value via Bifrost GraphQL.

        Args:
            user_ctx: User context for scoping
            key: State key
            amount: Amount to increment (can be negative)

        Returns:
            New value after increment

        Raises:
            StateError: If current value is not numeric
        """
        current = await self.get(user_ctx, key, default=0)

        if not isinstance(current, (int, float)):
            raise StateError(f"Cannot increment non-numeric value for key '{key}'")

        new_value = current + amount
        await self.set(user_ctx, key, new_value)

        return new_value
