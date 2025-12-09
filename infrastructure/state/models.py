"""State models and types for state management."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class MemoryType(str, Enum):
    """Types of memory storage."""

    # Short-term working memory (cleared on session end)
    WORKING = "working"
    # Long-term persistent memory (persists across sessions)
    PERSISTENT = "persistent"
    # Context memory for conversation history
    CONTEXT = "context"
    # Variable storage for code execution
    VARIABLE = "variable"
    # File references and metadata
    FILE = "file"
    # Learning patterns and preferences
    LEARNING = "learning"


class MemoryItem(BaseModel):
    """A memory item with metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str = Field(..., description="Memory key")
    value: Any = Field(..., description="Memory value")
    memory_type: MemoryType = Field(default=MemoryType.WORKING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


@dataclass
class MemoryStats:
    """Statistics about memory usage."""

    total_items: int = 0
    working_items: int = 0
    persistent_items: int = 0
    context_items: int = 0
    variable_items: int = 0
    file_items: int = 0
    learning_items: int = 0
