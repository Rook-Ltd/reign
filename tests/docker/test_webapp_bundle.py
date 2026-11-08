"""The image ships a current Webapp renderer that the unprivileged user can use.

The install root is read-only, so ``reign webapp`` cannot build the bundle at
runtime: a gateway with ``webapp.enabled`` serves only what the build baked, and
the CLI must reuse it without taking the build lock under ``/opt/reign``.
"""
from __future__ import annotations

import subprocess


def test_webapp_build_only_reuses_the_baked_bundle(built_image: str) -> None:
    inner = "source /opt/reign/.venv/bin/activate && cd /opt/data && reign webapp --build-only"
    r = subprocess.run(
        ["docker", "run", "--rm", "--network=none", "--entrypoint", "su", built_image,
         "reign", "-s", "/bin/bash", "-c", inner],
        capture_output=True, text=True, timeout=120, check=False,
    )
    out = r.stdout + r.stderr
    assert r.returncode == 0, f"reign webapp --build-only failed in the image:\n{out[-2000:]}"
    assert "up to date" in out, out[-2000:]
