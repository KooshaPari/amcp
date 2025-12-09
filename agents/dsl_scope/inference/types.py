"""
Data structures for scope inference.

Contains core data models used throughout the inference system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any

from ..scope_levels import ScopeLevel


@dataclass
class InferenceSignal:
    """Single inference signal with confidence score."""
    scope_level: ScopeLevel
    key: str  # session_id, project_id, etc.
    value: str  # actual ID or name
    confidence: float  # 0.0-1.0
    evidence: str  # What caused this inference
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolCallAnalysis:
    """Analysis of a single tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    timestamp: datetime
    cwd_before: Optional[str] = None
    cwd_after: Optional[str] = None
    files_accessed: List[str] = field(default_factory=list)
    project_signals: List[str] = field(default_factory=list)
    phase_signals: List[str] = field(default_factory=list)


@dataclass
class ChatAnalysis:
    """Analysis of chat messages."""
    user_message: str
    assistant_message: str
    timestamp: datetime
    intent: Optional[str] = None  # planning, implementation, debugging, etc.
    project_mentions: List[str] = field(default_factory=list)
    directory_changes: List[str] = field(default_factory=list)
    files_mentioned: List[str] = field(default_factory=list)
