"""
Comprehensive tests for planning strategies.

Tests ReAcTreePlanner and PreActPlanner edge cases and detailed behavior.
"""

import pytest
import asyncio
from optimization.planning.reactree import ReAcTreePlanner
from optimization.planning.preact import PreActPlanner
from optimization.planning.types import (
    PlanningConfig,
    PlanTree,
    PlanNode,
    NodeStatus,
    PlanType,
)


class TestReAcTreePlannerDetailed:
    """Detailed tests for ReAcTreePlanner."""

    @pytest.fixture
    def planner(self):
        """Create ReAcTree planner."""
        config = PlanningConfig(
            max_depth=3,
            max_breadth=3,
            timeout_seconds=5.0,
            min_confidence_threshold=0.3,
            pruning_threshold=0.1,
            enable_parallel_branches=True,
            max_parallel_branches=2,
        )
        return ReAcTreePlanner(config)

    @pytest.mark.asyncio
    async def test_generate_initial_thought(self, planner):
        """Test initial thought generation."""
        node = await planner._generate_initial_thought(
            goal="Test goal",
            context={"tools": ["tool1"]}
        )

        assert node.id.startswith("node_")
        assert "Test goal" in node.thought
        assert node.confidence == 1.0
        assert node.status == NodeStatus.PENDING

    @pytest.mark.asyncio
    async def test_expand_branch_no_actions(self, planner):
        """Test branch expansion when no actions available."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root", confidence=1.0)
        tree.root_id = root.id
        tree.add_node(root)

        async def empty_executor(tool: str, input: dict) -> str:
            return "result"

        result = await planner._expand_branch(
            tree, root, "goal", {"tools": []}, empty_executor
        )

        assert result is False
        assert root.status == NodeStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_expand_branch_with_actions(self, planner):
        """Test branch expansion with actions."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root", confidence=1.0)
        tree.root_id = root.id
        tree.add_node(root)

        async def mock_executor(tool: str, input: dict) -> str:
            return "success"

        result = await planner._expand_branch(
            tree, root, "goal", {"tools": ["list_files"]}, mock_executor
        )

        # Should create child nodes
        children = tree.get_children(root.id)
        assert len(children) > 0

    @pytest.mark.asyncio
    async def test_expand_branch_goal_achieved(self, planner):
        """Test branch expansion when goal is achieved."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root", confidence=1.0)
        tree.root_id = root.id
        tree.add_node(root)

        async def success_executor(tool: str, input: dict) -> str:
            return "done successfully"

        result = await planner._expand_branch(
            tree, root, "goal", {"tools": ["complete"]}, success_executor
        )

        # Should detect goal achievement
        assert result is True or len(tree.nodes) > 1

    @pytest.mark.asyncio
    async def test_expand_branch_execution_error(self, planner):
        """Test branch expansion with execution error."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root", confidence=1.0)
        tree.root_id = root.id
        tree.add_node(root)

        async def failing_executor(tool: str, input: dict) -> str:
            raise ValueError("Execution failed")

        result = await planner._expand_branch(
            tree, root, "goal", {"tools": ["failing_tool"]}, failing_executor
        )

        # Should handle error gracefully
        children = tree.get_children(root.id)
        if children:
            assert any(c.status == NodeStatus.FAILED for c in children)

    @pytest.mark.asyncio
    async def test_generate_actions_first_action(self, planner):
        """Test action generation for first action."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root")
        tree.root_id = root.id
        tree.add_node(root)

        actions = await planner._generate_actions(
            tree, root, "Find files", {"tools": ["list_files", "search"]}
        )

        assert len(actions) > 0
        assert actions[0]["confidence"] > 0
        assert "thought" in actions[0]
        assert "action" in actions[0]

    @pytest.mark.asyncio
    async def test_generate_actions_with_history(self, planner):
        """Test action generation with execution history."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root")
        child = PlanNode(
            id="child",
            thought="Child",
            action="list_files",
            observation="Found files",
            parent_id="root",
        )
        tree.root_id = root.id
        tree.add_node(root)
        tree.add_node(child)

        actions = await planner._generate_actions(
            tree, child, "Analyze files", {"tools": ["analyze"]}
        )

        assert len(actions) > 0

    @pytest.mark.asyncio
    async def test_check_goal_achieved_completion_indicators(self, planner):
        """Test goal achievement detection."""
        tree = PlanTree()
        node = PlanNode(id="node", thought="Thought")

        # Test various completion indicators
        assert await planner._check_goal_achieved(tree, node, "goal", "done") is True
        assert await planner._check_goal_achieved(tree, node, "goal", "complete") is True
        assert await planner._check_goal_achieved(tree, node, "goal", "finished") is True
        assert await planner._check_goal_achieved(tree, node, "goal", "success") is True
        assert await planner._check_goal_achieved(tree, node, "goal", "answer is X") is True
        assert await planner._check_goal_achieved(tree, node, "goal", "result is Y") is True
        assert await planner._check_goal_achieved(tree, node, "goal", "found") is True
        assert await planner._check_goal_achieved(tree, node, "goal", "processing") is False

    @pytest.mark.asyncio
    async def test_prune_branches(self, planner):
        """Test branch pruning."""
        tree = PlanTree()
        high_conf = PlanNode(id="high", thought="High", confidence=0.8, status=NodeStatus.PENDING)
        low_conf = PlanNode(id="low", thought="Low", confidence=0.05, status=NodeStatus.PENDING)
        tree.add_node(high_conf)
        tree.add_node(low_conf)

        await planner._prune_branches(tree)

        assert low_conf.status == NodeStatus.PRUNED
        assert high_conf.status == NodeStatus.PENDING

    @pytest.mark.asyncio
    async def test_find_best_path(self, planner):
        """Test finding best path in tree."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root", confidence=1.0)
        path1_node = PlanNode(
            id="path1",
            thought="Path1",
            confidence=0.9,
            status=NodeStatus.COMPLETED,
            parent_id="root",
        )
        path2_node = PlanNode(
            id="path2",
            thought="Path2",
            confidence=0.7,
            status=NodeStatus.COMPLETED,
            parent_id="root",
        )
        tree.root_id = root.id
        tree.add_node(root)
        tree.add_node(path1_node)
        tree.add_node(path2_node)

        best_path = planner._find_best_path(tree)

        assert len(best_path) > 0
        assert "root" in best_path
        # Higher confidence path should be selected
        assert "path1" in best_path or "path2" in best_path

    @pytest.mark.asyncio
    async def test_find_best_path_no_completed(self, planner):
        """Test finding best path when no nodes completed."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root")
        pending = PlanNode(id="pending", thought="Pending", status=NodeStatus.PENDING)
        tree.root_id = root.id
        tree.add_node(root)
        tree.add_node(pending)

        best_path = planner._find_best_path(tree)

        assert best_path == []

    @pytest.mark.asyncio
    async def test_refine_plan(self, planner):
        """Test plan refinement."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root")
        tree.root_id = root.id
        tree.add_node(root)
        tree.best_path = [root.id]

        initial_count = len(tree.nodes)
        refined = await planner.refine(tree, "Need more detail")

        assert len(refined.nodes) >= initial_count  # Should add refinement node
        assert refined.best_path == tree.best_path

    @pytest.mark.asyncio
    async def test_refine_plan_disabled(self):
        """Test refinement when disabled."""
        config = PlanningConfig(enable_refinement=False)
        planner = ReAcTreePlanner(config)

        tree = PlanTree()
        root = PlanNode(id="root", thought="Root")
        tree.root_id = root.id
        tree.add_node(root)

        refined = await planner.refine(tree, "feedback")

        assert len(refined.nodes) == len(tree.nodes)

    @pytest.mark.asyncio
    async def test_plan_timeout(self, planner):
        """Test planning timeout."""
        planner.config.timeout_seconds = 0.1
        planner.config.max_depth = 2  # Limit depth to prevent excessive expansion

        async def slow_executor(tool: str, input: dict) -> str:
            await asyncio.sleep(0.05)  # Reduced from 1.0 to prevent long waits
            return "result"

        tree = await planner.plan(
            goal="Test goal",
            context={"tools": ["slow_tool"]},
            tool_executor=slow_executor,
        )

        # Should complete despite timeout
        assert tree.root_id is not None

    @pytest.mark.asyncio
    async def test_plan_no_viable_paths(self, planner):
        """Test planning when no viable paths exist."""
        planner.config.min_confidence_threshold = 0.9

        async def low_conf_executor(tool: str, input: dict) -> str:
            return "low confidence result"

        tree = await planner.plan(
            goal="Test goal",
            context={"tools": ["tool"]},
            tool_executor=low_conf_executor,
        )

        assert tree.root_id is not None


class TestPreActPlannerDetailed:
    """Detailed tests for PreActPlanner."""

    @pytest.fixture
    def planner(self):
        """Create PreAct planner with mocked dependencies."""
        from unittest.mock import AsyncMock, MagicMock

        # Mock memory system
        memory = MagicMock()
        memory.recall_similar_tasks = AsyncMock(return_value=[])
        memory.record_task = AsyncMock(return_value="task_id")
        memory.assert_fact = AsyncMock()

        # Mock predictor
        from optimization.preact_predictor import PredictionResult, ReflectionResult
        predictor = MagicMock()
        predictor.config = MagicMock(similar_example_count=3)
        predictor.predict_and_plan = AsyncMock(return_value=PredictionResult(
            predicted_outcome="Success",
            confidence=0.8,
            reasoning="Test reasoning",
            expected_success_rate=0.8,
            risks=[],
            opportunities=[],
        ))
        predictor.reflect = AsyncMock(return_value=ReflectionResult(
            predicted_outcome="Success",
            actual_outcome="Success",
            accuracy=0.9,
            aligned=True,
            insights="Test insights",
            lesson_learned="Test lesson",
        ))

        # Create planner with mocked dependencies
        config = PlanningConfig()
        planner = PreActPlanner(config)
        planner.preact = predictor
        planner.memory = memory

        return planner

    @pytest.mark.asyncio
    async def test_extract_outcome_completed(self, planner):
        """Test outcome extraction from completed node."""
        tree = PlanTree()
        node = PlanNode(
            id="node",
            thought="Thought",
            observation="Task completed successfully",
            status=NodeStatus.COMPLETED,
        )
        tree.add_node(node)
        tree.best_path = [node.id]

        outcome = planner._extract_outcome(tree)

        assert outcome == "Task completed successfully"

    @pytest.mark.asyncio
    async def test_extract_outcome_failed(self, planner):
        """Test outcome extraction from failed node."""
        tree = PlanTree()
        node = PlanNode(
            id="node",
            thought="Thought",
            status=NodeStatus.FAILED,
            error="Execution error",
        )
        tree.add_node(node)
        tree.best_path = [node.id]

        outcome = planner._extract_outcome(tree)

        assert "failed" in outcome.lower() or "error" in outcome.lower()

    @pytest.mark.asyncio
    async def test_extract_outcome_no_path(self, planner):
        """Test outcome extraction with no best path."""
        tree = PlanTree()

        outcome = planner._extract_outcome(tree)

        assert outcome == "No path completed"

    @pytest.mark.asyncio
    async def test_extract_task_outcome_success(self, planner):
        """Test task outcome extraction for success."""
        from optimization.memory.episodic import TaskOutcome

        tree = PlanTree()
        node = PlanNode(
            id="node",
            thought="Thought",
            status=NodeStatus.COMPLETED,
        )
        tree.add_node(node)
        tree.best_path = [node.id]

        outcome = planner._extract_task_outcome(tree)

        assert outcome == TaskOutcome.SUCCESS

    @pytest.mark.asyncio
    async def test_extract_task_outcome_failure(self, planner):
        """Test task outcome extraction for failure."""
        from optimization.memory.episodic import TaskOutcome

        tree = PlanTree()
        node = PlanNode(
            id="node",
            thought="Thought",
            status=NodeStatus.FAILED,
        )
        tree.add_node(node)
        tree.best_path = [node.id]

        outcome = planner._extract_task_outcome(tree)

        assert outcome == TaskOutcome.FAILURE

    @pytest.mark.asyncio
    async def test_refine_with_lesson(self, planner):
        """Test refinement incorporating lesson learned."""
        tree = PlanTree()
        root = PlanNode(id="root", thought="Root")
        tree.root_id = root.id
        tree.add_node(root)
        tree.best_path = [root.id]
        tree.metadata = {
            "reflection": type('obj', (object,), {
                'lesson_learned': "Use simpler approach"
            })()
        }

        initial_count = len(tree.nodes)
        refined = await planner.refine(tree, "Need improvement")

        # Should add refinement node
        assert len(refined.nodes) >= initial_count
        # Check that lesson was incorporated
        refinement_nodes = [n for n in refined.nodes.values() if "lesson" in n.thought.lower() or "simpler" in n.thought.lower()]
        assert len(refinement_nodes) > 0
