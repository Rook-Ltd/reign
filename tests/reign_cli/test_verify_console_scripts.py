"""Orphan launcher discovery follows the declared console script names."""

from __future__ import annotations

import textwrap

import pytest
from reign_cli import main_install_repair

pytestmark = pytest.mark.platforms("windows")


@pytest.fixture
def temp_pyproject(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        textwrap.dedent(
            """\
        [project]
        name = "fake"
        version = "0.0.0"

        [project.scripts]
        reign = "reign_cli.main:main"
        reign-agent = "run_agent:main"
        reign-acp = "acp_adapter.entry:main"
    """
        )
    )
    import reign_cli.main as main_mod

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def fake_scripts_dir(tmp_path):
    scripts = tmp_path / "venv" / "Scripts"
    scripts.mkdir(parents=True)
    return scripts


class TestReignExeShims:
    """The orphan sweep includes declared scripts and the legacy gateway shim."""

    def test_shims_include_declared_console_scripts(
        self, temp_pyproject, fake_scripts_dir
    ):
        names = {path.name for path in main_install_repair._reign_exe_shims(fake_scripts_dir)}

        assert {"reign.exe", "reign-agent.exe", "reign-acp.exe"} <= names
        assert "reign-gateway.exe" in names
