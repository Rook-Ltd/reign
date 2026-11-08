"""Prompt snapshots must be deterministic without breaking native Python imports."""

import os
import subprocess
import sys
from pathlib import Path

from scripts.ci import prompt_surface


def test_skill_selection_is_pinned_without_changing_the_native_host():
    subprocess.run(
        [sys.executable, "-c", """
import sys
native_platform = sys.platform
from scripts.ci.prompt_surface import _pin_environment
_pin_environment()
import psutil
from agent.skill_utils import skill_matches_platform_list
assert sys.platform == native_platform
assert psutil.Process().pid > 0
assert skill_matches_platform_list(['linux'])
assert not skill_matches_platform_list(['macos'])
assert skill_matches_platform_list(['windows'], host_platform='win32')
"""],
        cwd=Path(__file__).resolve().parents[2],
        env=os.environ.copy(),
        check=True,
    )


def test_scrubbing_covers_environment_paths_and_native_host_labels(tmp_path, monkeypatch):
    home = tmp_path / "home"
    alias = tmp_path / "home-alias"
    home.mkdir()
    alias.mkdir()
    monkeypatch.setenv("HOME", str(alias))
    monkeypatch.setenv("REIGN_HOME", str(alias / ".reign"))

    rendered = prompt_surface._scrub(
        f"Host: native OS (release)\n{alias}/.reign\n{home}/.reign\n{alias}\n{home}", home,
    )

    assert rendered == "Host: <HOST_OS>\n<REIGN_HOME>\n<REIGN_HOME>\n<HOME>\n<HOME>"
