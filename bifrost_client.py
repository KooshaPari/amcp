"""Minimal async Bifrost GraphQL client for SmartCP.

Used to delegate execution, state, and memory operations to Bifrost.
Defaults target the local Bifrost backend (8080) when running via docker-compose.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_BIFROST_URL = "http://localhost:8080/graphql"
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass
class BifrostClientConfig:
    """Configuration for the Bifrost client."""

    url: str = field(default_factory=lambda: os.environ.get("BIFROST_URL", DEFAULT_BIFROST_URL))
    api_key: Optional[str] = field(default_factory=lambda: os.environ.get("BIFROST_API_KEY"))
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


class BifrostClient:
    """Tiny GraphQL client with query/mutate helpers."""

    def __init__(self, config: Optional[BifrostClientConfig] = None):
        self.config = config or BifrostClientConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self.is_connected = False

    async def connect(self) -> None:
        """Connect to Bifrost backend."""
        await self._ensure_client()
        self.is_connected = True

    async def disconnect(self) -> None:
        """Disconnect from Bifrost backend."""
        await self.close()
        self.is_connected = False

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.config.url,
                timeout=self.config.timeout_seconds,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._execute(query, variables)

    async def mutate(self, mutation: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._execute(mutation, variables)

    async def _execute(self, document: str, variables: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        client = await self._ensure_client()
        payload = {"query": document, "variables": variables or {}}
        try:
            resp = await client.post("", json=payload)
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                logger.error("Bifrost GraphQL error", extra={"errors": data.get("errors")})
                raise RuntimeError(data["errors"])
            return data.get("data", {})
        except Exception as exc:
            logger.error(
                "Bifrost request failed",
                extra={"error": str(exc), "url": self.config.url},
            )
            raise

    async def health(self) -> bool:
        """Best-effort health probe via a lightweight introspection ping."""
        try:
            await self.query("query { __typename }")
            return True
        except Exception:
            return False

    async def __aenter__(self) -> "BifrostClient":
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
