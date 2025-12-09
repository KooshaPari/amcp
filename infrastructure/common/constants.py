#!/usr/bin/env python3
"""Constants for infrastructure utilities."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
PHENO_SRC = ROOT / "pheno-sdk" / "src"

if PHENO_SRC.exists():  # pragma: no cover - path setup
    sys.path.insert(0, str(PHENO_SRC))

LOGGER = logging.getLogger("infra-common")

# Module-level cache for docker availability check
_DOCKER_AVAILABLE: Optional[bool] = None
