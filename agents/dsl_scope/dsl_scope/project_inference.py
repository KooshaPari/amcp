"""
Project inference from chat content.

Uses NLP patterns to infer project, workspace, organization context
from conversation without explicit user input.
"""

import re
from typing import Optional
from dataclasses import dataclass
from collections import Counter


@dataclass
class InferredContext:
    """Inferred context from chat analysis."""
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    organization_id: Optional[str] = None
    project_name: Optional[str] = None
    workspace_name: Optional[str] = None
    organization_name: Optional[str] = None
    confidence: float = 0.0
    evidence: list[str] = None

    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []


class ProjectInferenceEngine:
    """Infer project/workspace/org context from chat messages."""

    # Patterns for detecting project references
    PROJECT_PATTERNS = [
        r"(?:working on|building|developing|fixing)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:project|repo|codebase)\s+(?:called|named)\s+([A-Za-z0-9_-]+)",
        r"(?:in|for)\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+project",
        r"(?:^|\s)([A-Z][a-z]+(?:[A-Z][a-z]+)+)\s+(?:has|needs|requires)",  # CamelCase
        r"(?:github\.com|gitlab\.com)/[\w-]+/([\w-]+)",  # Git URLs
    ]

    # Patterns for workspace references
    WORKSPACE_PATTERNS = [
        r"(?:in|under)\s+(?:the\s+)?([A-Z][a-z]+)\s+workspace",
        r"workspace\s+(?:called|named)\s+([A-Za-z0-9_-]+)",
        r"(?:team|group)\s+workspace:\s+([A-Za-z0-9_-]+)",
    ]

    # Patterns for organization references
    ORG_PATTERNS = [
        r"(?:at|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|LLC|Ltd)",
        r"organization:\s+([A-Za-z0-9_-]+)",
        r"(?:company|org)\s+(?:called|named)\s+([A-Za-z0-9_-]+)",
    ]

    # File path patterns that indicate project
    FILE_PATH_PATTERNS = [
        r"/([a-z_][a-z0-9_-]*)/(?:src|lib|tests?|docs?)/",  # /project_name/src/
        r"~/([a-z_][a-z0-9_-]*)/",  # ~/project_name/
        r"(?:cd|ls|vim)\s+([a-z_][a-z0-9_-]+)/",  # cd project_name/
    ]

    def __init__(self):
        self.project_counter = Counter()
        self.workspace_counter = Counter()
        self.org_counter = Counter()
        self.message_history: list[str] = []

    def infer_from_message(self, message: str) -> InferredContext:
        """Infer context from a single message."""
        self.message_history.append(message)
        evidence = []

        # Extract project mentions
        for pattern in self.PROJECT_PATTERNS:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                project_name = match.group(1)
                self.project_counter[project_name] += 1
                evidence.append(f"project: {project_name} (pattern: {pattern[:30]})")

        # Extract from file paths
        for pattern in self.FILE_PATH_PATTERNS:
            matches = re.finditer(pattern, message)
            for match in matches:
                project_name = match.group(1)
                self.project_counter[project_name] += 2  # Higher weight
                evidence.append(f"project: {project_name} (from path)")

        # Extract workspace mentions
        for pattern in self.WORKSPACE_PATTERNS:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                workspace_name = match.group(1)
                self.workspace_counter[workspace_name] += 1
                evidence.append(f"workspace: {workspace_name}")

        # Extract organization mentions
        for pattern in self.ORG_PATTERNS:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                org_name = match.group(1)
                self.org_counter[org_name] += 1
                evidence.append(f"organization: {org_name}")

        return self._build_context(evidence)

    def infer_from_history(self, window: int = 10) -> InferredContext:
        """Infer context from recent message history."""
        recent = self.message_history[-window:]
        combined_text = " ".join(recent)
        return self.infer_from_message(combined_text)

    def _build_context(self, evidence: list[str]) -> InferredContext:
        """Build inferred context from evidence."""
        # Get most common mentions
        project_name = None
        workspace_name = None
        org_name = None
        confidence = 0.0

        if self.project_counter:
            project_name, count = self.project_counter.most_common(1)[0]
            confidence = min(count / 5.0, 1.0)  # Max out at 5 mentions

        if self.workspace_counter:
            workspace_name, _ = self.workspace_counter.most_common(1)[0]

        if self.org_counter:
            org_name, _ = self.org_counter.most_common(1)[0]

        # Generate IDs (simplified - in production would hash or lookup DB)
        project_id = self._generate_id(project_name) if project_name else None
        workspace_id = self._generate_id(workspace_name) if workspace_name else None
        org_id = self._generate_id(org_name) if org_name else None

        return InferredContext(
            project_id=project_id,
            workspace_id=workspace_id,
            organization_id=org_id,
            project_name=project_name,
            workspace_name=workspace_name,
            organization_name=org_name,
            confidence=confidence,
            evidence=evidence
        )

    def _generate_id(self, name: str) -> str:
        """Generate ID from name (simplified)."""
        if not name:
            return None
        # In production, would lookup existing ID or create UUID
        return name.lower().replace(" ", "_").replace("-", "_")

    def clear_history(self) -> None:
        """Clear inference history."""
        self.message_history.clear()
        self.project_counter.clear()
        self.workspace_counter.clear()
        self.org_counter.clear()


# Global singleton
_inference_engine: Optional[ProjectInferenceEngine] = None


def get_inference_engine() -> ProjectInferenceEngine:
    """Get or create global inference engine."""
    global _inference_engine
    if _inference_engine is None:
        _inference_engine = ProjectInferenceEngine()
    return _inference_engine
