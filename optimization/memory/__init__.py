"""
Memory Systems for SmartCP Optimization

Implements three types of memory for intelligent agents:
1. Episodic Memory - Task history and past experiences
2. Semantic Memory - Facts, relationships, and general knowledge
3. Working Memory - Current context and active information

Forgetting mechanisms:
- LRU (Least Recently Used) eviction for capacity limits
- Temporal decay for confidence degradation
- Relevance-based pruning for irrelevant information

Reference: 2025 Cognitive Science & AI Memory Research
"""

from .episodic import (
    EpisodicMemory,
    EpisodicEntry,
    EpisodicConfig,
    TaskOutcome,
)
from .semantic import (
    SemanticMemory,
    SemanticEntry,
    SemanticRelation,
    SemanticConfig,
    RelationType,
)
from .working import (
    WorkingMemory,
    WorkingContext,
    WorkingConfig,
)
from .forgetting import (
    ForgetMechanism,
    LRUEviction,
    TemporalDecay,
    RelevancePruning,
)
from .integration.system import MemorySystem
from .integration.config import MemoryConfig
from .integration.stats import MemoryStats
from .integration.cleanup import MemoryCleanup
from .integration.operations import MemoryOperations

__all__ = [
    # Episodic
    "EpisodicMemory",
    "EpisodicEntry",
    "EpisodicConfig",
    "TaskOutcome",
    # Semantic
    "SemanticMemory",
    "SemanticEntry",
    "SemanticRelation",
    "SemanticConfig",
    "RelationType",
    # Working
    "WorkingMemory",
    "WorkingContext",
    "WorkingConfig",
    # Forgetting
    "ForgetMechanism",
    "LRUEviction",
    "TemporalDecay",
    "RelevancePruning",
    # Integration
    "MemorySystem",
    "MemoryConfig",
    "MemoryStats",
    "MemoryCleanup",
    "MemoryOperations",
]
