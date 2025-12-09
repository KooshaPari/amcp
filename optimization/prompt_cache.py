"""
Prompt Cache Implementation

Implements Anthropic-style prompt caching with:
- Deterministic cache key generation from message content
- LRU eviction with configurable TTL
- Cache breakpoint markers for prefix matching
- 90% cost reduction on cache hits (research finding)
- Automatic cache warming for common patterns

Reference: 2025 LLM Cost Optimization Research
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from collections import OrderedDict
from enum import Enum

logger = logging.getLogger(__name__)


class CacheBreakpoint(str, Enum):
    """Cache breakpoint types for prefix matching."""
    EPHEMERAL = "ephemeral"  # Single-use, not cached
    SYSTEM = "system"  # System prompt (most reusable)
    CONTEXT = "context"  # Context/RAG content
    HISTORY = "history"  # Conversation history
    TOOLS = "tools"  # Tool definitions


@dataclass
class PromptCacheConfig:
    """Configuration for prompt caching."""

    # Cache sizing
    max_entries: int = 10000
    max_memory_mb: int = 512

    # TTL settings (in seconds)
    default_ttl: int = 3600  # 1 hour
    system_prompt_ttl: int = 86400  # 24 hours
    context_ttl: int = 1800  # 30 minutes

    # Prefix caching
    min_prefix_tokens: int = 1024  # Minimum tokens for prefix caching
    max_prefix_tokens: int = 128000  # Maximum cacheable prefix

    # Cost parameters
    cache_write_cost_multiplier: float = 1.25  # 25% extra for cache writes
    cache_read_cost_multiplier: float = 0.1  # 90% reduction on hits

    # Persistence
    persist_to_disk: bool = False
    persistence_path: str = "/tmp/smartcp_prompt_cache"

    # Warming
    enable_cache_warming: bool = True
    warm_common_prefixes: bool = True


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""

    key: str
    content: Any
    breakpoint: CacheBreakpoint
    token_count: int
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    ttl: int = 3600
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl

    def access(self) -> None:
        """Record an access."""
        self.last_accessed = time.time()
        self.hit_count += 1


@dataclass
class CacheStats:
    """Cache statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0
    memory_used_mb: float = 0.0
    tokens_cached: int = 0
    estimated_cost_savings: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class PromptCache:
    """
    LRU prompt cache with TTL and breakpoint support.

    Implements Anthropic-style prompt caching:
    1. System prompts cached longest (24h default)
    2. Context/RAG cached shorter (30m default)
    3. Prefix matching for partial hits
    4. Automatic eviction based on LRU + TTL

    Usage:
        cache = PromptCache(PromptCacheConfig())

        # Cache a system prompt
        await cache.set(
            messages=[{"role": "system", "content": "..."}],
            breakpoint=CacheBreakpoint.SYSTEM
        )

        # Check for cache hit
        hit = await cache.get(messages)
        if hit:
            # Use cached prefix, 90% cost reduction
            ...
    """

    def __init__(self, config: PromptCacheConfig = None):
        self.config = config or PromptCacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = CacheStats()
        logger.info(
            f"PromptCache initialized: max_entries={self.config.max_entries}, "
            f"max_memory_mb={self.config.max_memory_mb}"
        )

    def _compute_key(self, messages: list[dict[str, Any]]) -> str:
        """Compute deterministic cache key from messages."""
        # Normalize message content for consistent hashing
        normalized = []
        for msg in messages:
            normalized.append({
                "role": msg.get("role", ""),
                "content": str(msg.get("content", "")),
            })

        content = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def _compute_prefix_key(self, messages: list[dict[str, Any]], up_to: int) -> str:
        """Compute cache key for message prefix."""
        return self._compute_key(messages[:up_to])

    def _estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Estimate token count from messages."""
        total_chars = sum(
            len(str(msg.get("content", "")))
            for msg in messages
        )
        # Rough estimate: 4 chars per token
        return total_chars // 4

    def _get_ttl(self, breakpoint: CacheBreakpoint) -> int:
        """Get TTL based on breakpoint type."""
        if breakpoint == CacheBreakpoint.SYSTEM:
            return self.config.system_prompt_ttl
        elif breakpoint == CacheBreakpoint.CONTEXT:
            return self.config.context_ttl
        else:
            return self.config.default_ttl

    async def set(
        self,
        messages: list[dict[str, Any]],
        breakpoint: CacheBreakpoint = CacheBreakpoint.CONTEXT,
        response: Any = None,
    ) -> str:
        """
        Cache messages with optional response.

        Args:
            messages: List of message dicts
            breakpoint: Cache breakpoint type
            response: Optional response to cache

        Returns:
            Cache key
        """
        async with self._lock:
            key = self._compute_key(messages)
            token_count = self._estimate_tokens(messages)

            # Evict if needed
            await self._evict_if_needed()

            entry = CacheEntry(
                key=key,
                content={"messages": messages, "response": response},
                breakpoint=breakpoint,
                token_count=token_count,
                ttl=self._get_ttl(breakpoint),
            )

            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._stats.total_entries = len(self._cache)
            self._stats.tokens_cached += token_count

            logger.debug(
                f"Cached {token_count} tokens with key {key[:8]}..., "
                f"breakpoint={breakpoint.value}, ttl={entry.ttl}s"
            )

            return key

    async def get(
        self,
        messages: list[dict[str, Any]],
    ) -> Optional[dict[str, Any]]:
        """
        Get cached entry for messages.

        Supports prefix matching: if exact match not found,
        checks for longest matching prefix.

        Args:
            messages: List of message dicts

        Returns:
            Cache hit dict with 'cached_prefix_length' and optional 'response',
            or None if cache miss
        """
        async with self._lock:
            key = self._compute_key(messages)

            # Try exact match first
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    entry.access()
                    self._cache.move_to_end(key)
                    self._stats.hits += 1
                    self._update_cost_savings(entry.token_count)

                    logger.debug(f"Cache hit: key={key[:8]}..., hits={entry.hit_count}")
                    return {
                        "cached_prefix_length": len(messages),
                        "token_count": entry.token_count,
                        "response": entry.content.get("response"),
                        "hit_count": entry.hit_count,
                    }
                else:
                    # Expired, remove it
                    del self._cache[key]
                    self._stats.evictions += 1

            # Try prefix matching
            best_prefix = await self._find_longest_prefix(messages)
            if best_prefix:
                self._stats.hits += 1
                return best_prefix

            self._stats.misses += 1
            return None

    async def _find_longest_prefix(
        self,
        messages: list[dict[str, Any]],
    ) -> Optional[dict[str, Any]]:
        """Find longest cached prefix of messages."""
        # Try progressively shorter prefixes
        for prefix_len in range(len(messages) - 1, 0, -1):
            prefix_key = self._compute_prefix_key(messages, prefix_len)

            if prefix_key in self._cache:
                entry = self._cache[prefix_key]
                if not entry.is_expired():
                    entry.access()
                    self._cache.move_to_end(prefix_key)
                    self._update_cost_savings(entry.token_count)

                    logger.debug(
                        f"Prefix hit: key={prefix_key[:8]}..., "
                        f"prefix_len={prefix_len}/{len(messages)}"
                    )
                    return {
                        "cached_prefix_length": prefix_len,
                        "token_count": entry.token_count,
                        "response": None,  # No response for partial match
                        "hit_count": entry.hit_count,
                    }

        return None

    async def _evict_if_needed(self) -> None:
        """Evict entries if cache is full."""
        # Evict expired entries first
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
            self._stats.evictions += 1

        # LRU eviction if still over limit
        while len(self._cache) >= self.config.max_entries:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats.evictions += 1
            logger.debug(f"Evicted LRU entry: {oldest_key[:8]}...")

    def _update_cost_savings(self, token_count: int) -> None:
        """Update estimated cost savings from cache hit."""
        # Assume $0.003 per 1K input tokens (Claude Sonnet pricing)
        base_cost = (token_count / 1000) * 0.003
        cached_cost = base_cost * self.config.cache_read_cost_multiplier
        savings = base_cost - cached_cost
        self._stats.estimated_cost_savings += savings

    async def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        async with self._lock:
            self._stats.total_entries = len(self._cache)
            return self._stats

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
            logger.info("Cache cleared")

    async def warm_system_prompts(self, prompts: list[str]) -> int:
        """
        Pre-warm cache with common system prompts.

        Args:
            prompts: List of system prompts to cache

        Returns:
            Number of prompts cached
        """
        if not self.config.enable_cache_warming:
            return 0

        cached = 0
        for prompt in prompts:
            messages = [{"role": "system", "content": prompt}]
            await self.set(messages, breakpoint=CacheBreakpoint.SYSTEM)
            cached += 1

        logger.info(f"Warmed cache with {cached} system prompts")
        return cached


# Global cache instance
_prompt_cache: Optional[PromptCache] = None


def get_prompt_cache(config: PromptCacheConfig = None) -> PromptCache:
    """Get or create global prompt cache instance."""
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = PromptCache(config or PromptCacheConfig())
    return _prompt_cache
