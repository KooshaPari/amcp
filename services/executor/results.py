"""Execution result handling and serialization.

Manages result objects, serialization, and variable extraction from
code execution namespaces.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from smartcp.services.models import ExecutionStatus


@dataclass
class ExecutionResult:
    """Result of code execution."""

    execution_id: str = field(default_factory=lambda: str(uuid4()))
    status: ExecutionStatus = ExecutionStatus.PENDING
    output: str = ""
    error: Optional[str] = None
    result: Any = None
    variables: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ResultSerializer:
    """Handles serialization of execution results."""

    @staticmethod
    def is_serializable(value: Any) -> bool:
        """Check if value can be serialized to JSON.

        Args:
            value: Value to check

        Returns:
            True if serializable
        """
        try:
            json.dumps(value)
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def serialize_result(result: Any) -> Any:
        """Serialize execution result for response.

        Args:
            result: Raw result

        Returns:
            Serializable result or string representation
        """
        if result is None:
            return None

        if ResultSerializer.is_serializable(result):
            return result

        # Fall back to string representation
        return repr(result)


class VariableExtractor:
    """Extracts and manages user-defined variables from execution namespace."""

    @staticmethod
    def extract_variables(
        namespace: dict[str, Any],
        previous: dict[str, Any],
        safe_builtins: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract user-defined variables from namespace.

        Args:
            namespace: Execution namespace
            previous: Previous user variables
            safe_builtins: Safe builtins dictionary

        Returns:
            Dictionary of new/updated variables
        """
        new_vars = {}

        for name, value in namespace.items():
            # Skip internal names
            if name.startswith("_"):
                continue

            # Skip builtins
            if name in safe_builtins:
                continue

            # Skip if it's the same as previous
            if name in previous and previous[name] == value:
                continue

            # Only include serializable values
            if ResultSerializer.is_serializable(value):
                new_vars[name] = value

        return new_vars
