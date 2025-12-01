"""
Voyage AI Integration - Phase 6 Implementation

Provides embedding and reranking services using Voyage AI with:
- Text embedding generation (voyage-3, voyage-3-lite, voyage-code-3)
- Document reranking for search optimization
- Batch embedding with rate limiting
- Caching layer for embedding results
- Integration with Neo4j vector search
- MCP tool compatibility

Voyage AI provides state-of-the-art embeddings optimized for RAG applications.
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import (
    Any, Dict, List, Optional, Tuple, Union,
    TypeVar, Callable, Coroutine
)
from dataclasses import dataclass, field
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class VoyageModel(str, Enum):
    """Available Voyage AI embedding models."""
    VOYAGE_3 = "voyage-3"
    VOYAGE_3_LITE = "voyage-3-lite"
    VOYAGE_CODE_3 = "voyage-code-3"
    VOYAGE_FINANCE_2 = "voyage-finance-2"
    VOYAGE_LAW_2 = "voyage-law-2"
    VOYAGE_MULTILINGUAL_2 = "voyage-multilingual-2"


class InputType(str, Enum):
    """Input types for embedding optimization."""
    QUERY = "query"
    DOCUMENT = "document"


@dataclass
class VoyageConfig:
    """Voyage AI configuration."""
    api_key: str
    model: VoyageModel = VoyageModel.VOYAGE_3
    base_url: str = "https://api.voyageai.com/v1"
    max_batch_size: int = 128
    max_tokens_per_batch: int = 320000
    rate_limit_rpm: int = 300
    rate_limit_tpm: int = 1000000
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class EmbeddingResult:
    """Result from embedding generation."""
    embedding: List[float]
    text: str
    model: str
    input_type: Optional[str]
    usage: Dict[str, int]
    cached: bool = False

    @property
    def dimensions(self) -> int:
        """Embedding dimensions."""
        return len(self.embedding)


@dataclass
class RerankResult:
    """Result from document reranking."""
    index: int
    document: str
    relevance_score: float


@dataclass
class BatchEmbeddingResult:
    """Result from batch embedding."""
    embeddings: List[EmbeddingResult]
    total_tokens: int
    model: str
    processing_time_ms: float


class EmbeddingCache:
    """Cache for embedding results."""

    def __init__(self, cache_dir: str = ".voyage_cache", ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        self._memory_cache: Dict[str, Tuple[List[float], datetime]] = {}
        self._setup_cache_dir()

    def _setup_cache_dir(self) -> None:
        """Setup cache directory."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, mode=0o700)

    def _get_cache_key(self, text: str, model: str, input_type: Optional[str]) -> str:
        """Generate cache key for text."""
        key_data = f"{text}:{model}:{input_type or 'none'}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_cache_file(self, key: str) -> str:
        """Get cache file path."""
        return os.path.join(self.cache_dir, f"{key[:16]}.json")

    async def get(
        self,
        text: str,
        model: str,
        input_type: Optional[str] = None
    ) -> Optional[List[float]]:
        """Get embedding from cache."""
        key = self._get_cache_key(text, model, input_type)

        # Check memory cache first
        if key in self._memory_cache:
            embedding, cached_at = self._memory_cache[key]
            if _utcnow() - cached_at < self.ttl:
                return embedding
            else:
                del self._memory_cache[key]

        # Check file cache
        cache_file = self._get_cache_file(key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    cached_at = datetime.fromisoformat(data["cached_at"])
                    if _utcnow() - cached_at < self.ttl:
                        embedding = data["embedding"]
                        self._memory_cache[key] = (embedding, cached_at)
                        return embedding
            except Exception:
                pass

        return None

    async def set(
        self,
        text: str,
        model: str,
        embedding: List[float],
        input_type: Optional[str] = None
    ) -> None:
        """Store embedding in cache."""
        key = self._get_cache_key(text, model, input_type)
        now = _utcnow()

        # Store in memory
        self._memory_cache[key] = (embedding, now)

        # Store in file
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    "embedding": embedding,
                    "cached_at": now.isoformat(),
                    "model": model,
                    "input_type": input_type
                }, f)
            os.chmod(cache_file, 0o600)
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")

    async def clear(self) -> None:
        """Clear all cached embeddings."""
        self._memory_cache.clear()

        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                except Exception:
                    pass


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, rpm: int, tpm: int):
        self.rpm = rpm
        self.tpm = tpm
        self._request_times: List[datetime] = []
        self._token_usage: List[Tuple[datetime, int]] = []
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 0) -> None:
        """Acquire rate limit slot."""
        async with self._lock:
            now = _utcnow()
            minute_ago = now - timedelta(minutes=1)

            # Clean old entries
            self._request_times = [t for t in self._request_times if t > minute_ago]
            self._token_usage = [(t, n) for t, n in self._token_usage if t > minute_ago]

            # Check request rate
            while len(self._request_times) >= self.rpm:
                wait_time = (self._request_times[0] - minute_ago).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                now = _utcnow()
                minute_ago = now - timedelta(minutes=1)
                self._request_times = [t for t in self._request_times if t > minute_ago]

            # Check token rate
            current_tokens = sum(n for _, n in self._token_usage)
            while current_tokens + tokens > self.tpm:
                wait_time = (self._token_usage[0][0] - minute_ago).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                now = _utcnow()
                minute_ago = now - timedelta(minutes=1)
                self._token_usage = [(t, n) for t, n in self._token_usage if t > minute_ago]
                current_tokens = sum(n for _, n in self._token_usage)

            # Record usage
            self._request_times.append(now)
            if tokens > 0:
                self._token_usage.append((now, tokens))


class VoyageAIClient:
    """
    Voyage AI client for embeddings and reranking.

    Provides high-level API for text embedding and document reranking.
    """

    def __init__(
        self,
        config: VoyageConfig,
        cache: Optional[EmbeddingCache] = None
    ):
        self.config = config
        self.cache = cache or EmbeddingCache()
        self._rate_limiter = RateLimiter(config.rate_limit_rpm, config.rate_limit_tpm)
        self._http_client: Optional[Any] = None

    async def _get_client(self) -> Any:
        """Get or create HTTP client."""
        if self._http_client is None:
            try:
                import httpx
                self._http_client = httpx.AsyncClient(
                    timeout=self.config.timeout,
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json"
                    }
                )
            except ImportError:
                raise ImportError("httpx package required for Voyage AI client")
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def embed(
        self,
        text: str,
        input_type: Optional[InputType] = None,
        model: Optional[VoyageModel] = None,
        use_cache: bool = True
    ) -> EmbeddingResult:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed
            input_type: Query or document optimization
            model: Model override
            use_cache: Whether to use cache

        Returns:
            EmbeddingResult with embedding vector
        """
        model = model or self.config.model
        input_type_str = input_type.value if input_type else None

        # Check cache
        if use_cache:
            cached = await self.cache.get(text, model.value, input_type_str)
            if cached:
                return EmbeddingResult(
                    embedding=cached,
                    text=text,
                    model=model.value,
                    input_type=input_type_str,
                    usage={"total_tokens": 0},
                    cached=True
                )

        # Make API call
        result = await self._embed_batch([text], input_type, model)

        # Cache result
        if use_cache and result.embeddings:
            await self.cache.set(
                text, model.value,
                result.embeddings[0].embedding,
                input_type_str
            )

        return result.embeddings[0] if result.embeddings else EmbeddingResult(
            embedding=[],
            text=text,
            model=model.value,
            input_type=input_type_str,
            usage={"total_tokens": 0}
        )

    async def embed_batch(
        self,
        texts: List[str],
        input_type: Optional[InputType] = None,
        model: Optional[VoyageModel] = None,
        use_cache: bool = True
    ) -> BatchEmbeddingResult:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            input_type: Query or document optimization
            model: Model override
            use_cache: Whether to use cache

        Returns:
            BatchEmbeddingResult with all embeddings
        """
        import time
        start = time.perf_counter()

        model = model or self.config.model
        input_type_str = input_type.value if input_type else None

        results: List[EmbeddingResult] = []
        uncached_texts: List[str] = []
        uncached_indices: List[int] = []

        # Check cache for each text
        if use_cache:
            for i, text in enumerate(texts):
                cached = await self.cache.get(text, model.value, input_type_str)
                if cached:
                    results.append(EmbeddingResult(
                        embedding=cached,
                        text=text,
                        model=model.value,
                        input_type=input_type_str,
                        usage={"total_tokens": 0},
                        cached=True
                    ))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))

        # Fetch uncached embeddings
        total_tokens = 0
        if uncached_texts:
            # Split into batches
            for batch_start in range(0, len(uncached_texts), self.config.max_batch_size):
                batch_end = min(batch_start + self.config.max_batch_size, len(uncached_texts))
                batch_texts = uncached_texts[batch_start:batch_end]

                batch_result = await self._embed_batch(batch_texts, input_type, model)
                total_tokens += batch_result.total_tokens

                # Cache and store results
                for j, emb_result in enumerate(batch_result.embeddings):
                    if use_cache:
                        await self.cache.set(
                            emb_result.text, model.value,
                            emb_result.embedding,
                            input_type_str
                        )
                    results.append(emb_result)

        # Sort results back to original order
        sorted_results = [None] * len(texts)
        cached_idx = 0
        uncached_idx = 0
        for i in range(len(texts)):
            if i in uncached_indices:
                sorted_results[i] = results[len([j for j in uncached_indices if j < i])]
            else:
                # Find cached result
                for r in results:
                    if r.cached and r.text == texts[i]:
                        sorted_results[i] = r
                        break

        processing_time = (time.perf_counter() - start) * 1000

        return BatchEmbeddingResult(
            embeddings=[r for r in sorted_results if r],
            total_tokens=total_tokens,
            model=model.value,
            processing_time_ms=processing_time
        )

    async def _embed_batch(
        self,
        texts: List[str],
        input_type: Optional[InputType],
        model: VoyageModel
    ) -> BatchEmbeddingResult:
        """Internal batch embedding call."""
        import time
        start = time.perf_counter()

        # Estimate tokens (rough: 1 token per 4 chars)
        estimated_tokens = sum(len(t) // 4 for t in texts)
        await self._rate_limiter.acquire(estimated_tokens)

        client = await self._get_client()

        payload = {
            "input": texts,
            "model": model.value
        }
        if input_type:
            payload["input_type"] = input_type.value

        response = await self._make_request(
            "POST",
            f"{self.config.base_url}/embeddings",
            payload
        )

        embeddings = []
        for i, emb_data in enumerate(response.get("data", [])):
            embeddings.append(EmbeddingResult(
                embedding=emb_data["embedding"],
                text=texts[i],
                model=model.value,
                input_type=input_type.value if input_type else None,
                usage=response.get("usage", {})
            ))

        processing_time = (time.perf_counter() - start) * 1000

        return BatchEmbeddingResult(
            embeddings=embeddings,
            total_tokens=response.get("usage", {}).get("total_tokens", 0),
            model=model.value,
            processing_time_ms=processing_time
        )

    async def rerank(
        self,
        query: str,
        documents: List[str],
        model: str = "rerank-2",
        top_k: Optional[int] = None,
        return_documents: bool = True
    ) -> List[RerankResult]:
        """
        Rerank documents by relevance to query.

        Args:
            query: Query text
            documents: Documents to rerank
            model: Reranking model
            top_k: Number of top results
            return_documents: Include document text in results

        Returns:
            List of RerankResult sorted by relevance
        """
        await self._rate_limiter.acquire()

        payload = {
            "query": query,
            "documents": documents,
            "model": model,
            "return_documents": return_documents
        }
        if top_k:
            payload["top_k"] = top_k

        response = await self._make_request(
            "POST",
            f"{self.config.base_url}/rerank",
            payload
        )

        results = []
        for item in response.get("data", []):
            results.append(RerankResult(
                index=item["index"],
                document=documents[item["index"]] if return_documents else "",
                relevance_score=item["relevance_score"]
            ))

        return sorted(results, key=lambda x: x.relevance_score, reverse=True)

    async def _make_request(
        self,
        method: str,
        url: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make HTTP request with retries."""
        client = await self._get_client()

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                if method == "POST":
                    response = await client.post(url, json=payload)
                else:
                    response = await client.get(url)

                response.raise_for_status()
                return response.json()

            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

        raise last_error


# MCP Integration

class VoyageEmbeddingService:
    """
    Embedding service for MCP tools integration.

    Provides semantic search capabilities for MCP entities.
    """

    def __init__(self, client: VoyageAIClient):
        self.client = client

    async def embed_entity(
        self,
        entity_id: str,
        name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """
        Generate embedding for MCP entity.

        Combines entity fields into optimized text representation.
        """
        # Build text representation
        parts = [name]
        if description:
            parts.append(description)
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, str) and value:
                    parts.append(f"{key}: {value}")

        text = " | ".join(parts)

        result = await self.client.embed(text, input_type=InputType.DOCUMENT)
        return result.embedding

    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding optimized for search queries."""
        result = await self.client.embed(query, input_type=InputType.QUERY)
        return result.embedding

    async def semantic_search(
        self,
        query: str,
        candidates: List[Tuple[str, str]],  # (id, text) pairs
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Semantic search over candidate texts.

        Returns list of (id, score) pairs sorted by relevance.
        """
        if not candidates:
            return []

        # Get query embedding
        query_embedding = await self.embed_query(query)

        # Get candidate embeddings
        texts = [text for _, text in candidates]
        batch_result = await self.client.embed_batch(
            texts,
            input_type=InputType.DOCUMENT
        )

        # Calculate similarities
        import math
        results = []
        for i, emb_result in enumerate(batch_result.embeddings):
            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(query_embedding, emb_result.embedding))
            norm_q = math.sqrt(sum(a * a for a in query_embedding))
            norm_d = math.sqrt(sum(a * a for a in emb_result.embedding))
            similarity = dot_product / (norm_q * norm_d) if norm_q and norm_d else 0

            results.append((candidates[i][0], similarity))

        # Sort and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def rerank_search_results(
        self,
        query: str,
        results: List[Tuple[str, str, float]],  # (id, text, initial_score)
        top_k: Optional[int] = None
    ) -> List[Tuple[str, str, float]]:
        """
        Rerank search results using Voyage AI reranker.

        Returns reranked list of (id, text, rerank_score).
        """
        if not results:
            return []

        texts = [text for _, text, _ in results]
        reranked = await self.client.rerank(query, texts, top_k=top_k)

        return [
            (results[r.index][0], r.document, r.relevance_score)
            for r in reranked
        ]


# Neo4j Integration

class VoyageNeo4jIntegration:
    """
    Integration between Voyage AI embeddings and Neo4j vector search.

    Enables semantic search over Neo4j graph entities.
    """

    def __init__(
        self,
        voyage_client: VoyageAIClient,
        neo4j_adapter: Any  # Neo4jStorageAdapter
    ):
        self.voyage = voyage_client
        self.neo4j = neo4j_adapter
        self._index_name = "entity_embeddings"
        self._embedding_property = "embedding"

    async def setup_vector_index(
        self,
        label: str = "Entity",
        dimensions: int = 1024
    ) -> bool:
        """Create vector index in Neo4j."""
        return await self.neo4j.create_vector_index(
            index_name=self._index_name,
            label=label,
            property_name=self._embedding_property,
            dimensions=dimensions
        )

    async def index_entity(
        self,
        entity_id: str,
        text: str
    ) -> bool:
        """Generate embedding and store in Neo4j entity."""
        # Generate embedding
        result = await self.voyage.embed(text, input_type=InputType.DOCUMENT)

        # Update entity with embedding
        updated = await self.neo4j.update_entity(
            entity_id,
            {self._embedding_property: result.embedding}
        )

        return updated is not None

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.5
    ) -> List[Tuple[Any, float]]:
        """
        Search entities by semantic similarity.

        Returns list of (Entity, score) pairs.
        """
        # Generate query embedding
        query_result = await self.voyage.embed(query, input_type=InputType.QUERY)

        # Search in Neo4j
        results = await self.neo4j.vector_search(
            index_name=self._index_name,
            query_vector=query_result.embedding,
            top_k=top_k,
            min_score=min_score
        )

        return results

    async def batch_index_entities(
        self,
        entities: List[Tuple[str, str]]  # (entity_id, text)
    ) -> int:
        """
        Batch index multiple entities.

        Returns number of successfully indexed entities.
        """
        texts = [text for _, text in entities]

        # Generate embeddings in batch
        batch_result = await self.voyage.embed_batch(
            texts,
            input_type=InputType.DOCUMENT
        )

        # Update entities
        indexed = 0
        for i, emb_result in enumerate(batch_result.embeddings):
            entity_id = entities[i][0]
            updated = await self.neo4j.update_entity(
                entity_id,
                {self._embedding_property: emb_result.embedding}
            )
            if updated:
                indexed += 1

        return indexed
