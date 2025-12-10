"""Scope package for 11-level scope hierarchy."""

from smartcp.runtime.scope.api import ScopeAPI
from smartcp.runtime.scope.manager import ScopeManager
from smartcp.runtime.scope.types import ScopeLevel, ScopeKey

__all__ = [
    "ScopeManager",
    "ScopeAPI",
    "ScopeLevel",
    "ScopeKey",
]
