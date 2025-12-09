"""Core data types for planning strategies."""

import time
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class NodeStatus(str, Enum):
    """Plan node execution status."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    PRUNED = "pruned"


class PlanType(str, Enum):
    """Planning strategy types."""
    REACT = "react"  # Standard ReAct
    REACTREE = "reactree"  # ReAcTree (recommended)
    PREACT = "preact"  # Preemptive ReAct
    TOT = "tot"  # Tree of Thoughts
    MCTS = "mcts"  # Monte Carlo Tree Search


@dataclass
class PlanningConfig:
    """Configuration for planning strategies."""

    # Strategy selection
    strategy: PlanType = PlanType.REACTREE
    enable_parallel_branches: bool = True
    max_parallel_branches: int = 3

    # Tree parameters
    max_depth: int = 5
    max_breadth: int = 4
    min_confidence_threshold: float = 0.3
    pruning_threshold: float = 0.1

    # Refinement
    enable_refinement: bool = True
    max_refinement_iterations: int = 2
    refinement_threshold: float = 0.7

    # Resource limits
    max_tokens_per_step: int = 4000
    max_total_tokens: int = 50000
    timeout_seconds: float = 120.0
    max_nodes: int = 1000  # Hard limit to prevent unbounded growth
    max_iterations: int = 500  # Maximum loop iterations as failsafe

    # Tool integration
    enable_tool_prediction: bool = True
    tool_confidence_threshold: float = 0.5


@dataclass
class PlanNode:
    """Single node in the plan tree."""

    id: str
    thought: str
    action: Optional[str] = None
    action_input: Optional[dict[str, Any]] = None
    observation: Optional[str] = None
    confidence: float = 1.0
    status: NodeStatus = NodeStatus.PENDING
    parent_id: Optional[str] = None
    children_ids: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error: Optional[str] = None

    # Metrics
    tokens_used: int = 0
    execution_time_ms: int = 0

    def mark_completed(self, observation: str) -> None:
        """Mark node as completed."""
        self.observation = observation
        self.status = NodeStatus.COMPLETED
        self.completed_at = time.time()
        self.execution_time_ms = int((self.completed_at - self.created_at) * 1000)

    def mark_failed(self, error: str) -> None:
        """Mark node as failed."""
        self.error = error
        self.status = NodeStatus.FAILED
        self.completed_at = time.time()

    def mark_pruned(self, reason: str) -> None:
        """Mark node as pruned."""
        self.status = NodeStatus.PRUNED
        self.error = f"Pruned: {reason}"


@dataclass
class PlanTree:
    """Tree structure for plan execution."""

    root_id: Optional[str] = None
    nodes: dict[str, PlanNode] = field(default_factory=dict)
    current_path: list[str] = field(default_factory=list)
    best_path: list[str] = field(default_factory=list)
    best_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: PlanNode) -> None:
        """Add node to tree."""
        self.nodes[node.id] = node
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            parent.children_ids.append(node.id)

    def get_node(self, node_id: str) -> Optional[PlanNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> list[PlanNode]:
        """Get children of a node."""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[cid] for cid in node.children_ids if cid in self.nodes]

    def get_path_to_root(self, node_id: str) -> list[PlanNode]:
        """Get path from node to root."""
        path = []
        current_id = node_id
        while current_id:
            node = self.nodes.get(current_id)
            if not node:
                break
            path.append(node)
            current_id = node.parent_id
        return list(reversed(path))

    def get_leaf_nodes(self) -> list[PlanNode]:
        """Get all leaf nodes."""
        return [
            node for node in self.nodes.values()
            if not node.children_ids and node.status != NodeStatus.PRUNED
        ]

    def get_depth(self, node_id: str) -> int:
        """Get depth of a node."""
        depth = 0
        current_id = node_id
        while current_id:
            node = self.nodes.get(current_id)
            if not node or not node.parent_id:
                break
            depth += 1
            current_id = node.parent_id
        return depth
