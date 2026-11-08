"""Login shells in the image keep Reign' own dirs on PATH.

Debian's ``/etc/profile`` resets PATH for every login shell, so without
``/etc/profile.d/reign.sh`` a ``bash -l`` (``docker exec <c> bash -l``, ssh, the
terminal tool's background ``bash -lic``) lost ``/opt/reign/bin`` and bare
``reign`` exited 127 (#56634).
"""
from __future__ import annotations

import subprocess


def test_login_shell_resolves_reign_to_the_image_shim(built_image: str) -> None:
    r = subprocess.run(
        ["docker", "run", "--rm", "-u", "reign", "--entrypoint", "bash", built_image,
         "-lc", 'echo "reign=$(command -v reign)"; echo "path=$PATH"'],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert r.returncode == 0, r.stderr
    lines = dict(line.split("=", 1) for line in r.stdout.splitlines() if "=" in line)
    assert lines["reign"] == "/opt/reign/bin/reign"
    entries = lines["path"].split(":")
    assert entries.index("/opt/reign/bin") < entries.index("/opt/reign/.venv/bin")
    assert entries.count("/opt/reign/bin") == 1
