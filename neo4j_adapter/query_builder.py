"""Cypher query builder for Neo4j."""

from typing import Any, Dict, List, Optional, Tuple


class CypherQueryBuilder:
    """Fluent Cypher query builder."""

    def __init__(self):
        self._match_clauses: List[str] = []
        self._where_clauses: List[str] = []
        self._create_clauses: List[str] = []
        self._merge_clauses: List[str] = []
        self._set_clauses: List[str] = []
        self._delete_clauses: List[str] = []
        self._return_clause: Optional[str] = None
        self._order_by: Optional[str] = None
        self._skip: Optional[int] = None
        self._limit: Optional[int] = None
        self._params: Dict[str, Any] = {}

    def match(self, pattern: str) -> "CypherQueryBuilder":
        """Add MATCH clause."""
        self._match_clauses.append(f"MATCH {pattern}")
        return self

    def optional_match(self, pattern: str) -> "CypherQueryBuilder":
        """Add OPTIONAL MATCH clause."""
        self._match_clauses.append(f"OPTIONAL MATCH {pattern}")
        return self

    def where(self, condition: str) -> "CypherQueryBuilder":
        """Add WHERE condition."""
        self._where_clauses.append(condition)
        return self

    def where_id(self, var: str, entity_id: str) -> "CypherQueryBuilder":
        """Add WHERE clause for entity ID."""
        param_name = f"{var}_id"
        self._where_clauses.append(f"{var}.id = ${param_name}")
        self._params[param_name] = entity_id
        return self

    def create(self, pattern: str) -> "CypherQueryBuilder":
        """Add CREATE clause."""
        self._create_clauses.append(f"CREATE {pattern}")
        return self

    def merge(self, pattern: str) -> "CypherQueryBuilder":
        """Add MERGE clause."""
        self._merge_clauses.append(f"MERGE {pattern}")
        return self

    def set(self, assignment: str) -> "CypherQueryBuilder":
        """Add SET clause."""
        self._set_clauses.append(assignment)
        return self

    def delete(self, var: str, detach: bool = False) -> "CypherQueryBuilder":
        """Add DELETE clause."""
        prefix = "DETACH DELETE" if detach else "DELETE"
        self._delete_clauses.append(f"{prefix} {var}")
        return self

    def returns(self, expression: str) -> "CypherQueryBuilder":
        """Add RETURN clause."""
        self._return_clause = f"RETURN {expression}"
        return self

    def order_by(self, expression: str, desc: bool = False) -> "CypherQueryBuilder":
        """Add ORDER BY clause."""
        direction = " DESC" if desc else ""
        self._order_by = f"ORDER BY {expression}{direction}"
        return self

    def skip(self, n: int) -> "CypherQueryBuilder":
        """Add SKIP clause."""
        self._skip = n
        return self

    def limit(self, n: int) -> "CypherQueryBuilder":
        """Add LIMIT clause."""
        self._limit = n
        return self

    def param(self, name: str, value: Any) -> "CypherQueryBuilder":
        """Add query parameter."""
        self._params[name] = value
        return self

    def params(self, **kwargs: Any) -> "CypherQueryBuilder":
        """Add multiple query parameters."""
        self._params.update(kwargs)
        return self

    def build(self) -> Tuple[str, Dict[str, Any]]:
        """Build Cypher query string and parameters."""
        parts = []

        parts.extend(self._match_clauses)

        if self._where_clauses:
            parts.append("WHERE " + " AND ".join(self._where_clauses))

        parts.extend(self._create_clauses)
        parts.extend(self._merge_clauses)

        if self._set_clauses:
            parts.append("SET " + ", ".join(self._set_clauses))

        parts.extend(self._delete_clauses)

        if self._return_clause:
            parts.append(self._return_clause)

        if self._order_by:
            parts.append(self._order_by)

        if self._skip is not None:
            parts.append(f"SKIP {self._skip}")

        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")

        query = "\n".join(parts)
        return query, self._params
