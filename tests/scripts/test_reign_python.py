"""``scripts/reign-python``: the interpreter a just recipe runs.

On a GitHub Actions runner it is the one setup-pm exported as REIGN_PYTHON.
Anywhere else REIGN_PYTHON may be inherited from a wrapped ``reign`` (Nix,
Termux, a TUI launch) and name a release venv without the dev tools, so the
checkout's environment (scripts/run-in-reign-env) wins. run-in-reign-env and
the inherited interpreter are stubbed at their process boundary: each announces
itself.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from tests.pm.activation_support import bash, child_env, posix

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKOUT_ENV = "run-in-reign-env python -V"
INHERITED = "REIGN_PYTHON -V"


def _announcer(path: Path, name: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'#!/usr/bin/env bash\necho "{name} $*"\n', encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.mark.parametrize("env,expected", [
    ({"GITHUB_ACTIONS": "true"}, INHERITED),
    ({}, CHECKOUT_ENV),
    ({"GITHUB_ACTIONS": "true", "__REIGN_ACTIVATED": "1"}, CHECKOUT_ENV),
    ({"GITHUB_ACTIONS": "true", "REIGN_PYTHON": "missing/python"}, CHECKOUT_ENV),
], ids=["runner", "inherited-outside-ci", "activated", "not-executable"])
def test_reign_python_picks_the_interpreter(tmp_path: Path, env: dict, expected: str):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(REPO_ROOT / "scripts" / "reign-python", scripts / "reign-python")
    _announcer(scripts / "run-in-reign-env", "run-in-reign-env")
    child = child_env()
    for key in ("GITHUB_ACTIONS", "__REIGN_ACTIVATED"):
        child.pop(key, None)
    child["REIGN_PYTHON"] = posix(_announcer(tmp_path / "release" / "python", "REIGN_PYTHON"))
    child.update(env)
    result = subprocess.run([bash(), posix(scripts / "reign-python"), "-V"], env=child, cwd=tmp_path,
                            capture_output=True, text=True, encoding="utf-8", timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected
