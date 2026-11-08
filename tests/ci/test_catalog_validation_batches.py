"""Catalog batching must retain complete admission coverage, including empty diffs."""

import json
import subprocess
import sys
from pathlib import Path

from scripts.ci.catalog_validation_batches import build_matrix


def test_batches_cover_every_entry_once_with_bounded_deterministic_work():
    entries = [f"plugin-catalog/plugin-{i}.yaml" for i in range(93)]
    entries.append("plugin-catalog/with spaces.yaml")
    matrix = build_matrix(entries + entries[:5], batch_size=7)
    batches = [row["files"].splitlines() for row in matrix["include"]]
    flattened = [entry for batch in batches for entry in batch]

    assert sorted(flattened) == sorted(entries)
    assert len(flattened) == len(set(flattened))
    assert all(0 < len(batch) <= 7 for batch in batches)
    assert matrix == build_matrix(list(reversed(entries)), batch_size=7)


def test_cli_preserves_admission_work_and_handles_empty_diffs():
    script = Path(__file__).resolve().parents[2] / "scripts/ci/catalog_validation_batches.py"
    for entries in ([], [f"plugin-catalog/plugin-{i}.yml" for i in range(47)]):
        result = subprocess.run(
            [sys.executable, str(script)], input="\n".join(entries),
            text=True, capture_output=True, check=True,
        )
        assert json.loads(result.stdout) == build_matrix(entries)
