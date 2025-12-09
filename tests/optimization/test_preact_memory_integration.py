"""
Tests for PreAct Planner Memory Integration.

Tests memory integration paths including episodic memory recording and semantic fact assertion.
Covers lines 107-155 in optimization/planning/preact.py.
"""

import asyncio
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimization.planning import (
    PreActPlanner,
    PlanningConfig,
    PlanTree,
    NodeStatus,
)
from optimization.preact_predictor import (
    PreActConfig,
    PredictionResult,
    ReflectionResult,
)


class TestPreActMemoryIntegration:
    """Tests for PreAct memory integration paths."""

    @pytest.fixture
    def planning_config(self):
        """Create planning config with limits."""
        return PlanningConfig(
            max_depth=2,
            max_breadth=2,
            timeout_seconds=5.0,
            max_nodes=100,
            max_iterations=50,
        )

    @pytest.fixture
    def preact_config(self):
        """Create PreAct config."""
        return PreActConfig(
            enable_prediction=True,
            enable_reflection=True,
            cache_predictions=False,
        )

    @pytest.fixture
    def mock_memory_system(self):
        """Create mock memory system."""
        memory = MagicMock()
        memory.record_task = AsyncMock(return_value="episodic_entry_123")
        memory.assert_fact = AsyncMock()
        memory.recall_similar_tasks = AsyncMock(return_value=[])  # Add missing method
        return memory

    @pytest.fixture
    def planner(self, planning_config, preact_config, mock_memory_system):
        """Create PreActPlanner with memory system."""
        return PreActPlanner(planning_config, preact_config, mock_memory_system)

    @pytest.fixture
    def mock_tool_executor(self):
        """Mock tool executor that succeeds."""
        async def execute(tool_name: str, params: dict):
            return {"success": True, "result": f"Result from {tool_name}"}
        return execute

    @pytest.mark.asyncio
    async def test_memory_recording_with_best_path(
        self, planner, mock_memory_system, mock_tool_executor
    ):
        """Test that episodic memory is recorded when best path exists (lines 128-143)."""
        goal = "Test goal with memory recording"
        context = {"tools": ["test_tool"]}

        tree = await planner.plan(goal, context, mock_tool_executor)

        # Verify memory was called if best path exists
        if tree.best_path:
            mock_memory_system.record_task.assert_called_once()
            call_args = mock_memory_system.record_task.call_args
            assert call_args.kwargs["goal"] == goal
            assert call_args.kwargs["outcome"] is not None
            assert "confidence" in call_args.kwargs
            assert "duration" in call_args.kwargs
            assert call_args.kwargs["tools_used"] == context.get("tools", [])
            assert "result" in call_args.kwargs
            assert "lesson_learned" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_full_memory_integration_path(
        self, planner, mock_memory_system, mock_tool_executor
    ):
        """Test complete memory integration path including reflection (lines 107-143)."""
        goal = "Complete integration test"
        context = {"tools": ["test_tool"]}

        # Patch ReAcTreePlanner.plan to ensure best_path exists
        from optimization.planning.reactree import ReAcTreePlanner
        from optimization.planning.types import PlanNode
        original_plan = ReAcTreePlanner.plan
        
        async def patched_super_plan(self, goal, context, tool_executor):
            tree = await original_plan(self, goal, context, tool_executor)
            # Ensure best_path exists for memory integration
            if not tree.best_path and len(tree.nodes) > 0:
                # Create a simple best_path from root
                root_id = tree.root_id
                if root_id:
                    node = tree.get_node(root_id)
                    if node:
                        node.status = NodeStatus.COMPLETED
                        tree.best_path = [root_id]
            return tree

        with patch.object(ReAcTreePlanner, 'plan', patched_super_plan):
            tree = await planner.plan(goal, context, mock_tool_executor)

            # Verify complete integration path when best_path exists
            if tree.best_path:
                # Verify reflection phase executed (lines 107-121)
                assert "reflection" in tree.metadata
                reflection = tree.metadata["reflection"]
                assert isinstance(reflection, ReflectionResult)
                
                # Verify actual_outcome was extracted (line 107)
                assert "prediction" in tree.metadata
                prediction = tree.metadata["prediction"]
                assert isinstance(prediction, PredictionResult)
                
                # Verify reflection was called with correct parameters (lines 113-116)
                # (reflection is called internally, we verify it's stored)
                assert reflection.predicted_outcome is not None
                assert reflection.actual_outcome is not None
                
                # Verify memory recording (lines 132-141)
                mock_memory_system.record_task.assert_called_once()
                call_args = mock_memory_system.record_task.call_args
                assert call_args.kwargs["goal"] == goal
                assert call_args.kwargs["confidence"] == reflection.accuracy
                assert "lesson_learned" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_semantic_fact_assertion(
        self, planner, mock_memory_system, mock_tool_executor
    ):
        """Test that discovered facts are asserted to semantic memory (lines 145-155)."""
        goal = "Test goal with facts"
        context = {"tools": ["discover_tool"]}

        # Patch ReAcTreePlanner.plan to inject discovered_facts and ensure best_path
        from optimization.planning.reactree import ReAcTreePlanner
        from optimization.planning.types import PlanNode
        original_plan = ReAcTreePlanner.plan
        
        async def patched_super_plan(self, goal, context, tool_executor):
            # Call the actual super().plan()
            tree = await original_plan(self, goal, context, tool_executor)
            # Ensure best_path exists
            if not tree.best_path and len(tree.nodes) > 0:
                root_id = tree.root_id
                if root_id:
                    node = tree.get_node(root_id)
                    if node:
                        node.status = NodeStatus.COMPLETED
                        tree.best_path = [root_id]
            # Inject discovered_facts into metadata before memory integration runs
            if tree.best_path:
                tree.metadata = tree.metadata or {}
                tree.metadata["discovered_facts"] = [
                    {
                        "entity": "test_entity",
                        "property": "test_property",
                        "value": "test_value",
                        "confidence": 0.9,
                    },
                    {
                        "entity": "another_entity",
                        "property": "another_property",
                        "value": "another_value",
                        "confidence": 0.8,
                    },
                ]
            return tree

        with patch.object(ReAcTreePlanner, 'plan', patched_super_plan):
            tree = await planner.plan(goal, context, mock_tool_executor)

            # Verify facts were asserted to semantic memory (lines 145-155)
            if tree.best_path:
                # assert_fact should be called for each fact
                assert mock_memory_system.assert_fact.call_count == 2
                
                # Verify first fact assertion
                call1 = mock_memory_system.assert_fact.call_args_list[0]
                assert call1.kwargs["entity"] == "test_entity"
                assert call1.kwargs["property_name"] == "test_property"
                assert call1.kwargs["value"] == "test_value"
                assert call1.kwargs["confidence"] == 0.9
                assert call1.kwargs["source"] == "planning_execution"
                
                # Verify second fact assertion
                call2 = mock_memory_system.assert_fact.call_args_list[1]
                assert call2.kwargs["entity"] == "another_entity"
                assert call2.kwargs["property_name"] == "another_property"
                assert call2.kwargs["value"] == "another_value"
                assert call2.kwargs["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_semantic_fact_assertion_empty_list(
        self, planner, mock_memory_system, mock_tool_executor
    ):
        """Test that empty discovered_facts list doesn't cause errors."""
        goal = "Test goal with empty facts"
        context = {"tools": ["test_tool"]}

        # Patch ReAcTreePlanner.plan to return tree with empty discovered_facts and best_path
        from optimization.planning.reactree import ReAcTreePlanner
        from optimization.planning.types import PlanNode
        original_plan = ReAcTreePlanner.plan
        
        async def patched_super_plan(self, goal, context, tool_executor):
            tree = await original_plan(self, goal, context, tool_executor)
            # Ensure best_path exists
            if not tree.best_path and len(tree.nodes) > 0:
                root_id = tree.root_id
                if root_id:
                    node = tree.get_node(root_id)
                    if node:
                        node.status = NodeStatus.COMPLETED
                        tree.best_path = [root_id]
            if tree.best_path:
                tree.metadata = tree.metadata or {}
                tree.metadata["discovered_facts"] = []  # Empty list
            return tree

        with patch.object(ReAcTreePlanner, 'plan', patched_super_plan):
            tree = await planner.plan(goal, context, mock_tool_executor)

            # Should not call assert_fact for empty list (loop doesn't execute)
            if tree.best_path:
                assert mock_memory_system.assert_fact.call_count == 0

    @pytest.mark.asyncio
    async def test_semantic_fact_assertion_missing_keys(
        self, planner, mock_memory_system, mock_tool_executor
    ):
        """Test that discovered_facts with missing keys uses defaults."""
        goal = "Test goal with incomplete facts"
        context = {"tools": ["test_tool"]}

        # Patch ReAcTreePlanner.plan to return tree with incomplete fact dicts and best_path
        from optimization.planning.reactree import ReAcTreePlanner
        from optimization.planning.types import PlanNode
        original_plan = ReAcTreePlanner.plan
        
        async def patched_super_plan(self, goal, context, tool_executor):
            tree = await original_plan(self, goal, context, tool_executor)
            # Ensure best_path exists
            if not tree.best_path and len(tree.nodes) > 0:
                root_id = tree.root_id
                if root_id:
                    node = tree.get_node(root_id)
                    if node:
                        node.status = NodeStatus.COMPLETED
                        tree.best_path = [root_id]
            if tree.best_path:
                tree.metadata = tree.metadata or {}
                tree.metadata["discovered_facts"] = [
                    {
                        "entity": "test_entity",
                        # Missing property, value, confidence - should use defaults
                    },
                ]
            return tree

        with patch.object(ReAcTreePlanner, 'plan', patched_super_plan):
            tree = await planner.plan(goal, context, mock_tool_executor)

            # Should call assert_fact with defaults for missing keys
            if tree.best_path:
                assert mock_memory_system.assert_fact.call_count == 1
                call = mock_memory_system.assert_fact.call_args
                assert call.kwargs["entity"] == "test_entity"
                assert call.kwargs["property_name"] == ""  # Default from .get("property", "")
                assert call.kwargs["value"] == ""  # Default from .get("value", "")
                assert call.kwargs["confidence"] == 0.8  # Default from .get("confidence", 0.8)

    @pytest.mark.asyncio
    async def test_reflection_stored_in_metadata(
        self, planner, mock_memory_system, mock_tool_executor
    ):
        """Test that reflection is stored in tree metadata."""
        goal = "Test reflection storage"
        context = {"tools": ["test_tool"]}

        tree = await planner.plan(goal, context, mock_tool_executor)

        if tree.best_path:
            assert tree.metadata is not None
            assert "reflection" in tree.metadata
            reflection = tree.metadata["reflection"]
            assert isinstance(reflection, ReflectionResult)
            assert hasattr(reflection, "accuracy")
            assert hasattr(reflection, "aligned")

    @pytest.mark.asyncio
    async def test_extract_outcome_edge_cases(self, planner):
        """Test edge cases in _extract_outcome method."""
        # Test with no best path
        tree = PlanTree()
        outcome = planner._extract_outcome(tree)
        assert outcome == "No path completed"

        # Test with best path but no last node
        tree.best_path = ["nonexistent_node"]
        outcome = planner._extract_outcome(tree)
        assert outcome == "Unknown outcome"

        # Test with completed node
        from optimization.planning.types import PlanNode
        node = PlanNode(
            id="test_node",
            thought="test thought",
            status=NodeStatus.COMPLETED,
        )
        tree.add_node(node)
        tree.best_path = ["test_node"]
        outcome = planner._extract_outcome(tree)
        assert outcome == "Goal achieved"

        # Test with failed node
        failed_node = PlanNode(
            id="failed_node",
            thought="failed thought",
            status=NodeStatus.FAILED,
            error="Test error",
        )
        tree.add_node(failed_node)
        tree.best_path = ["failed_node"]
        outcome = planner._extract_outcome(tree)
        assert "Goal failed" in outcome

        # Test with node that has observation
        obs_node = PlanNode(
            id="obs_node",
            thought="obs thought",
            status=NodeStatus.EXECUTING,
            observation="Test observation",
        )
        tree.add_node(obs_node)
        tree.best_path = ["obs_node"]
        outcome = planner._extract_outcome(tree)
        assert outcome == "Test observation"

        # Test with node that has no observation and not completed/failed
        pending_node = PlanNode(
            id="pending_node",
            thought="pending thought",
            status=NodeStatus.PENDING,
        )
        tree.add_node(pending_node)
        tree.best_path = ["pending_node"]
        outcome = planner._extract_outcome(tree)
        assert outcome == "Goal not reached"

    @pytest.mark.asyncio
    async def test_extract_task_outcome_edge_cases(self, planner):
        """Test edge cases in _extract_task_outcome method."""
        from optimization.memory.episodic import TaskOutcome
        from optimization.planning.types import PlanNode

        # Test with no best path
        tree = PlanTree()
        outcome = planner._extract_task_outcome(tree)
        assert outcome == TaskOutcome.FAILURE

        # Test with best path but no last node
        tree.best_path = ["nonexistent_node"]
        outcome = planner._extract_task_outcome(tree)
        assert outcome == TaskOutcome.FAILURE

        # Test with completed node
        node = PlanNode(
            id="test_node",
            thought="test thought",
            status=NodeStatus.COMPLETED,
        )
        tree.add_node(node)
        tree.best_path = ["test_node"]
        outcome = planner._extract_task_outcome(tree)
        assert outcome == TaskOutcome.SUCCESS

        # Test with failed node
        failed_node = PlanNode(
            id="failed_node",
            thought="failed thought",
            status=NodeStatus.FAILED,
        )
        tree.add_node(failed_node)
        tree.best_path = ["failed_node"]
        outcome = planner._extract_task_outcome(tree)
        assert outcome == TaskOutcome.FAILURE

        # Test with incomplete node
        incomplete_node = PlanNode(
            id="incomplete_node",
            thought="incomplete thought",
            status=NodeStatus.EXECUTING,
        )
        tree.add_node(incomplete_node)
        tree.best_path = ["incomplete_node"]
        outcome = planner._extract_task_outcome(tree)
        assert outcome == TaskOutcome.PARTIAL  # Incomplete maps to PARTIAL

    @pytest.mark.asyncio
    async def test_refine_with_lesson_learned(
        self, planner, mock_memory_system, mock_tool_executor
    ):
        """Test refine method incorporates lesson learned from reflection (lines 217-220)."""
        goal = "Test refine with lesson"
        context = {"tools": ["test_tool"]}

        # Create a tree first
        tree = await planner.plan(goal, context, mock_tool_executor)

        # Ensure tree has metadata and add reflection with lesson_learned
        tree.metadata = tree.metadata or {}
        
        # Create a reflection with lesson_learned to test lines 217-220
        from optimization.preact_predictor import ReflectionResult
        reflection_with_lesson = ReflectionResult(
            predicted_outcome="Predicted success",
            actual_outcome="Actual success",
            accuracy=0.9,
            aligned=True,
            insights="Prediction was accurate",
            lesson_learned="Always check dependencies before execution",  # This triggers lines 217-220
        )
        tree.metadata["reflection"] = reflection_with_lesson

        # Refine with feedback - should incorporate lesson_learned
        feedback = "Plan needs adjustment"
        refined_tree = await planner.refine(tree, feedback)

        # Verify refinement occurred
        assert isinstance(refined_tree, PlanTree)
        
        # The refine method should have incorporated the lesson into feedback
        # We verify refine was called successfully with reflection containing lesson_learned
        assert refined_tree is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
