"""
Scope level definitions and hierarchy management.

Defines the 6-level scope hierarchy and provides utilities for
scope validation and navigation.
"""

from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


class ScopeLevel(Enum):
    """Scope hierarchy levels (most specific to most general)."""
    BLOCK = "block"                    # Function/block-local
    ITERATION = "iteration"            # Single iteration within a task
    TOOL_CALL = "tool_call"           # Single tool invocation
    PROMPT_CHAIN = "prompt_chain"     # Multi-turn conversation
    SESSION = "session"                # Entire CLI session
    PHASE = "phase"                    # Session phase (plan/docwrite/impl)
    PROJECT = "project"                # Inferred project context
    WORKSPACE = "workspace"            # Workspace scope
    ORGANIZATION = "organization"      # Organization scope
    GLOBAL = "global"                  # Cross-session shared
    PERMANENT = "permanent"            # Forever-persisted


@dataclass
class ScopeEntry:
    """Single scope entry with metadata."""
    key: str
    value: Any
    scope_level: ScopeLevel
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None          # Time-to-live in seconds
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL."""
        if self.ttl is None:
            return False

        elapsed = (datetime.now() - self.updated_at).total_seconds()
        return elapsed > self.ttl

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "key": self.key,
            "value": self.value,
            "scope_level": self.scope_level.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "ttl": self.ttl,
            "metadata": self.metadata,
        }


class ScopeHierarchy:
    """Scope hierarchy validator and navigator."""

    # Scope precedence (higher index = more general, lower = more specific)
    HIERARCHY = [
        ScopeLevel.BLOCK,
        ScopeLevel.ITERATION,
        ScopeLevel.TOOL_CALL,
        ScopeLevel.PROMPT_CHAIN,
        ScopeLevel.SESSION,
        ScopeLevel.PHASE,
        ScopeLevel.PROJECT,
        ScopeLevel.WORKSPACE,
        ScopeLevel.ORGANIZATION,
        ScopeLevel.GLOBAL,
        ScopeLevel.PERMANENT,
    ]

    @classmethod
    def is_parent(cls, parent: ScopeLevel, child: ScopeLevel) -> bool:
        """Check if parent scope is ancestor of child."""
        parent_idx = cls.HIERARCHY.index(parent)
        child_idx = cls.HIERARCHY.index(child)
        return parent_idx > child_idx

    @classmethod
    def get_scope_chain(cls, scope: ScopeLevel) -> list[ScopeLevel]:
        """Get all scopes from most specific to this scope (inclusive)."""
        idx = cls.HIERARCHY.index(scope)
        return cls.HIERARCHY[:idx + 1]

    @classmethod
    def get_parent_scopes(cls, scope: ScopeLevel) -> list[ScopeLevel]:
        """Get parent scopes (from current to most general)."""
        idx = cls.HIERARCHY.index(scope)
        return cls.HIERARCHY[idx:]

    @classmethod
    def inherit_scope(cls, child: ScopeLevel, parent: ScopeLevel) -> bool:
        """Validate inheritance relationship (child can access parent)."""
        return cls.is_parent(parent, child)

    @classmethod
    def get_persistence_backend(cls, scope: ScopeLevel) -> str:
        """Determine storage backend for scope."""
        if scope in (ScopeLevel.BLOCK, ScopeLevel.ITERATION, ScopeLevel.TOOL_CALL):
            return "memory"
        elif scope in (ScopeLevel.PROMPT_CHAIN, ScopeLevel.SESSION, ScopeLevel.PHASE):
            return "redis"
        elif scope in (ScopeLevel.PROJECT, ScopeLevel.WORKSPACE, ScopeLevel.ORGANIZATION):
            return "database"
        else:  # GLOBAL, PERMANENT
            return "database"
