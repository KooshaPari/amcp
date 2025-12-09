"""ReAcTree planning strategy implementation."""

import asyncio
import logging
import time
from typing import Any, Optional, Callable, Awaitable
from abc import ABC, abstractmethod

from .types import (
    PlanningConfig,
    PlanNode,
    PlanTree,
    NodeStatus,
)

logger = logging.getLogger(__name__)


class PlanningStrategy(ABC):
    """Abstract base class for planning strategies."""

    def __init__(self, config: PlanningConfig):
        self.config = config

    @abstractmethod
    async def plan(
        self,
        goal: str,
        context: dict[str, Any],
        tool_executor: Callable[[str, dict], Awaitable[Any]],
    ) -> PlanTree:
        """Generate and execute a plan for the goal."""

    @abstractmethod
    async def refine(
        self,
        tree: PlanTree,
        feedback: str,
    ) -> PlanTree:
        """Refine plan based on feedback."""


class ReAcTreePlanner(PlanningStrategy):
    """
    ReAcTree planning implementation.

    Key innovations over ReAct:
    1. Tree-based exploration of action space
    2. Confidence scoring for branch selection
    3. Parallel evaluation of promising branches
    4. Dynamic pruning of low-confidence paths
    5. Preemptive action refinement

    Usage:
        planner = ReAcTreePlanner(PlanningConfig())

        tree = await planner.plan(
            goal="Analyze the repository structure",
            context={"tools": ["list_files", "read_file"]},
            tool_executor=execute_tool
        )

        # tree.best_path contains the successful execution path
    """

    def __init__(self, config: PlanningConfig = None):
        super().__init__(config or PlanningConfig())
        self._node_counter = 0
        self._lock = asyncio.Lock()

    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        self._node_counter += 1
        return f"node_{self._node_counter}"

    async def plan(
        self,
        goal: str,
        context: dict[str, Any],
        tool_executor: Callable[[str, dict], Awaitable[Any]],
    ) -> PlanTree:
        """
        Execute ReAcTree planning.

        Args:
            goal: The goal to achieve
            context: Context including available tools
            tool_executor: Async function to execute tools

        Returns:
            PlanTree with execution history
        """
        tree = PlanTree()
        start_time = time.time()

        # Create root node with initial thought
        root = await self._generate_initial_thought(goal, context)
        tree.root_id = root.id
        tree.add_node(root)
        tree.current_path = [root.id]

        logger.info(f"Starting ReAcTree planning for goal: {goal[:100]}...")

        try:
            iteration_count = 0  # Track iterations to prevent infinite loops
            
            # Main planning loop
            while True:
                iteration_count += 1
                
                # Hard iteration limit as failsafe
                if iteration_count > self.config.max_iterations:
                    logger.warning(f"Planning iteration limit reached ({self.config.max_iterations})")
                    break
                
                # Check node count limit
                if len(tree.nodes) > self.config.max_nodes:
                    logger.warning(f"Planning node limit reached ({self.config.max_nodes})")
                    break
                
                # Check timeout
                if time.time() - start_time > self.config.timeout_seconds:
                    logger.warning("Planning timeout reached")
                    break

                # Get current leaf nodes for expansion
                leaves = tree.get_leaf_nodes()
                if not leaves:
                    break

                # Filter leaves by confidence
                viable_leaves = [
                    leaf for leaf in leaves
                    if leaf.confidence >= self.config.min_confidence_threshold
                    and leaf.status == NodeStatus.PENDING
                    and tree.get_depth(leaf.id) < self.config.max_depth
                ]

                if not viable_leaves:
                    # No more viable paths
                    break

                # Select branches for parallel exploration
                branches_to_expand = sorted(
                    viable_leaves,
                    key=lambda n: n.confidence,
                    reverse=True
                )[:self.config.max_parallel_branches]

                # Expand branches
                if self.config.enable_parallel_branches:
                    results = await asyncio.gather(*[
                        self._expand_branch(tree, leaf, goal, context, tool_executor)
                        for leaf in branches_to_expand
                    ], return_exceptions=True)
                else:
                    results = []
                    for leaf in branches_to_expand:
                        result = await self._expand_branch(
                            tree, leaf, goal, context, tool_executor
                        )
                        results.append(result)

                # Check for goal completion
                for result in results:
                    if isinstance(result, bool) and result:
                        logger.info("Goal achieved!")
                        return tree

                # Prune low-confidence branches
                await self._prune_branches(tree)

        except Exception as e:
            logger.error(f"Planning error: {e}")
            raise

        # Find best path
        tree.best_path = self._find_best_path(tree)

        logger.info(
            f"Planning complete: {len(tree.nodes)} nodes, "
            f"best path length: {len(tree.best_path)}"
        )

        return tree

    async def _generate_initial_thought(
        self,
        goal: str,
        context: dict[str, Any],
    ) -> PlanNode:
        """Generate initial thought/plan decomposition."""
        node = PlanNode(
            id=self._generate_node_id(),
            thought=f"Goal: {goal}. I need to break this down into steps.",
            confidence=1.0,
            status=NodeStatus.PENDING,
        )
        return node

    async def _expand_branch(
        self,
        tree: PlanTree,
        node: PlanNode,
        goal: str,
        context: dict[str, Any],
        tool_executor: Callable[[str, dict], Awaitable[Any]],
    ) -> bool:
        """
        Expand a branch by generating and executing next actions.

        Returns True if goal is achieved.
        """
        node.status = NodeStatus.EXECUTING

        try:
            # Generate possible next actions
            actions = await self._generate_actions(tree, node, goal, context)

            if not actions:
                node.mark_completed("No actions available")
                return False

            # Execute top action (check node limit first)
            if len(tree.nodes) >= self.config.max_nodes:
                logger.warning(f"Node limit reached ({self.config.max_nodes}), cannot expand branch")
                node.mark_completed("Node limit reached")
                return False
                
            top_action = actions[0]
            child_node = PlanNode(
                id=self._generate_node_id(),
                thought=top_action["thought"],
                action=top_action["action"],
                action_input=top_action["input"],
                confidence=top_action["confidence"],
                parent_id=node.id,
            )
            tree.add_node(child_node)

            # Execute the action
            if child_node.action:
                try:
                    result = await tool_executor(
                        child_node.action,
                        child_node.action_input or {}
                    )
                    child_node.mark_completed(str(result))

                    # Check if goal achieved
                    if await self._check_goal_achieved(
                        tree, child_node, goal, str(result)
                    ):
                        return True

                except Exception as e:
                    child_node.mark_failed(str(e))

            # Create alternative branches for other actions (with node limit check)
            for alt_action in actions[1:self.config.max_breadth]:
                # Check node limit before adding
                if len(tree.nodes) >= self.config.max_nodes:
                    logger.warning(f"Node limit reached ({self.config.max_nodes}), skipping alternative branches")
                    break
                    
                alt_node = PlanNode(
                    id=self._generate_node_id(),
                    thought=alt_action["thought"],
                    action=alt_action["action"],
                    action_input=alt_action["input"],
                    confidence=alt_action["confidence"] * 0.9,  # Slight penalty
                    parent_id=node.id,
                )
                tree.add_node(alt_node)

            node.mark_completed("Branch expanded")
            return False

        except Exception as e:
            node.mark_failed(str(e))
            return False

    async def _generate_actions(
        self,
        tree: PlanTree,
        node: PlanNode,
        goal: str,
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Generate possible next actions based on current state.

        This would typically call an LLM - simplified here.
        """
        # Get execution history
        path = tree.get_path_to_root(node.id)
        history = [
            {
                "thought": n.thought,
                "action": n.action,
                "observation": n.observation,
            }
            for n in path
        ]

        # Get available tools
        tools = context.get("tools", [])

        # Generate action candidates
        actions = []

        # Example heuristic-based action generation
        if not history or len(history) == 1:
            # First action: typically explore/gather info
            if "list_files" in tools or "search" in tools:
                actions.append({
                    "thought": "I should first understand the structure/context",
                    "action": "list_files" if "list_files" in tools else "search",
                    "input": {"path": "."} if "list_files" in tools else {"query": goal},
                    "confidence": 0.9,
                })

        if "analyze" in str(tools):
            actions.append({
                "thought": "I should analyze the available information",
                "action": "analyze",
                "input": {"target": goal},
                "confidence": 0.8,
            })

        # Default action if no specific tools
        if not actions:
            actions.append({
                "thought": "I need to process the goal step by step",
                "action": tools[0] if tools else "think",
                "input": {"query": goal},
                "confidence": 0.7,
            })

        return actions

    async def _check_goal_achieved(
        self,
        tree: PlanTree,
        node: PlanNode,
        goal: str,
        observation: str,
    ) -> bool:
        """Check if the goal has been achieved."""
        # Simplified check - in production, use LLM evaluation
        completion_indicators = [
            "done", "complete", "finished", "success",
            "answer is", "result is", "found"
        ]

        obs_lower = observation.lower()
        return any(ind in obs_lower for ind in completion_indicators)

    async def _prune_branches(self, tree: PlanTree) -> None:
        """Prune low-confidence branches."""
        for node in tree.nodes.values():
            if (
                node.status == NodeStatus.PENDING
                and node.confidence < self.config.pruning_threshold
            ):
                node.mark_pruned("Below confidence threshold")

    def _find_best_path(self, tree: PlanTree) -> list[str]:
        """Find the best execution path in the tree."""
        completed_leaves = [
            node for node in tree.get_leaf_nodes()
            if node.status == NodeStatus.COMPLETED
        ]

        if not completed_leaves:
            return []

        # Score paths by cumulative confidence
        best_leaf = max(
            completed_leaves,
            key=lambda n: sum(
                p.confidence for p in tree.get_path_to_root(n.id)
            )
        )

        path = tree.get_path_to_root(best_leaf.id)
        return [n.id for n in path]

    async def refine(
        self,
        tree: PlanTree,
        feedback: str,
    ) -> PlanTree:
        """Refine plan based on feedback."""
        if not self.config.enable_refinement:
            return tree

        # Add refinement node (check node limit)
        if len(tree.nodes) >= self.config.max_nodes:
            logger.warning(f"Node limit reached ({self.config.max_nodes}), cannot add refinement node")
            return tree
            
        refinement_node = PlanNode(
            id=self._generate_node_id(),
            thought=f"Refinement based on feedback: {feedback}",
            confidence=0.8,
            parent_id=tree.best_path[-1] if tree.best_path else tree.root_id,
        )
        tree.add_node(refinement_node)

        logger.info(f"Plan refined with feedback: {feedback[:100]}...")

        return tree


# Global planner instance
_reactree_planner: Optional[ReAcTreePlanner] = None


def get_reactree_planner(config: PlanningConfig = None) -> ReAcTreePlanner:
    """Get or create global ReAcTree planner instance."""
    global _reactree_planner
    if _reactree_planner is None:
        _reactree_planner = ReAcTreePlanner(config or PlanningConfig())
    return _reactree_planner
