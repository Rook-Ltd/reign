"""Catalog admissions must be data-only while retaining the complete upstream update."""

import subprocess

from rebrand.sync_catalog import record_sync_branches


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True,
        check=True, timeout=30,
    ).stdout.strip()


def _commit(repo, message):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def test_catalog_admissions_are_split_without_changing_the_checkout(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.name", "Sync test")
    _git(tmp_path, "config", "user.email", "sync@example.test")
    catalog = tmp_path / "plugin-catalog"
    catalog.mkdir()
    for name in ("changed.yaml", "deleted.yml", "removed.yaml", "README.md"):
        (catalog / name).write_text("old\n")
    (tmp_path / "core.py").write_text("old\n")
    previous = _commit(tmp_path, "baseline")
    for name in ("changed.yaml", "added.yml", "removed.yaml", "README.md"):
        (catalog / name).write_text("new\n")
    (catalog / "deleted.yml").unlink()
    (tmp_path / "core.py").write_text("new\n")
    full = _commit(tmp_path, "upstream snapshot")
    output = tmp_path / "actions-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))

    code = record_sync_branches(tmp_path, full, previous, "sync/upstream-test")
    companion = _git(tmp_path, "rev-parse", "sync/upstream-test-catalog")

    assert set(_git(tmp_path, "diff", "--name-only", previous, code).splitlines()) == {
        "core.py", "plugin-catalog/README.md",
    }
    assert set(_git(tmp_path, "diff", "--name-only", code, companion).splitlines()) == {
        "plugin-catalog/changed.yaml", "plugin-catalog/added.yml",
        "plugin-catalog/deleted.yml", "plugin-catalog/removed.yaml",
    }
    assert _git(tmp_path, "rev-parse", f"{companion}^{{tree}}") == _git(tmp_path, "rev-parse", f"{full}^{{tree}}")
    assert _git(tmp_path, "merge-base", "--is-ancestor", full, code) == ""
    assert _git(tmp_path, "rev-parse", "HEAD") == full
    assert _git(tmp_path, "diff", "--name-only", "HEAD") == ""
    assert _git(tmp_path, "status", "--porcelain") == "?? actions-output"
    assert output.read_text() == "catalog_branch=sync/upstream-test-catalog\n"


def test_code_only_updates_keep_the_original_commit(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.name", "Sync test")
    _git(tmp_path, "config", "user.email", "sync@example.test")
    (tmp_path / "core.py").write_text("old\n")
    previous = _commit(tmp_path, "baseline")
    (tmp_path / "core.py").write_text("new\n")
    full = _commit(tmp_path, "code snapshot")
    output = tmp_path / "actions-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))

    assert record_sync_branches(tmp_path, full, previous, "sync/upstream-test") == full
    assert _git(tmp_path, "branch", "--list", "sync/upstream-test-catalog") == ""
    assert output.read_text() == "catalog_branch=\n"
