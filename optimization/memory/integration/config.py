"""
Memory System Configuration

Configuration classes for the unified memory system.
"""

from dataclasses import dataclass, field

from ..episodic import EpisodicConfig
from ..semantic import SemanticConfig
from ..working import WorkingConfig


@dataclass
class MemoryConfig:
    """Configuration for unified memory system."""

    episodic_config: EpisodicConfig = field(default_factory=EpisodicConfig)
    semantic_config: SemanticConfig = field(default_factory=SemanticConfig)
    working_config: WorkingConfig = field(default_factory=WorkingConfig)

    # Global settings
    enable_forgetting: bool = True
    cleanup_interval_seconds: float = 3600.0  # 1 hour
    hybrid_forgetting: bool = True
