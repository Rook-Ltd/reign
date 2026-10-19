"""Resolve REIGN_HOME for standalone skill scripts.

Skill scripts may run outside the Reign process (e.g. system Python,
nix env, CI) where ``reign_constants`` is not importable.  This module
provides the same ``get_reign_home()`` and ``display_reign_home()``
contracts as ``reign_constants`` without requiring it on ``sys.path``.

When ``reign_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``reign_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``REIGN_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from reign_constants import display_reign_home
    from reign_constants import get_reign_home
except (ModuleNotFoundError, ImportError):

    def get_reign_home() -> Path:
        """Return the Reign home directory (default: ~/.reign).

        Mirrors ``reign_constants.get_reign_home()``."""
        val = os.environ.get("REIGN_HOME", "").strip()
        return Path(val) if val else Path.home() / ".reign"

    def display_reign_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``reign_constants.display_reign_home()``."""
        home = get_reign_home()
        try:
            return "~/" + home.relative_to(Path.home()).as_posix()
        except ValueError:
            return str(home)
