"""
Complexity Analysis for Model Routing

Analyzes prompts to determine task complexity level,
enabling optimal model selection based on task requirements.
"""

import re
from typing import Any, Optional

from .models import ComplexityLevel, ModelRoutingConfig


class ComplexityAnalyzer:
    """Analyzes task complexity from prompts."""

    def __init__(self, config: ModelRoutingConfig):
        self.config = config
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficiency."""
        self._simple_patterns = [
            re.compile(rf"\b{kw}\b", re.IGNORECASE)
            for kw in self.config.simple_task_keywords
        ]
        self._complex_patterns = [
            re.compile(rf"\b{kw}\b", re.IGNORECASE)
            for kw in self.config.complex_task_indicators
        ]

    def analyze(
        self,
        prompt: str,
        context: Optional[dict[str, Any]] = None,
    ) -> ComplexityLevel:
        """
        Analyze prompt complexity.

        Args:
            prompt: The user prompt
            context: Optional context (tool definitions, history, etc.)

        Returns:
            Complexity level
        """
        # Check for explicit complexity hints in context
        if context:
            if context.get("require_expert"):
                return ComplexityLevel.EXPERT
            if context.get("require_complex"):
                return ComplexityLevel.COMPLEX

        # Token count heuristic
        token_estimate = len(prompt.split())
        if token_estimate < self.config.simple_task_max_tokens // 4:
            # Very short prompts are usually simple
            if any(p.search(prompt) for p in self._simple_patterns):
                return ComplexityLevel.SIMPLE

        # Check for complex indicators
        complex_matches = sum(
            1 for p in self._complex_patterns if p.search(prompt)
        )
        if complex_matches >= 2:
            return ComplexityLevel.COMPLEX

        # Check for code/technical complexity
        code_indicators = [
            "```", "function", "class", "def ", "import ",
            "error", "debug", "refactor"
        ]
        code_matches = sum(1 for ind in code_indicators if ind in prompt.lower())
        if code_matches >= 2:
            return ComplexityLevel.COMPLEX

        # Check for multi-part requests
        if any(marker in prompt for marker in ["1.", "2.", "3.", "first,", "then,"]):
            return ComplexityLevel.MODERATE

        # Default to moderate
        return ComplexityLevel.MODERATE
