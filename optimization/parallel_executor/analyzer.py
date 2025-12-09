"""
Dependency analyzer for parallel tool execution.

Analyzes dependencies between tool calls to determine safe parallelization groups.
"""

from typing import Any
from collections import defaultdict


class DependencyAnalyzer:
    """Analyzes dependencies between tool calls."""

    # Tools that typically have dependencies
    DEPENDENT_PATTERNS = {
        "update": ["read", "get"],  # Update depends on read
        "delete": ["read", "get"],  # Delete depends on read
        "analyze": ["read", "search", "get"],  # Analyze depends on data gathering
        "summarize": ["read", "search"],  # Summarize depends on reading
    }

    # Tools that are always safe to parallelize
    INDEPENDENT_TOOLS = {
        "search", "list", "get", "check", "validate", "ping"
    }

    def analyze(
        self,
        tools: list[tuple[str, dict[str, Any]]],
    ) -> list[set[int]]:
        """
        Analyze tool dependencies and return parallelizable groups.

        Args:
            tools: List of (tool_name, tool_input) tuples

        Returns:
            List of sets, each set contains indices that can run in parallel
        """
        n = len(tools)
        if n == 0:
            return []

        # Build dependency graph
        deps = defaultdict(set)  # deps[i] = set of indices that i depends on

        for i, (tool_i, input_i) in enumerate(tools):
            tool_base_i = tool_i.split("_")[0].lower()

            for j, (tool_j, input_j) in enumerate(tools):
                if i == j:
                    continue

                tool_base_j = tool_j.split("_")[0].lower()

                # Check if tool_i depends on tool_j
                if self._has_dependency(tool_base_i, input_i, tool_base_j, input_j):
                    deps[i].add(j)

        # Topological grouping
        groups = []
        remaining = set(range(n))

        while remaining:
            # Find tools with no remaining dependencies
            ready = {
                i for i in remaining
                if not (deps[i] & remaining)
            }

            if not ready:
                # Cycle detected, just take one
                ready = {min(remaining)}

            groups.append(ready)
            remaining -= ready

        return groups

    def _has_dependency(
        self,
        tool_i: str,
        input_i: dict,
        tool_j: str,
        input_j: dict,
    ) -> bool:
        """Check if tool_i depends on tool_j."""
        # Independent tools never have dependencies
        if tool_i in self.INDEPENDENT_TOOLS:
            return False

        # Check pattern-based dependencies
        if tool_i in self.DEPENDENT_PATTERNS:
            if tool_j in self.DEPENDENT_PATTERNS[tool_i]:
                # Check if operating on same resource
                return self._same_resource(input_i, input_j)

        # Same resource with write after read
        if self._is_write_operation(tool_i) and self._is_read_operation(tool_j):
            return self._same_resource(input_i, input_j)

        return False

    def _same_resource(self, input_i: dict, input_j: dict) -> bool:
        """Check if two inputs operate on the same resource."""
        # Check common resource identifiers
        for key in ["path", "file", "id", "resource", "target", "url"]:
            if key in input_i and key in input_j:
                if input_i[key] == input_j[key]:
                    return True
        return False

    def _is_write_operation(self, tool: str) -> bool:
        """Check if tool is a write operation."""
        write_indicators = ["write", "update", "delete", "create", "set", "add", "remove"]
        return any(ind in tool.lower() for ind in write_indicators)

    def _is_read_operation(self, tool: str) -> bool:
        """Check if tool is a read operation."""
        read_indicators = ["read", "get", "list", "search", "find", "check"]
        return any(ind in tool.lower() for ind in read_indicators)
