#!/usr/bin/env python3
"""Type definitions for infrastructure utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass(slots=True)
class ServiceSpec:
    """Service specification."""

    command: List[str]
    working_dir: Path
    env: Dict[str, str]
    preferred_port: int
    kill_existing: bool
    enable_tunnel: bool
    tunnel_domain: str


@dataclass(slots=True)
class InfraState:
    """Infrastructure state."""

    name: str
    display_name: str
    service: ServiceSpec
    managed_resources: Dict[str, Dict[str, Any]]
    state_file: Path


@dataclass(slots=True)
class ProjectSettings:
    """Project settings configuration."""

    name: str
    display_name: str
    project_root: Path
    config_path: Path
    state_file: Path
    default_command: List[str]
    default_workdir: Path
    default_env: Dict[str, str] = field(default_factory=dict)
    default_port: int = 8080
    default_domain: str = "localhost"
    default_kill_existing: bool = True
    default_enable_tunnel: bool = True
