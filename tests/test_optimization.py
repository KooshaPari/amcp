"""
SmartCP Optimization Tests - Legacy Entry Point

This file provides backward compatibility for test discovery.
All tests have been decomposed into the optimization/ module:

- tests/optimization/test_prompt_cache.py
- tests/optimization/test_model_router.py
- tests/optimization/test_planning.py
- tests/optimization/test_context_compression.py
- tests/optimization/test_parallel_executor.py
- tests/optimization/test_integration_pipeline.py
- tests/optimization/test_preact_predictor.py
- tests/optimization/test_preact_planner.py
- tests/optimization/test_preact_integration.py

Run tests using:
    pytest tests/optimization/
    pytest tests/optimization/test_prompt_cache.py
    pytest tests/optimization/ -m performance

This file re-exports all test classes for backward compatibility.
It will be removed in a future version.
"""

# Re-export all test classes from decomposed modules
# NOTE: This file is deprecated. All tests have been moved to tests/optimization/
# These imports are commented out to prevent import errors.
# Import test classes directly from tests/optimization/ modules instead.
# 
# from tests.optimization.test_prompt_cache import (
#     TestPromptCache,
#     TestPromptCachePerformance,
# )
# from tests.optimization.test_model_router import (
#     TestComplexityRouter,
#     TestComplexityAnalyzer,
# )
# from tests.optimization.test_planning import (
#     TestReAcTreePlanner,
# )
# from tests.optimization.test_context_compression import (
#     TestACONCompressor,
# )
# from tests.optimization.test_parallel_executor import (
#     TestParallelToolExecutor,
#     TestDependencyAnalyzer,
#     TestParallelExecutorPerformance,
# )
# from tests.optimization.test_integration_pipeline import (
#     TestOptimizationPipeline,
# )
# from tests.optimization.test_preact_predictor import (
#     TestPredictionResult,
#     TestReflectionResult,
#     TestPreActPredictor,
# )
# from tests.optimization.test_preact_planner import (
#     TestPreActPlanner,
# )
# from tests.optimization.test_preact_integration import (
#     TestPreActIntegration,
# )

# __all__ is commented out since imports are disabled
# __all__ = [
#     # Prompt Cache
#     "TestPromptCache",
#     "TestPromptCachePerformance",
#     # Model Router
#     "TestComplexityRouter",
#     "TestComplexityAnalyzer",
#     # Planning
#     "TestReAcTreePlanner",
#     # Context Compression
#     "TestACONCompressor",
#     # Parallel Executor
#     "TestParallelToolExecutor",
#     "TestDependencyAnalyzer",
#     "TestParallelExecutorPerformance",
#     # Integration Pipeline
#     "TestOptimizationPipeline",
#     # PreAct Predictor
#     "TestPredictionResult",
#     "TestReflectionResult",
#     "TestPreActPredictor",
#     # PreAct Planner
#     "TestPreActPlanner",
#     # PreAct Integration
#     "TestPreActIntegration",
# ]


# NOTE: This backward compatibility layer will be removed in future versions.
# Please update test imports to reference tests/optimization/ modules directly.
