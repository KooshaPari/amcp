"""Root-level pytest configuration - ensures Python path is set before any imports."""

import sys
import os
from pathlib import Path

# CRITICAL: Set path at module import time (before pytest imports anything)
project_root = Path(__file__).parent.resolve()
project_root_str = str(project_root)

# Ensure project root is FIRST in path
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)
elif sys.path[0] != project_root_str:
    sys.path.remove(project_root_str)
    sys.path.insert(0, project_root_str)

# Set environment variable for subprocesses
os.environ['PYTHONPATH'] = project_root_str

# Verify optimization can be imported
try:
    import optimization.memory.forgetting
except ImportError:
    # If still can't import, try one more time after ensuring path
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
