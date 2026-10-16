"""`setup_path()` in --no-venv mode must resolve Reign's own console script.

Without a venv, the launcher wraps whatever `reign` the package install put on
PATH. A machine that also runs upstream Hermes has a `hermes` command there too,
so resolving the wrong name would point every Reign launcher at Hermes.

Drives the real `setup_path()` out of `scripts/install.sh`.
"""

import os
import subprocess
from pathlib import Path

INSTALL_SH = (
    Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "install.sh"
)


def _fake_command(bin_dir: Path, name: str) -> Path:
    path = bin_dir / name
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_no_venv_launcher_targets_reign_not_hermes(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_command(bin_dir, "hermes")
    reign = _fake_command(bin_dir, "reign")
    home = tmp_path / "home"
    home.mkdir()

    script = (
        "set +e\n"
        f"eval \"$(sed -n '/^setup_path() {{/,/^}}/p' {INSTALL_SH})\"\n"
        "log_info(){ :; }; log_warn(){ :; }; log_success(){ :; }; log_error(){ :; }\n"
        f"USE_VENV=false; INSTALL_DIR={tmp_path}/src; DISTRO=ubuntu; OS=linux\n"
        "setup_path >/dev/null 2>&1\n"
        'printf "%s" "$REIGN_BIN"\n'
    )
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(home)}
    result = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, env=env, cwd=tmp_path
    )
    assert result.stdout == str(reign), result
