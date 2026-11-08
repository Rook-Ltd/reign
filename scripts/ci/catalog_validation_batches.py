"""Bound catalog admission work without omitting entries from large upstream syncs."""

from __future__ import annotations

import json
import sys


def build_matrix(entries: list[str], batch_size: int = 20) -> dict:
    """Assign every distinct entry once; each runner gets a bounded workload."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    entries = sorted(set(entries))
    batches = [entries[start:start + batch_size] for start in range(0, len(entries), batch_size)]
    return {"include": [
        {"batch": f"{index + 1}/{len(batches)}", "files": "\n".join(batch)}
        for index, batch in enumerate(batches)
    ]}


if __name__ == "__main__":
    print(json.dumps(build_matrix([line for line in sys.stdin.read().splitlines() if line]), separators=(",", ":")))
