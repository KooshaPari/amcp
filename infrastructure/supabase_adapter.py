"""Supabase Database Adapter for SmartCP.

Provides a typed wrapper around the Supabase client for database operations.
All database access should go through this adapter to ensure consistent
error handling, logging, and user context scoping.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass
class SupabaseConfig:
    """Supabase connection configuration."""

    url: str
    key: str
    service_role_key: Optional[str] = None
    timeout: float = 30.0
    auto_refresh_token: bool = True
    persist_session: bool = False


class SupabaseError(Exception):
    """Base error for Supabase operations."""

    def __init__(self, message: str, code: str = "SUPABASE_ERROR", details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class SupabaseConnectionError(SupabaseError):
    """Connection error to Supabase."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "CONNECTION_ERROR", details)


class SupabaseQueryError(SupabaseError):
    """Query execution error."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "QUERY_ERROR", details)


class SupabaseAdapter:
    """Adapter for Supabase database operations.

    Provides typed access to Supabase tables with consistent error handling
    and logging. Supports both service role (admin) and user-scoped access.

    Usage:
        adapter = SupabaseAdapter(config)
        await adapter.connect()

        # Query with user scoping (RLS applies)
        records = await adapter.select(
            "user_state",
            columns="*",
            filters={"user_id": user_id}
        )

        # Insert data
        result = await adapter.insert("user_state", {"key": "value"})

        # Update data
        updated = await adapter.update(
            "user_state",
            {"value": "new_value"},
            filters={"id": record_id}
        )
    """

    def __init__(self, config: SupabaseConfig):
        """Initialize adapter with configuration.

        Args:
            config: Supabase connection configuration
        """
        self.config = config
        self._client: Optional[Any] = None
        self._service_client: Optional[Any] = None

    @property
    def client(self) -> Any:
        """Get the Supabase client.

        Returns:
            Initialized Supabase client

        Raises:
            SupabaseConnectionError: If client not initialized
        """
        if self._client is None:
            raise SupabaseConnectionError(
                "Supabase client not initialized. Call connect() first."
            )
        return self._client

    @property
    def service_client(self) -> Any:
        """Get the service role client (bypasses RLS).

        Returns:
            Service role Supabase client

        Raises:
            SupabaseConnectionError: If service client not available
        """
        if self._service_client is None:
            raise SupabaseConnectionError(
                "Service role client not available. Configure service_role_key."
            )
        return self._service_client

    async def connect(self) -> None:
        """Initialize connection to Supabase.

        Creates both the regular client and optionally the service role client.
        """
        try:
            from supabase import create_client

            self._client = create_client(self.config.url, self.config.key)

            if self.config.service_role_key:
                self._service_client = create_client(
                    self.config.url, self.config.service_role_key
                )

            logger.info(
                "Supabase connection established",
                extra={"url": self.config.url[:50] + "..."},
            )

        except ImportError as e:
            raise SupabaseConnectionError(
                "Supabase library not installed. Install with: pip install supabase",
                details={"error": str(e)},
            ) from e
        except Exception as e:
            logger.error("Failed to connect to Supabase", extra={"error": str(e)})
            raise SupabaseConnectionError(
                f"Failed to connect to Supabase: {e}",
                details={"error": str(e)},
            ) from e

    async def disconnect(self) -> None:
        """Clean up Supabase connections."""
        self._client = None
        self._service_client = None
        logger.info("Supabase connection closed")

    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: int = 0,
        use_service_role: bool = False,
    ) -> list[dict[str, Any]]:
        """Select records from a table.

        Args:
            table: Table name
            columns: Columns to select (default "*")
            filters: Dictionary of column=value filters
            order_by: Column to order by
            ascending: Sort order (default True)
            limit: Maximum number of records
            offset: Number of records to skip
            use_service_role: Use service role client (bypasses RLS)

        Returns:
            List of matching records

        Raises:
            SupabaseQueryError: If query fails
        """
        try:
            client = self.service_client if use_service_role else self.client
            query = client.table(table).select(columns)

            if filters:
                for column, value in filters.items():
                    if value is None:
                        query = query.is_(column, "null")
                    elif isinstance(value, list):
                        query = query.in_(column, value)
                    else:
                        query = query.eq(column, value)

            if order_by:
                query = query.order(order_by, desc=not ascending)

            if limit:
                query = query.range(offset, offset + limit - 1)

            result = query.execute()

            logger.debug(
                "Select query completed",
                extra={
                    "table": table,
                    "filters": filters,
                    "count": len(result.data),
                },
            )

            return result.data

        except Exception as e:
            logger.error(
                "Select query failed",
                extra={"table": table, "filters": filters, "error": str(e)},
            )
            raise SupabaseQueryError(
                f"Select from {table} failed: {e}",
                details={"table": table, "filters": filters, "error": str(e)},
            ) from e

    async def select_one(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[dict[str, Any]] = None,
        use_service_role: bool = False,
    ) -> Optional[dict[str, Any]]:
        """Select a single record from a table.

        Args:
            table: Table name
            columns: Columns to select
            filters: Dictionary of filters
            use_service_role: Use service role client

        Returns:
            Single record or None if not found
        """
        results = await self.select(
            table=table,
            columns=columns,
            filters=filters,
            limit=1,
            use_service_role=use_service_role,
        )
        return results[0] if results else None

    async def insert(
        self,
        table: str,
        data: dict[str, Any],
        use_service_role: bool = False,
        return_data: bool = True,
    ) -> Optional[dict[str, Any]]:
        """Insert a record into a table.

        Args:
            table: Table name
            data: Record data to insert
            use_service_role: Use service role client
            return_data: Return the inserted record

        Returns:
            Inserted record if return_data=True

        Raises:
            SupabaseQueryError: If insert fails
        """
        try:
            client = self.service_client if use_service_role else self.client
            result = client.table(table).insert(data).execute()

            logger.debug(
                "Insert completed",
                extra={"table": table, "record_id": result.data[0].get("id") if result.data else None},
            )

            return result.data[0] if return_data and result.data else None

        except Exception as e:
            logger.error(
                "Insert failed",
                extra={"table": table, "error": str(e)},
            )
            raise SupabaseQueryError(
                f"Insert into {table} failed: {e}",
                details={"table": table, "error": str(e)},
            ) from e

    async def insert_many(
        self,
        table: str,
        data: list[dict[str, Any]],
        use_service_role: bool = False,
    ) -> list[dict[str, Any]]:
        """Insert multiple records into a table.

        Args:
            table: Table name
            data: List of records to insert
            use_service_role: Use service role client

        Returns:
            List of inserted records

        Raises:
            SupabaseQueryError: If insert fails
        """
        try:
            client = self.service_client if use_service_role else self.client
            result = client.table(table).insert(data).execute()

            logger.debug(
                "Bulk insert completed",
                extra={"table": table, "count": len(result.data)},
            )

            return result.data

        except Exception as e:
            logger.error(
                "Bulk insert failed",
                extra={"table": table, "count": len(data), "error": str(e)},
            )
            raise SupabaseQueryError(
                f"Bulk insert into {table} failed: {e}",
                details={"table": table, "count": len(data), "error": str(e)},
            ) from e

    async def update(
        self,
        table: str,
        data: dict[str, Any],
        filters: dict[str, Any],
        use_service_role: bool = False,
    ) -> list[dict[str, Any]]:
        """Update records in a table.

        Args:
            table: Table name
            data: Fields to update
            filters: Dictionary of filters to match records
            use_service_role: Use service role client

        Returns:
            List of updated records

        Raises:
            SupabaseQueryError: If update fails
        """
        try:
            client = self.service_client if use_service_role else self.client
            query = client.table(table).update(data)

            for column, value in filters.items():
                if value is None:
                    query = query.is_(column, "null")
                else:
                    query = query.eq(column, value)

            result = query.execute()

            logger.debug(
                "Update completed",
                extra={"table": table, "filters": filters, "count": len(result.data)},
            )

            return result.data

        except Exception as e:
            logger.error(
                "Update failed",
                extra={"table": table, "filters": filters, "error": str(e)},
            )
            raise SupabaseQueryError(
                f"Update {table} failed: {e}",
                details={"table": table, "filters": filters, "error": str(e)},
            ) from e

    async def upsert(
        self,
        table: str,
        data: dict[str, Any],
        on_conflict: str = "id",
        use_service_role: bool = False,
    ) -> dict[str, Any]:
        """Insert or update a record.

        Args:
            table: Table name
            data: Record data
            on_conflict: Column(s) to check for conflict
            use_service_role: Use service role client

        Returns:
            Upserted record

        Raises:
            SupabaseQueryError: If upsert fails
        """
        try:
            client = self.service_client if use_service_role else self.client
            result = client.table(table).upsert(data, on_conflict=on_conflict).execute()

            logger.debug(
                "Upsert completed",
                extra={"table": table, "on_conflict": on_conflict},
            )

            return result.data[0] if result.data else {}

        except Exception as e:
            logger.error(
                "Upsert failed",
                extra={"table": table, "error": str(e)},
            )
            raise SupabaseQueryError(
                f"Upsert into {table} failed: {e}",
                details={"table": table, "error": str(e)},
            ) from e

    async def delete(
        self,
        table: str,
        filters: dict[str, Any],
        use_service_role: bool = False,
    ) -> list[dict[str, Any]]:
        """Delete records from a table.

        Args:
            table: Table name
            filters: Dictionary of filters to match records
            use_service_role: Use service role client

        Returns:
            List of deleted records

        Raises:
            SupabaseQueryError: If delete fails
        """
        try:
            client = self.service_client if use_service_role else self.client
            query = client.table(table).delete()

            for column, value in filters.items():
                if value is None:
                    query = query.is_(column, "null")
                else:
                    query = query.eq(column, value)

            result = query.execute()

            logger.debug(
                "Delete completed",
                extra={"table": table, "filters": filters, "count": len(result.data)},
            )

            return result.data

        except Exception as e:
            logger.error(
                "Delete failed",
                extra={"table": table, "filters": filters, "error": str(e)},
            )
            raise SupabaseQueryError(
                f"Delete from {table} failed: {e}",
                details={"table": table, "filters": filters, "error": str(e)},
            ) from e

    async def rpc(
        self,
        function_name: str,
        params: Optional[dict[str, Any]] = None,
        use_service_role: bool = False,
    ) -> Any:
        """Call a Supabase RPC function.

        Args:
            function_name: Name of the function to call
            params: Function parameters
            use_service_role: Use service role client

        Returns:
            Function result

        Raises:
            SupabaseQueryError: If RPC call fails
        """
        try:
            client = self.service_client if use_service_role else self.client
            result = client.rpc(function_name, params or {}).execute()

            logger.debug(
                "RPC call completed",
                extra={"function": function_name},
            )

            return result.data

        except Exception as e:
            logger.error(
                "RPC call failed",
                extra={"function": function_name, "error": str(e)},
            )
            raise SupabaseQueryError(
                f"RPC call to {function_name} failed: {e}",
                details={"function": function_name, "error": str(e)},
            ) from e


def create_supabase_adapter(
    url: Optional[str] = None,
    key: Optional[str] = None,
    service_role_key: Optional[str] = None,
) -> SupabaseAdapter:
    """Factory function to create a Supabase adapter.

    Args:
        url: Supabase project URL (or from SUPABASE_URL env)
        key: Supabase anon key (or from SUPABASE_KEY env)
        service_role_key: Optional service role key (or from SUPABASE_SERVICE_ROLE_KEY env)

    Returns:
        Configured SupabaseAdapter instance
    """
    import os

    config = SupabaseConfig(
        url=url or os.environ.get("SUPABASE_URL", ""),
        key=key or os.environ.get("SUPABASE_KEY", ""),
        service_role_key=service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    )

    if not config.url or not config.key:
        raise ValueError(
            "Supabase URL and key are required. "
            "Set SUPABASE_URL and SUPABASE_KEY environment variables."
        )

    return SupabaseAdapter(config)
