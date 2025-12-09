"""
Pattern definitions and matching logic for scope inference.

Contains regex patterns and matching utilities for detecting scope transitions.
"""

import re
from typing import Dict, List

# Phase transition patterns
PHASE_PATTERNS: Dict[str, List[str]] = {
    "planning": [
        r"let'?s? plan",
        r"how should we",
        r"strategy for",
        r"approach to",
        r"design pattern",
        r"architecture",
        r"requirements",
        r"spec(?:ification)?",
    ],
    "documentation": [
        r"write (?:a |the )?(?:doc|readme|guide)",
        r"document(?:ation)?",
        r"add comments?",
        r"explain (?:how|what|why)",
        r"create (?:a |the )?guide",
    ],
    "implementation": [
        r"implement",
        r"write (?:the )?code",
        r"add (?:a |the )?function",
        r"create (?:a |the )?class",
        r"fix (?:the )?bug",
        r"refactor",
    ],
    "testing": [
        r"test(?:s|ing)?",
        r"run tests?",
        r"pytest",
        r"coverage",
        r"verify",
        r"validate",
    ],
    "debugging": [
        r"debug",
        r"error",
        r"bug",
        r"issue",
        r"problem",
        r"fix",
        r"broken",
    ],
}

# Project mention patterns
PROJECT_PATTERNS: List[str] = [
    r"(?:working on|building|developing)\s+(?:the\s+)?([A-Z][a-z]+(?:[A-Z][a-z]+)*)",
    r"project\s+(?:called|named)\s+([A-Za-z0-9_-]+)",
    r"in\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+project",
    r"(?:github|gitlab)\.com/[\w-]+/([\w-]+)",  # Git URLs
]

# Workspace patterns
WORKSPACE_PATTERNS: List[str] = [
    r"(?:in|under)\s+(?:the\s+)?([A-Z][a-z]+)\s+workspace",
    r"workspace\s+(?:called|named)\s+([A-Za-z0-9_-]+)",
    r"(?:team|group)\s+workspace:\s+([A-Za-z0-9_-]+)",
]

# Organization patterns
ORGANIZATION_PATTERNS: List[str] = [
    r"(?:at|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|LLC|Ltd)",
    r"organization:\s+([A-Za-z0-9_-]+)",
    r"(?:company|org)\s+(?:called|named)\s+([A-Za-z0-9_-]+)",
]

# Directory change patterns
DIRECTORY_CHANGE_PATTERNS: List[str] = [
    r"cd\s+([/~][\w/.-]+)",
    r"change directory to\s+([/~][\w/.-]+)",
    r"go to\s+([/~][\w/.-]+)",
]

# Project path patterns
PROJECT_PATH_PATTERN_1 = re.compile(
    r"/([a-z_][a-z0-9_-]*)/(?:src|lib|tests?|docs?)/"
)
PROJECT_PATH_PATTERN_2 = re.compile(r"~/([a-z_][a-z0-9_-]+)/")


def score_phase_from_text(text: str) -> Dict[str, int]:
    """
    Score each phase based on pattern matches in text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary mapping phase names to scores
    """
    text_lower = text.lower()
    phase_scores = {}

    for phase, patterns in PHASE_PATTERNS.items():
        score = sum(
            1 for pattern in patterns
            if re.search(pattern, text_lower, re.IGNORECASE)
        )
        if score > 0:
            phase_scores[phase] = score

    return phase_scores


def extract_project_mentions(text: str) -> List[str]:
    """
    Extract project names from text.

    Args:
        text: Text to analyze

    Returns:
        List of project names found
    """
    projects = []
    for pattern in PROJECT_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            projects.append(match.group(1))
    return projects


def extract_workspace_mentions(text: str) -> List[str]:
    """
    Extract workspace names from text.

    Args:
        text: Text to analyze

    Returns:
        List of workspace names found
    """
    workspaces = []
    for pattern in WORKSPACE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            workspaces.append(match.group(1))
    return workspaces


def extract_organization_mentions(text: str) -> List[str]:
    """
    Extract organization names from text.

    Args:
        text: Text to analyze

    Returns:
        List of organization names found
    """
    organizations = []
    for pattern in ORGANIZATION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            organizations.append(match.group(1))
    return organizations


def extract_directory_changes(text: str) -> List[str]:
    """
    Extract directory paths from text.

    Args:
        text: Text to analyze

    Returns:
        List of directory paths found
    """
    directories = []
    for pattern in DIRECTORY_CHANGE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            directories.append(match.group(1))
    return directories


def infer_project_from_path(path: str) -> str:
    """
    Infer project name from file path.

    Args:
        path: File or directory path

    Returns:
        Project name or empty string if not found
    """
    # Pattern 1: /path/to/project_name/src/...
    match = PROJECT_PATH_PATTERN_1.search(path)
    if match:
        return match.group(1)

    # Pattern 2: ~/project_name/
    match = PROJECT_PATH_PATTERN_2.search(path)
    if match:
        return match.group(1)

    return ""
