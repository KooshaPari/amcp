"""
MCP Lazy Loader

Provides:
- On-demand loading
- Caching
- Memory optimization
- Preloading
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CachedMCP:
    """Cached MCP."""
    name: str
    mcp: Any
    loaded_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0


class MCPLazyLoader:
    """Lazy load MCPs."""
    
    def __init__(self, max_cache_size: int = 100, ttl_seconds: int = 3600):
        self.cache: Dict[str, CachedMCP] = {}
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_seconds
        self.loaders: Dict[str, callable] = {}
    
    async def register_loader(self, name: str, loader: callable) -> None:
        """Register MCP loader."""
        logger.info(f"Registering loader for {name}")
        self.loaders[name] = loader
    
    async def lazy_load_mcp(self, name: str) -> Optional[Any]:
        """Lazy load MCP."""
        try:
            logger.info(f"Lazy loading MCP: {name}")
            
            # Check cache
            if name in self.cache:
                cached = self.cache[name]
                cached.last_accessed = datetime.now()
                cached.access_count += 1
                logger.info(f"Loaded {name} from cache (access #{cached.access_count})")
                return cached.mcp
            
            # Load from loader
            if name not in self.loaders:
                logger.error(f"No loader registered for {name}")
                return None
            
            loader = self.loaders[name]
            mcp = await loader()
            
            # Cache it
            await self._cache_mcp(name, mcp)
            
            logger.info(f"Loaded and cached {name}")
            return mcp
        
        except Exception as e:
            logger.error(f"Error lazy loading MCP: {e}")
            return None
    
    async def _cache_mcp(self, name: str, mcp: Any) -> None:
        """Cache MCP."""
        try:
            # Check cache size
            if len(self.cache) >= self.max_cache_size:
                await self._evict_lru()
            
            cached = CachedMCP(
                name=name,
                mcp=mcp,
                loaded_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                size_bytes=self._estimate_size(mcp)
            )
            
            self.cache[name] = cached
            logger.info(f"Cached {name} ({cached.size_bytes} bytes)")
        
        except Exception as e:
            logger.error(f"Error caching MCP: {e}")
    
    async def _evict_lru(self) -> None:
        """Evict least recently used MCP."""
        try:
            # Find LRU
            lru_name = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].last_accessed
            )
            
            del self.cache[lru_name]
            logger.info(f"Evicted LRU MCP: {lru_name}")
        
        except Exception as e:
            logger.error(f"Error evicting LRU: {e}")
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate object size."""
        try:
            import sys
            return sys.getsizeof(obj)
        except:
            return 0
    
    async def preload_mcp(self, name: str) -> bool:
        """Preload MCP."""
        try:
            logger.info(f"Preloading MCP: {name}")
            mcp = await self.lazy_load_mcp(name)
            return mcp is not None
        
        except Exception as e:
            logger.error(f"Error preloading MCP: {e}")
            return False
    
    async def unload_mcp(self, name: str) -> bool:
        """Unload MCP."""
        try:
            logger.info(f"Unloading MCP: {name}")
            
            if name in self.cache:
                del self.cache[name]
                logger.info(f"Unloaded {name}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error unloading MCP: {e}")
            return False
    
    async def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage."""
        try:
            logger.info("Optimizing memory")
            
            now = datetime.now()
            expired = []
            
            # Find expired entries
            for name, cached in self.cache.items():
                age = (now - cached.loaded_at).total_seconds()
                if age > self.ttl_seconds:
                    expired.append(name)
            
            # Remove expired
            for name in expired:
                del self.cache[name]
                logger.info(f"Removed expired MCP: {name}")
            
            # Calculate stats
            total_size = sum(c.size_bytes for c in self.cache.values())
            
            stats = {
                "cached_mcps": len(self.cache),
                "removed_expired": len(expired),
                "total_size_bytes": total_size,
                "max_cache_size": self.max_cache_size
            }
            
            logger.info(f"Memory optimization complete: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error optimizing memory: {e}")
            return {}
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(c.size_bytes for c in self.cache.values())
        total_accesses = sum(c.access_count for c in self.cache.values())
        
        return {
            "cached_mcps": len(self.cache),
            "total_size_bytes": total_size,
            "total_accesses": total_accesses,
            "max_cache_size": self.max_cache_size,
            "ttl_seconds": self.ttl_seconds,
            "mcps": [
                {
                    "name": c.name,
                    "size_bytes": c.size_bytes,
                    "access_count": c.access_count,
                    "age_seconds": (datetime.now() - c.loaded_at).total_seconds()
                }
                for c in self.cache.values()
            ]
        }


# Global instance
_lazy_loader: Optional[MCPLazyLoader] = None


def get_mcp_lazy_loader() -> MCPLazyLoader:
    """Get or create global lazy loader."""
    global _lazy_loader
    if _lazy_loader is None:
        _lazy_loader = MCPLazyLoader()
    return _lazy_loader

