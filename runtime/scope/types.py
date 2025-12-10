"""Scope types for 11-level scope hierarchy."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ScopeLevel(str, Enum):
    """11-level scope hierarchy for variable persistence.

    Levels are ordered from most transient to most permanent:
    1. BLOCK - Single code block (most transient)
    2. ITERATION - Loop iteration
    3. TOOL_CALL - Single tool invocation
    4. PROMPT_CHAIN - Chain of prompts/conversation turn
    5. SESSION - User session (default for most operations)
    6. PHASE - Development phase (e.g., "planning", "implementation")
    7. PROJECT - Project-level scope
    8. WORKSPACE - Workspace-level scope
    9. ORGANIZATION - Organization-level scope
    10. GLOBAL - Global/shared scope
    11. PERMANENT - Permanent storage (most persistent)
    """

    BLOCK = "block"
    ITERATION = "iteration"
    TOOL_CALL = "tool_call"
    PROMPT_CHAIN = "prompt_chain"
    SESSION = "session"
    PHASE = "phase"
    PROJECT = "project"
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"
    GLOBAL = "global"
    PERMANENT = "permanent"

    @classmethod
    def from_string(cls, level: str) -> "ScopeLevel":
        """Convert string to ScopeLevel.

        Args:
            level: String representation of scope level

        Returns:
            ScopeLevel enum value

        Raises:
            ValueError: If level string is invalid
        """
        try:
            return cls(level.lower())
        except ValueError:
            raise ValueError(
                f"Invalid scope level: {level}. "
                f"Must be one of: {[e.value for e in cls]}"
            )

    def __lt__(self, other: "ScopeLevel") -> bool:
        """Compare scope levels (lower = more transient)."""
        order = [
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
        return order.index(self) < order.index(other)

    def __le__(self, other: "ScopeLevel") -> bool:
        """Compare scope levels."""
        return self == other or self < other

    def __gt__(self, other: "ScopeLevel") -> bool:
        """Compare scope levels."""
        return not self <= other

    def __ge__(self, other: "ScopeLevel") -> bool:
        """Compare scope levels."""
        return self == other or self > other


@dataclass
class ScopeKey:
    """Key for scope storage."""

    level: ScopeLevel
    key: str
    user_id: str
    workspace_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None

    def to_string(self) -> str:
        """Convert to storage key string."""
        parts = [self.level.value, self.user_id]
        if self.workspace_id:
            parts.append(f"ws:{self.workspace_id}")
        if self.project_id:
            parts.append(f"proj:{self.project_id}")
        if self.session_id:
            parts.append(f"sess:{self.session_id}")
        parts.append(self.key)
        return ":".join(parts)

    @classmethod
    def from_string(cls, key_string: str) -> "ScopeKey":
        """Parse storage key string."""
        # Implementation for parsing
        parts = key_string.split(":")
        # Simplified parsing - full implementation would handle all cases
        return cls(
            level=ScopeLevel(parts[0]),
            user_id=parts[1],
            key=parts[-1],
        )
