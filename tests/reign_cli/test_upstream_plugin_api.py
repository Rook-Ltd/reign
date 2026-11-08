"""Unchanged upstream consumers share Reign's identity, profile and admission contracts."""
from importlib.metadata import EntryPoint, EntryPoints
import json
import os
from pathlib import Path
import shutil

import pytest
import reign_yaml as yaml

from agent import secret_scope
from reign_constants import reset_reign_home_override, set_reign_home_override
from reign_cli.plugins import PluginManager

FIXTURE = Path(__file__).parent / "fixtures" / "upstream_api"


@pytest.mark.platforms("any")
@pytest.mark.parametrize("isolation", ["in_process", "host"])
@pytest.mark.parametrize("source", ["directory", "entrypoint"])
def test_unchanged_plugin_uses_owning_profile_in_both_runtimes(tmp_path, monkeypatch, isolation, source):
    from reign_cli import plugins as plugins_mod

    empty = tmp_path / "bundled"
    empty.mkdir()
    monkeypatch.setattr(plugins_mod, "get_bundled_plugins_dir", lambda: empty)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "os-home")
    homes = [tmp_path / name for name in ("alpha", "beta")]
    managers = []
    monkeypatch.setenv("REIGN_HOME", str(homes[0]))
    monkeypatch.setenv("HERMES_HOME", "must-not-be-mirrored")
    if source == "entrypoint":
        site = tmp_path / "site"
        shutil.copytree(FIXTURE, site / "frozen_upstream_api")
        metadata = site / "frozen_upstream_api-1.0.dist-info"
        metadata.mkdir()
        (metadata / "METADATA").write_text("Metadata-Version: 2.1\nName: frozen-upstream-api\nVersion: 1.0\n")
        (metadata / "entry_points.txt").write_text(
            "[hermes_agent.plugins]\nupstream-api-fixture = frozen_upstream_api\n")
        monkeypatch.syspath_prepend(str(site))
        monkeypatch.setenv("PYTHONPATH", str(site))
    for home in homes:
        home.mkdir(parents=True)
        if source == "directory":
            shutil.copytree(FIXTURE, home / "plugins" / "upstream-api-fixture")
        (home / ".env").write_text(f"PLUGIN_TEST_KEY={home.name}\n", encoding="utf-8")
        (home / "config.yaml").write_text(yaml.safe_dump({"plugins": {
            "enabled": ["upstream-api-fixture"], "isolation": isolation}}), encoding="utf-8")
    secret_scope.set_multiplex_active(True)
    try:
        for home in homes:
            token = set_reign_home_override(home)
            secrets = secret_scope.set_secret_scope(secret_scope.build_profile_secret_scope(home))
            try:
                manager = PluginManager()
                managers.append(manager)
                manager.discover_and_load()
                assert manager._plugins["upstream-api-fixture"].error is None
            finally:
                secret_scope.reset_secret_scope(secrets)
                reset_reign_home_override(token)
        for index in (0, 1, 0):
            home, manager = homes[index], managers[index]
            token = set_reign_home_override(home)
            secrets = secret_scope.set_secret_scope(secret_scope.build_profile_secret_scope(home))
            try:
                result, = manager.invoke_hook("on_session_start", session_id="probe")
                assert (result["home"], result["secret"]) == (str(home), home.name)
                assert (result["pid"] == os.getpid()) == (isolation == "in_process")
                assert os.environ["REIGN_HOME"] == str(homes[0])
                assert os.environ["HERMES_HOME"] == "must-not-be-mirrored"
            finally:
                secret_scope.reset_secret_scope(secrets)
                reset_reign_home_override(token)
    finally:
        for manager in managers:
            manager.unload()
            host = getattr(manager, "_plugin_host_instance", None)
            if host is not None:
                host.shutdown()
        secret_scope.set_multiplex_active(False)


def test_upstream_names_keep_version_and_admission_boundaries(tmp_path, monkeypatch):
    from reign_cli.plugin_host_api import select_entry_points
    from reign_cli.plugin_validate import _run_capability_probe, validate_plugin_dir
    from reign_cli.plugins_manifest import requires_reign_error, parse_manifest_file
    from reign_cli.plugin_validate_core_override import core_override_findings
    from reign_cli.plugin_validate_private_imports import private_import_findings
    from reign_cli.plugin_isolation_audit import audit_plugin_dir

    plugin = tmp_path / "plugin"
    shutil.copytree(FIXTURE, plugin)
    manifest = yaml.safe_load((plugin / "plugin.yaml").read_text())
    recorded, error = _run_capability_probe(plugin, manifest)
    assert not error, error
    assert recorded["hooks"] == manifest["provides_hooks"]
    manifest["requires_hermes"] = ">=9999.0"
    monkeypatch.setattr("reign_cli.plugins_manifest.running_reign_version", lambda: "1.2.3")
    (plugin / "plugin.yaml").write_text(yaml.safe_dump(manifest))
    parsed = parse_manifest_file(plugin / "plugin.yaml", plugin, "user", "")
    assert parsed is not None
    assert requires_reign_error(parsed)
    assert requires_reign_error({"requires_hermes": ">=9999.0", "requires_reign": ">=1.0"}) is None
    manifest["requires_hermes"] = "not-a-version"
    (plugin / "plugin.yaml").write_text(yaml.safe_dump(manifest))
    report = validate_plugin_dir(plugin)
    assert any(name == "requires_reign" and not ok for name, ok, _ in report.checks)

    native = EntryPoint(name="shared", value="native:register", group="reign_agent.plugins")
    legacy = EntryPoint(name="shared", value="legacy:register", group="hermes_agent.plugins")
    upstream = EntryPoint(name="extra", value="extra:register", group="hermes_agent.plugins")
    assert select_entry_points(EntryPoints([legacy, upstream, native]), native.group) == [native, upstream]

    (plugin / "__init__.py").write_text(
        "import hermes_cli.config as config\n"
        "from hermes_cli.cli_config_load import _parse_service_tier_config\n"
        "def register(ctx):\n    config.load_config = lambda: {}\n")
    assert core_override_findings(plugin)
    assert private_import_findings(plugin)
    assert audit_plugin_dir(plugin).verdict == "in_process"


@pytest.mark.platforms("any")
@pytest.mark.parametrize("isolation", ["in_process", "host"])
def test_upstream_memory_provider_receives_the_same_profile_home(tmp_path, monkeypatch, isolation):
    from agent.memory_manager import MemoryManager
    from plugins.memory import load_memory_provider
    from reign_cli import plugins as plugins_mod

    homes = [tmp_path / name for name in ("alpha", "beta")]
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "os-home")
    monkeypatch.setenv("REIGN_HOME", str(homes[0]))
    for home in homes:
        directory = home / "plugins" / "upstream-memory"
        directory.mkdir(parents=True)
        shutil.copyfile(FIXTURE / "memory.py", directory / "__init__.py")
        (directory / "plugin.yaml").write_text("name: upstream-memory\n")
        (home / ".env").write_text(f"PLUGIN_TEST_KEY={home.name}\n")
        (home / "config.yaml").write_text(yaml.safe_dump({
            "plugins": {"isolation": isolation}, "memory": {"provider": "upstream-memory"}}))
    providers, managers, plugin_managers = [], [], []
    secret_scope.set_multiplex_active(True)
    try:
        for home in homes:
            token = set_reign_home_override(home)
            secrets = secret_scope.set_secret_scope(secret_scope.build_profile_secret_scope(home))
            try:
                plugin_managers.append(plugins_mod.get_plugin_manager())
                provider = load_memory_provider("upstream-memory", register_skills=False)
                assert provider is not None
                providers.append(provider)
                manager = MemoryManager()
                managers.append(manager)
                manager.add_provider(provider)
                manager.initialize_all(session_id=home.name)
            finally:
                secret_scope.reset_secret_scope(secrets)
                reset_reign_home_override(token)
        for index in (0, 1, 0):
            home = homes[index]
            token = set_reign_home_override(home)
            secrets = secret_scope.set_secret_scope(secret_scope.build_profile_secret_scope(home))
            try:
                proof = json.loads(providers[index].system_prompt_block())
                assert (proof["home"], proof["secret"]) == (str(home), home.name)
                assert (proof["pid"] == os.getpid()) == (isolation == "in_process")
            finally:
                secret_scope.reset_secret_scope(secrets)
                reset_reign_home_override(token)
    finally:
        for manager in managers:
            manager.shutdown_all()
        for manager in plugin_managers:
            manager.unload()
            host = getattr(manager, "_plugin_host_instance", None)
            if host is not None:
                host.shutdown()
        secret_scope.set_multiplex_active(False)
