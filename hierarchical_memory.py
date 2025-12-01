"""
Hierarchical Memory System for SmartCP

Provides:
- Global scope (shared across all sessions)
- Session scope (per-session state)
- Local scope (per-execution state)
- Persistence layer
- Synchronization
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum
from datetime import datetime
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryScope(Enum):
    """Memory scope levels."""
    GLOBAL = "global"
    SESSION = "session"
    LOCAL = "local"


@dataclass
class MemoryEntry:
    """Memory entry with metadata."""
    key: str
    value: Any
    scope: MemoryScope
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None  # Time to live in seconds
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        elapsed = (datetime.now() - self.updated_at).total_seconds()
        return elapsed > self.ttl


class GlobalMemory:
    """Global memory scope - shared across all sessions."""
    
    def __init__(self):
        self.data: Dict[str, MemoryEntry] = {}
        self.lock = asyncio.Lock()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set global memory value."""
        async with self.lock:
            self.data[key] = MemoryEntry(
                key=key,
                value=value,
                scope=MemoryScope.GLOBAL,
                ttl=ttl
            )
            logger.debug(f"Global memory set: {key}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get global memory value."""
        async with self.lock:
            entry = self.data.get(key)
            if entry and entry.is_expired():
                del self.data[key]
                return None
            return entry.value if entry else None
    
    async def delete(self, key: str) -> bool:
        """Delete global memory value."""
        async with self.lock:
            if key in self.data:
                del self.data[key]
                return True
            return False
    
    async def list_keys(self) -> List[str]:
        """List all global memory keys."""
        async with self.lock:
            return list(self.data.keys())


class SessionMemory:
    """Session memory scope - per-session state."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.data: Dict[str, MemoryEntry] = {}
        self.lock = asyncio.Lock()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set session memory value."""
        async with self.lock:
            self.data[key] = MemoryEntry(
                key=key,
                value=value,
                scope=MemoryScope.SESSION,
                ttl=ttl
            )
            logger.debug(f"Session {self.session_id} memory set: {key}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get session memory value."""
        async with self.lock:
            entry = self.data.get(key)
            if entry and entry.is_expired():
                del self.data[key]
                return None
            return entry.value if entry else None
    
    async def delete(self, key: str) -> bool:
        """Delete session memory value."""
        async with self.lock:
            if key in self.data:
                del self.data[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all session memory."""
        async with self.lock:
            self.data.clear()


class LocalMemory:
    """Local memory scope - per-execution state."""
    
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.data: Dict[str, MemoryEntry] = {}
        self.lock = asyncio.Lock()
    
    async def set(self, key: str, value: Any) -> None:
        """Set local memory value."""
        async with self.lock:
            self.data[key] = MemoryEntry(
                key=key,
                value=value,
                scope=MemoryScope.LOCAL
            )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get local memory value."""
        async with self.lock:
            entry = self.data.get(key)
            return entry.value if entry else None
    
    async def delete(self, key: str) -> bool:
        """Delete local memory value."""
        async with self.lock:
            if key in self.data:
                del self.data[key]
                return True
            return False


class PersistenceLayer:
    """Persistence layer for memory."""
    
    def __init__(self, db_path: str = "smartcp_memory.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                scope TEXT NOT NULL,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                ttl INTEGER,
                UNIQUE(key, scope)
            )
        """)
        self.conn.commit()
        logger.info(f"Persistence layer initialized: {self.db_path}")
    
    async def save(self, entry: MemoryEntry) -> None:
        """Save memory entry to database."""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO memory 
                (key, value, scope, created_at, updated_at, ttl)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry.key,
                json.dumps(entry.value),
                entry.scope.value,
                entry.created_at,
                entry.updated_at,
                entry.ttl
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error saving memory entry: {e}")
    
    async def load(self, key: str, scope: MemoryScope) -> Optional[MemoryEntry]:
        """Load memory entry from database."""
        try:
            cursor = self.conn.execute("""
                SELECT key, value, scope, created_at, updated_at, ttl
                FROM memory WHERE key = ? AND scope = ?
            """, (key, scope.value))
            
            row = cursor.fetchone()
            if row:
                return MemoryEntry(
                    key=row[0],
                    value=json.loads(row[1]),
                    scope=MemoryScope(row[2]),
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                    ttl=row[5]
                )
        except Exception as e:
            logger.error(f"Error loading memory entry: {e}")
        
        return None
    
    async def delete(self, key: str, scope: MemoryScope) -> None:
        """Delete memory entry from database."""
        try:
            self.conn.execute(
                "DELETE FROM memory WHERE key = ? AND scope = ?",
                (key, scope.value)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error deleting memory entry: {e}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()


class HierarchicalMemory:
    """Unified hierarchical memory system."""
    
    def __init__(self, persistence_enabled: bool = True, db_path: str = "smartcp_memory.db"):
        self.global_memory = GlobalMemory()
        self.session_memories: Dict[str, SessionMemory] = {}
        self.local_memories: Dict[str, LocalMemory] = {}
        self.persistence_enabled = persistence_enabled
        self.persistence = PersistenceLayer(db_path) if persistence_enabled else None
        self.lock = asyncio.Lock()
    
    async def create_session(self, session_id: str) -> SessionMemory:
        """Create new session memory."""
        async with self.lock:
            if session_id not in self.session_memories:
                self.session_memories[session_id] = SessionMemory(session_id)
                logger.info(f"Session created: {session_id}")
            return self.session_memories[session_id]
    
    async def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """Get session memory."""
        return self.session_memories.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session memory."""
        async with self.lock:
            if session_id in self.session_memories:
                await self.session_memories[session_id].clear()
                del self.session_memories[session_id]
                logger.info(f"Session deleted: {session_id}")
                return True
            return False
    
    async def create_execution(self, execution_id: str) -> LocalMemory:
        """Create new execution memory."""
        async with self.lock:
            if execution_id not in self.local_memories:
                self.local_memories[execution_id] = LocalMemory(execution_id)
            return self.local_memories[execution_id]
    
    async def delete_execution(self, execution_id: str) -> bool:
        """Delete execution memory."""
        async with self.lock:
            if execution_id in self.local_memories:
                del self.local_memories[execution_id]
                return True
            return False
    
    async def set(
        self,
        key: str,
        value: Any,
        scope: MemoryScope = MemoryScope.GLOBAL,
        session_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> None:
        """Set memory value in specified scope."""
        if scope == MemoryScope.GLOBAL:
            await self.global_memory.set(key, value, ttl)
            if self.persistence_enabled:
                entry = MemoryEntry(key, value, scope, ttl=ttl)
                await self.persistence.save(entry)
        
        elif scope == MemoryScope.SESSION and session_id:
            session = await self.get_session(session_id)
            if session:
                await session.set(key, value, ttl)
        
        elif scope == MemoryScope.LOCAL and execution_id:
            execution = self.local_memories.get(execution_id)
            if execution:
                await execution.set(key, value)
    
    async def get(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.GLOBAL,
        session_id: Optional[str] = None,
        execution_id: Optional[str] = None
    ) -> Optional[Any]:
        """Get memory value from specified scope."""
        if scope == MemoryScope.GLOBAL:
            return await self.global_memory.get(key)
        
        elif scope == MemoryScope.SESSION and session_id:
            session = await self.get_session(session_id)
            if session:
                return await session.get(key)
        
        elif scope == MemoryScope.LOCAL and execution_id:
            execution = self.local_memories.get(execution_id)
            if execution:
                return await execution.get(key)
        
        return None
    
    def close(self) -> None:
        """Close memory system."""
        if self.persistence:
            self.persistence.close()


# Global instance
_hierarchical_memory: Optional[HierarchicalMemory] = None


def get_hierarchical_memory() -> HierarchicalMemory:
    """Get or create global hierarchical memory."""
    global _hierarchical_memory
    if _hierarchical_memory is None:
        _hierarchical_memory = HierarchicalMemory()
    return _hierarchical_memory

