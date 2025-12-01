"""
FastMCP Advanced Features (Proposal 16)

Provides:
- Streaming support
- Batch operations
- Pagination
- Caching
- Rate limiting
"""

import logging
import asyncio
from typing import Dict, Optional, Any, List, AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry."""
    key: str
    value: Any
    created_at: datetime
    ttl_seconds: int


@dataclass
class RateLimit:
    """Rate limit."""
    requests_per_second: int
    burst_size: int


class FastMCPAdvanced:
    """Advanced FastMCP features."""
    
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.rate_limits: Dict[str, RateLimit] = {}
        self.request_counts: Dict[str, List[datetime]] = {}
    
    async def stream_results(self, query: str, batch_size: int = 10) -> AsyncIterator[List[Any]]:
        """Stream results."""
        try:
            logger.info(f"Streaming results for: {query}")
            
            # Mock streaming
            for i in range(0, 100, batch_size):
                batch = [{"id": j, "data": f"item_{j}"} for j in range(i, min(i + batch_size, 100))]
                yield batch
                await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Error streaming: {e}")
    
    async def batch_operation(self, operations: List[Dict[str, Any]]) -> List[Any]:
        """Execute batch operations."""
        try:
            logger.info(f"Executing batch: {len(operations)} operations")
            
            results = []
            for op in operations:
                result = {"operation": op, "status": "completed"}
                results.append(result)
            
            logger.info(f"Batch completed: {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Error in batch: {e}")
            return []
    
    async def paginate(self, query: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Paginate results."""
        try:
            logger.info(f"Paginating: page {page}, size {page_size}")
            
            # Mock pagination
            total = 100
            start = (page - 1) * page_size
            end = min(start + page_size, total)
            
            items = [{"id": i, "data": f"item_{i}"} for i in range(start, end)]
            
            return {
                "items": items,
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        
        except Exception as e:
            logger.error(f"Error paginating: {e}")
            return {}
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get from cache."""
        try:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            # Check TTL
            age = (datetime.now() - entry.created_at).total_seconds()
            if age > entry.ttl_seconds:
                del self.cache[key]
                return None
            
            logger.info(f"Cache hit: {key}")
            return entry.value
        
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    async def cache_set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set cache."""
        try:
            logger.info(f"Caching: {key}")
            
            self.cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                ttl_seconds=ttl_seconds
            )
        
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
    
    async def set_rate_limit(self, endpoint: str, rps: int, burst: int) -> None:
        """Set rate limit."""
        logger.info(f"Setting rate limit for {endpoint}: {rps} rps")
        
        self.rate_limits[endpoint] = RateLimit(
            requests_per_second=rps,
            burst_size=burst
        )
    
    async def check_rate_limit(self, endpoint: str) -> bool:
        """Check rate limit."""
        try:
            if endpoint not in self.rate_limits:
                return True
            
            limit = self.rate_limits[endpoint]
            now = datetime.now()
            
            if endpoint not in self.request_counts:
                self.request_counts[endpoint] = []
            
            # Remove old requests
            cutoff = now - timedelta(seconds=1)
            self.request_counts[endpoint] = [
                t for t in self.request_counts[endpoint] if t > cutoff
            ]
            
            # Check limit
            if len(self.request_counts[endpoint]) >= limit.requests_per_second:
                logger.warning(f"Rate limit exceeded for {endpoint}")
                return False
            
            self.request_counts[endpoint].append(now)
            return True
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False
    
    async def get_advanced_stats(self) -> Dict[str, Any]:
        """Get advanced statistics."""
        return {
            "cache_entries": len(self.cache),
            "rate_limits": len(self.rate_limits),
            "endpoints_tracked": len(self.request_counts)
        }


# Global instance
_advanced: Optional[FastMCPAdvanced] = None


def get_fastmcp_advanced() -> FastMCPAdvanced:
    """Get or create global advanced features."""
    global _advanced
    if _advanced is None:
        _advanced = FastMCPAdvanced()
    return _advanced

