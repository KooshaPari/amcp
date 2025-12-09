"""PreAct planning strategy implementation."""

import logging
import time
from typing import Any, Optional, Callable, Awaitable

from .types import (
    PlanningConfig,
    PlanTree,
    NodeStatus,
)
from .reactree import ReAcTreePlanner
from ..preact_predictor import (
    PreActPredictor,
    PreActConfig,
    PredictionResult,
    get_preact_predictor,
)
from ..memory.integration import MemorySystem, MemoryConfig
from ..memory.episodic import TaskOutcome

logger = logging.getLogger(__name__)


class PreActPlanner(ReAcTreePlanner):
    """
    PreAct planning implementation extending ReAcTree.

    Adds prediction and reflection layers to ReAcTree:
    1. Prediction phase: Forecast outcomes before planning
    2. ReAcTree planning: Generate and execute plan tree
    3. Reflection phase: Compare predictions to actual outcomes

    Usage:
        planner = PreActPlanner(PlanningConfig())

        tree = await planner.plan(
            goal="Analyze the repository structure",
            context={"tools": ["list_files", "read_file"]},
            tool_executor=execute_tool
        )
    """

    def __init__(
        self,
        config: PlanningConfig = None,
        preact_config: PreActConfig = None,
        memory_system: Optional[MemorySystem] = None,
    ):
        super().__init__(config or PlanningConfig())
        self.preact = get_preact_predictor(preact_config or PreActConfig())
        self.memory = memory_system or MemorySystem(MemoryConfig())
        self._predictions: dict[str, PredictionResult] = {}

    async def plan(
        self,
        goal: str,
        context: dict[str, Any],
        tool_executor: Callable[[str, dict], Awaitable[Any]],
    ) -> PlanTree:
        """
        Execute PreAct-enhanced planning.

        Extends ReAcTree with prediction and reflection phases,
        integrating episodic memory for historical context.

        Args:
            goal: The goal to achieve
            context: Context including available tools
            tool_executor: Async function to execute tools

        Returns:
            PlanTree with execution history and prediction data
        """
        start_time = time.time()

        # Phase 0: Memory retrieval - Get similar historical examples
        logger.info(f"PreAct: Retrieving similar tasks from memory for goal: {goal[:100]}...")
        episodic_examples = await self.memory.recall_similar_tasks(
            goal=goal,
            limit=self.preact.config.similar_example_count
        )
        logger.debug(f"PreAct: Retrieved {len(episodic_examples)} similar examples from episodic memory")

        # Phase 1: Prediction - Forecast outcomes before planning
        logger.info(f"PreAct: Starting prediction phase for goal: {goal[:100]}...")
        prediction = await self.preact.predict_and_plan(
            goal=goal,
            context=context,
            episodic_examples=episodic_examples,
            tool_executor=tool_executor,
        )
        self._predictions[goal] = prediction

        logger.info(
            f"PreAct: Prediction confidence={prediction.confidence:.2f}, "
            f"risks={len(prediction.risks)}, "
            f"opportunities={len(prediction.opportunities)}"
        )

        # Phase 2: Planning - Execute ReAcTree planning with prediction context
        logger.info("PreAct: Starting ReAcTree planning phase...")
        tree = await super().plan(goal, context, tool_executor)

        # Phase 3: Reflection - Compare predictions to actual outcomes
        if tree.best_path and prediction:
            actual_outcome = self._extract_outcome(tree)
            logger.info(
                f"PreAct: Starting reflection phase... "
                f"Actual outcome: {actual_outcome[:100]}"
            )

            reflection = await self.preact.reflect(
                prediction=prediction,
                actual_outcome=actual_outcome,
            )

            logger.info(
                f"PreAct: Reflection complete - accuracy={reflection.accuracy:.2f}, "
                f"aligned={reflection.aligned}"
            )

            # Store reflection in tree for analysis
            tree.metadata = tree.metadata or {}
            tree.metadata["prediction"] = prediction
            tree.metadata["reflection"] = reflection

            # Phase 4: Memory update - Record task outcome and lessons learned
            task_outcome = self._extract_task_outcome(tree)
            logger.info(f"PreAct: Recording task outcome in episodic memory...")

            entry_id = await self.memory.record_task(
                goal=goal,
                context=context,
                tools_used=context.get("tools", []),
                outcome=task_outcome,
                result={"actual_outcome": actual_outcome},
                confidence=reflection.accuracy,
                duration=(time.time() - start_time),
                lesson_learned=reflection.lesson_learned,
            )

            logger.info(f"PreAct: Task recorded in episodic memory: {entry_id}")

            # Store any discovered facts in semantic memory
            if "discovered_facts" in tree.metadata:
                for fact in tree.metadata["discovered_facts"]:
                    await self.memory.assert_fact(
                        entity=fact.get("entity", ""),
                        property_name=fact.get("property", ""),
                        value=fact.get("value", ""),
                        confidence=fact.get("confidence", 0.8),
                        source="planning_execution"
                    )
                logger.debug(f"PreAct: Recorded {len(tree.metadata['discovered_facts'])} facts to semantic memory")

        duration = time.time() - start_time
        logger.info(f"PreAct planning complete in {duration:.2f}s")

        return tree

    def _extract_outcome(self, tree: PlanTree) -> str:
        """Extract final outcome from execution tree."""
        if not tree.best_path:
            return "No path completed"

        # Get last node in best path
        last_node_id = tree.best_path[-1]
        last_node = tree.get_node(last_node_id)

        if not last_node:
            return "Unknown outcome"

        if last_node.observation:
            return last_node.observation
        elif last_node.status == NodeStatus.COMPLETED:
            return "Goal achieved"
        elif last_node.status == NodeStatus.FAILED:
            return f"Goal failed: {last_node.error}"
        else:
            return "Goal not reached"

    def _extract_task_outcome(self, tree: PlanTree) -> TaskOutcome:
        """Extract task outcome enum from execution tree."""
        if not tree.best_path:
            return TaskOutcome.FAILURE

        # Get last node in best path
        last_node_id = tree.best_path[-1]
        last_node = tree.get_node(last_node_id)

        if not last_node:
            return TaskOutcome.FAILURE

        if last_node.status == NodeStatus.COMPLETED:
            return TaskOutcome.SUCCESS
        elif last_node.status == NodeStatus.FAILED:
            return TaskOutcome.FAILURE
        else:
            return TaskOutcome.PARTIAL  # Incomplete/partial completion

    async def refine(
        self,
        tree: PlanTree,
        feedback: str,
    ) -> PlanTree:
        """
        Refine plan based on feedback.

        Incorporates reflection insights into refinement.
        """
        # Get previous reflection if available
        metadata = getattr(tree, "metadata", {}) or {}
        reflection = metadata.get("reflection")

        if reflection and reflection.lesson_learned:
            logger.info(
                f"PreAct: Incorporating lesson learned: {reflection.lesson_learned}"
            )
            feedback = f"{feedback}\nLesson from prediction: {reflection.lesson_learned}"

        return await super().refine(tree, feedback)


# Global PreAct planner instance
_preact_planner: Optional[PreActPlanner] = None


def get_preact_planner(
    config: PlanningConfig = None,
    preact_config: PreActConfig = None,
    memory_system: Optional[MemorySystem] = None,
) -> PreActPlanner:
    """Get or create global PreAct planner instance."""
    global _preact_planner
    if _preact_planner is None:
        _preact_planner = PreActPlanner(
            config or PlanningConfig(),
            preact_config,
            memory_system
        )
    return _preact_planner
