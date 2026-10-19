"""Resolve REIGN_HOME for standalone skill scripts.

Skill scripts may run outside the Reign process (system Python, nix env,
CI) where ``reign_constants`` is not importable.  This module provides the
same ``get_reign_home()`` contract without requiring it on ``sys.path``.

When ``reign_constants`` IS available it is used directly so profile
resolution and any future enhancements are picked up automatically.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from reign_constants import get_reign_home
except (ModuleNotFoundError, ImportError):

    def get_reign_home() -> Path:
        """Return the Reign home directory (default: ``~/.reign``)."""
        val = os.environ.get("REIGN_HOME", "").strip()
        return Path(val) if val else Path.home() / ".reign"
