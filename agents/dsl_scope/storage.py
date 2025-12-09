"""
Multi-level storage for scoped variables.

Implements three-tier storage:
- Memory: BLOCK, TOOL_CALL scopes (transient)
- Redis: PROMPT_CHAIN, SESSION scopes (medium-term)
- Database: GLOBAL, PERMANENT scopes (long-term)
"""

import sqlite3
import json
import logging
import asyncio
from typing import Optional
from pathlib import Path
from datetime import datetime

from dsl_scope.scope_levels import ScopeEntry, ScopeLevel

logger = logging.getLogger(__name__)


class ScopeStorage:
    """Multi-level storage with in-memory + persistence."""

    def __init__(self, db_path: str = "dsl_scope.db"):
        self.db_path = Path(db_path)
        self.memory: dict[str, dict[str, ScopeEntry]] = {
            level.value: {} for level in ScopeLevel
        }
        self.lock = asyncio.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database for persistent scopes."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))

        conn.execute("""
            CREATE TABLE IF NOT EXISTS scope_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                scope_level TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                ttl INTEGER,
                metadata TEXT,
                UNIQUE(key, scope_level)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scope_entries_scope_level
            ON scope_entries(scope_level)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scope_entries_key
            ON scope_entries(key)
        """)

        conn.commit()
        conn.close()
        logger.info(f"Scope storage DB initialized: {self.db_path}")

    async def set(
        self,
        key: str,
        value: any,
        scope_level: ScopeLevel,
        ttl: Optional[int] = None,
        persist: bool = True,
        metadata: Optional[dict[str, any]] = None,
    ) -> None:
        """Set scope variable."""
        async with self.lock:
            entry = ScopeEntry(
                key=key,
                value=value,
                scope_level=scope_level,
                ttl=ttl,
                metadata=metadata or {},
            )

            # Store in memory
            self.memory[scope_level.value][key] = entry

            # Persist to DB if requested and scope is persistent
            if persist and scope_level in (ScopeLevel.GLOBAL, ScopeLevel.PERMANENT):
                self._persist_entry(entry)

    async def get(self, key: str, scope_level: ScopeLevel) -> Optional[any]:
        """Get scope variable."""
        async with self.lock:
            entry = self.memory[scope_level.value].get(key)

            # Load from DB if not in memory and scope is persistent
            if entry is None and scope_level in (
                ScopeLevel.GLOBAL,
                ScopeLevel.PERMANENT,
            ):
                entry = self._load_from_db(key, scope_level)
                # Cache in memory
                if entry:
                    self.memory[scope_level.value][key] = entry

            if entry and not entry.is_expired():
                return entry.value

            # Clean up expired entry
            if entry and entry.is_expired():
                await self.delete(key, scope_level)

            return None

    async def lookup(
        self, key: str, scopes: list[ScopeLevel]
    ) -> Optional[any]:
        """Lookup variable across scope hierarchy."""
        for scope in scopes:
            value = await self.get(key, scope)
            if value is not None:
                return value
        return None

    async def delete(self, key: str, scope_level: ScopeLevel) -> bool:
        """Delete scope variable."""
        async with self.lock:
            if key in self.memory[scope_level.value]:
                del self.memory[scope_level.value][key]

            if scope_level in (ScopeLevel.GLOBAL, ScopeLevel.PERMANENT):
                self._delete_from_db(key, scope_level)

            return True

    async def clear_scope(self, scope_level: ScopeLevel) -> None:
        """Clear all entries in a scope."""
        async with self.lock:
            self.memory[scope_level.value].clear()
            if scope_level in (ScopeLevel.GLOBAL, ScopeLevel.PERMANENT):
                self._clear_db_scope(scope_level)

    async def list_keys(self, scope_level: ScopeLevel) -> list[str]:
        """List all keys in a scope."""
        async with self.lock:
            return list(self.memory[scope_level.value].keys())

    def _persist_entry(self, entry: ScopeEntry) -> None:
        """Save entry to database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                """
                INSERT OR REPLACE INTO scope_entries
                (key, value, scope_level, created_at, updated_at, ttl, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry.key,
                    json.dumps(entry.value),
                    entry.scope_level.value,
                    entry.created_at.isoformat(),
                    entry.updated_at.isoformat(),
                    entry.ttl,
                    json.dumps(entry.metadata),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error persisting scope entry: {e}")

    def _load_from_db(
        self, key: str, scope_level: ScopeLevel
    ) -> Optional[ScopeEntry]:
        """Load entry from database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute(
                """
                SELECT key, value, scope_level, created_at, updated_at, ttl, metadata
                FROM scope_entries
                WHERE key = ? AND scope_level = ?
            """,
                (key, scope_level.value),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return ScopeEntry(
                    key=row[0],
                    value=json.loads(row[1]),
                    scope_level=ScopeLevel(row[2]),
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                    ttl=row[5],
                    metadata=json.loads(row[6]),
                )
        except Exception as e:
            logger.error(f"Error loading from DB: {e}")

        return None

    def _delete_from_db(self, key: str, scope_level: ScopeLevel) -> None:
        """Delete entry from database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                "DELETE FROM scope_entries WHERE key = ? AND scope_level = ?",
                (key, scope_level.value),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error deleting from DB: {e}")

    def _clear_db_scope(self, scope_level: ScopeLevel) -> None:
        """Clear scope from database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                "DELETE FROM scope_entries WHERE scope_level = ?",
                (scope_level.value,),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error clearing DB scope: {e}")
