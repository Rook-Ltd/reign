"""Keep upstream catalog admissions separate from the code that validates them."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

CATALOG_PATHS = ("plugin-catalog/*.yaml", "plugin-catalog/*.yml")


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], env=env, text=True, capture_output=True,
        check=True, timeout=30,
    ).stdout.strip()


def partition_catalog_commit(repo: Path, full_commit: str, previous_head: str) -> tuple[str, str | None]:
    """Return the code commit and its data-only companion, without touching the checkout."""
    changed = _git(repo, "diff", "--name-only", previous_head, full_commit, "--", *CATALOG_PATHS)
    if not changed:
        return full_commit, None
    with tempfile.TemporaryDirectory(prefix="reign-sync-index-") as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
        _git(repo, "read-tree", full_commit, env=env)
        _git(repo, "reset", "--quiet", previous_head, "--", *CATALOG_PATHS, env=env)
        code_tree = _git(repo, "write-tree", env=env)
    code_commit = _git(
        repo, "commit-tree", code_tree, "-p", full_commit, "-m",
        "Reign: defer upstream plugin catalog changes to a data-only companion PR",
    )
    full_tree = _git(repo, "rev-parse", f"{full_commit}^{{tree}}")
    catalog_commit = _git(
        repo, "commit-tree", full_tree, "-p", code_commit, "-m",
        "Reign: sync upstream plugin catalog (data-only companion)",
    )
    return code_commit, catalog_commit


def record_sync_branches(repo: Path, full_commit: str, previous_head: str, branch: str) -> str:
    code_commit, catalog_commit = partition_catalog_commit(repo, full_commit, previous_head)
    _git(repo, "update-ref", f"refs/heads/{branch}", code_commit)
    catalog_branch = f"{branch}-catalog" if catalog_commit else ""
    if catalog_commit:
        _git(repo, "update-ref", f"refs/heads/{catalog_branch}", catalog_commit)
        print(f"  {catalog_branch} -> {catalog_commit[:10]} (data-only PR against {branch})")
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a") as stream:
            stream.write(f"catalog_branch={catalog_branch}\n")
    return code_commit
