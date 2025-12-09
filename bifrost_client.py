"""Minimal async Bifrost GraphQL client for SmartCP.

Used to delegate execution, state, and memory operations to Bifrost.
Defaults target the local Bifrost backend (8080) when running via docker-compose.

Configuration is now centralized in config.bifrost module.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from config.bifrost import BifrostAuth, BifrostEndpoints, BifrostTimeouts

logger = logging.getLogger(__name__)


@dataclass
class BifrostClientConfig:
    """Configuration for the Bifrost client."""

    url: str = BifrostEndpoints.GRAPHQL_LOCAL
    api_key: Optional[str] = None
    timeout_seconds: float = BifrostTimeouts.DEFAULT_REQUEST


class BifrostClient:
    """Tiny GraphQL client with query/mutate helpers."""

    def __init__(self, config: Optional[BifrostClientConfig] = None):
        if config is None:
            self.config = BifrostClientConfig(
                url=BifrostEndpoints.get_graphql_endpoint(),
                api_key=BifrostAuth.get_api_key(),
                timeout_seconds=BifrostTimeouts.get_default(),
            )
        else:
            self.config = config
        self._client: Optional[httpx.AsyncClient] = None

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
        except Exception as exc:  # broad to ensure fallback can happen upstream
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

