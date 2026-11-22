"""Sites the move rewrite leaves alone.

``EXCLUDED`` rows are ``(path, anchor, reason)``; ``BY_HAND`` rows are ``(path, anchor)``: a rewrite inside the
anchored site is flagged as ``by-hand`` instead. An excluded site is neither rewritten nor flagged, and the run
prints each reason once with its site count.

``path`` is the file's path before any move; it also matches the file's new path after this move and the moves
already in the compat MOVES table. ``anchor`` is exact source text: every place it occurs is a site, widened to
the whole statement when it starts a ``def``, ``class``, assignment or ``return``. An empty anchor is the whole file. No line
numbers, so a row holds while the lines around the site shift, and a row whose anchor is gone is flagged.
"""
from __future__ import annotations

import ast

SHIPPED = "called by shipped updaters and installers of earlier releases"
PERSISTED = "text persisted into units, launchers, desktop entries and the Codex MCP config that outlive this tree"
IDENTITY = "matches processes started before the move by their old command line"
FROZEN = "frozen code for historical updaters"
TORN_UPDATE = "torn-update fallback that reads the directory a killed update moved aside"
OLD_NAMES = "a test of how old top-level names resolve, so it names them on purpose"
KEPT_NAMES = (SHIPPED, PERSISTED, IDENTITY)
"""Reasons whose sites keep module names that tests may mirror: those names are flagged in test argv, not rewritten."""

EXCLUDED: tuple[tuple[str, str, str], ...] = (
    ("reign_cli/_old_updater.py", "", FROZEN),
    ("tests/compat/old_updater_dependencies.py", "", FROZEN),
    ("reign_cli/_launchers.py", "def runtime_command(", PERSISTED),
    ("reign_cli/_launchers.py", '_CLOSURE_REPAIR = """\\', PERSISTED),
    ("reign_cli/_launchers.py", "return (\n        # The repair's own stdlib", PERSISTED),
    ("reign_cli/_launchers.py", "def print_runtime_command(", PERSISTED),
    ("reign_bootstrap.py", "def _settle_interrupted_update(", TORN_UPDATE),
    (".github/actions/plugin-validate/action.yml", '"$_VALIDATOR_PYTHON" -I -m reign_cli.main plugins validate "$_PLUGIN_PATH"', SHIPPED),
    ("apps/bootstrap-installer/src-tauri/src/update.rs", 'if install_root.join("reign_cli/_launchers.py").is_file() {', SHIPPED),
    ("apps/desktop/electron/desktop-uninstall.ts", "return ['-m', 'reign_cli.uninstall', '--mode', mode]", SHIPPED),
    ("apps/desktop/electron/main.ts", "return directoryExists(root) && fileExists(path.join(root, 'reign_cli', 'main.py'))", SHIPPED),
    ("apps/desktop/electron/main.ts", "script: path.join(root, 'reign_cli', 'backup_sqlite.py'),", SHIPPED),
    ("apps/desktop/electron/main.ts", "['-m', 'reign_cli.main', 'uninstall', '--gui-summary'],", SHIPPED),
    ("apps/desktop/electron/source-backend.ts", "if (!existsSync(path.join(root, 'reign_cli', 'main.py'))) {", SHIPPED),
    ("apps/desktop/electron/source-backend.ts", "args: ['-m', 'reign_cli.main', ...args],", SHIPPED),
    ("apps/desktop/electron/updater-process.ts", "if (!stagedFileExists(path.join(updateRoot, 'reign_cli', '_launchers.py'))) {", SHIPPED),
    ("apps/desktop/electron/updater-process.ts", "if (root && existsSync(path.join(root, 'reign_cli', 'main.py'))) {", SHIPPED),
    ("apps/desktop/electron/updater/checkout-source.ts", "? ['--run-module', 'reign_cli.source_check']", SHIPPED),
    ("apps/desktop/electron/updater/checkout-source.ts", "'from pathlib import Path; import runpy; p = Path(\"reign_cli/source_check.py\"); entry = runpy.run_path(str(p)).get(\"main\") if p.is_file() else None; entry() if callable(entry) else print(\"null\")'", SHIPPED),
    ("apps/desktop/electron/updater/state-db-preflight.ts", "const args: string[] = launcher ? ['--run-module', 'reign_cli.backup_sqlite', home] : ['-I', '-S', script, home]", SHIPPED),
    ("apps/desktop/electron/windows-reign-path.ts", "args: ['-m', 'reign_cli.main', ...backendArgs],", SHIPPED),
    ("apps/desktop/electron/windows-runtime-command.ts", "return [runtime.reignPath, '--run-module', 'reign_cli.windows_ssh_runtime', operation, ...args]", SHIPPED),
    ("gateway/status.py", "def _read_process_cmdline(", IDENTITY),
    ("gateway/status.py", "def _record_looks_like_gateway(", IDENTITY),
    ("gateway/status.py", "def profile_flag_value(", IDENTITY),
    ("gateway/status.py", "def _record_matches_live_gateway_pid(", IDENTITY),
    ("reign_cli/_launchers.py", "def installation_command(", PERSISTED),
    ("reign_cli/_launchers.py", '"reign": ("reign_cli.main", "main"),', PERSISTED),
    ("reign_cli/_launchers.py", '"reign-acp": ("acp_adapter.entry", "main"),', PERSISTED),
    ("reign_cli/_launchers.py", '"        from reign_cli import _early_recovery\\n"', PERSISTED),
    ("reign_cli/_launchers.py", '"    from reign_cli._launchers import print_runtime_command\\n"', PERSISTED),
    ("reign_cli/_launchers.py", '"    import reign_bootstrap\\n"', PERSISTED),
    ("reign_cli/_launchers.py", 'command = ([str(root / ".reign/bin/reign"), "--run-module", "run_agent"]', PERSISTED),
    ("reign_cli/_subprocess_compat.py", "def _text_names_reign(", IDENTITY),
    ("reign_cli/codex_runtime_plugin_migration.py", '"args": ["-P", "-m", "agent.transports.reign_tools_mcp_server"],',
     PERSISTED),
    ("reign_cli/container_boot.py", 'if any("main-wrapper.sh" in part for part in argv):', IDENTITY),
    ("reign_cli/dashboard_procs.py", "def _dashboard_subcommand_index(", IDENTITY),
    ("reign_cli/data_cleanup.py", 'if (canonical / "reign_cli" / "__init__.py").is_file():', SHIPPED),
    ("reign_cli/gateway.py", 'if (parent.name() or "").lower() == "services.exe":', IDENTITY),
    ("reign_cli/gateway.py", "_LEGACY_UNIT_EXECSTART_MARKERS: tuple[str, ...] = (", IDENTITY),
    ("reign_cli/gateway.py", 'cleanup = installation_command(project_root, module="gateway.cgroup_cleanup",', PERSISTED),
    ("reign_cli/gateway.py", 'stop_mark = installation_command(project_root, module="gateway.systemd_stop_mark",', PERSISTED),
    ("reign_cli/gateway_connections_ssh_remote.py", 'raw=open(f"/proc/{{pid}}/cmdline","rb").read()', IDENTITY),
    ("reign_cli/gateway_launchd.py", 'module="reign_cli.stderr_timestamp", python=_gw().get_python_path())', PERSISTED),
    ("reign_cli/gateway_windows.py", 'argv = [python_exe, "-m", "reign_cli.main"]', PERSISTED),
    ("reign_cli/linux_desktop_entry.py", 'argv = [interpreter, "-m", "reign_cli.main", *_desktop_argv_tail(project_root)]', PERSISTED),
    ("reign_cli/main_dashboard.py", "if cmdline is not None and _norm(list(cmdline)) == _norm(argv):", IDENTITY),
    ("reign_cli/main_desktop.py", "return release_dir in Path(proc.exe()).resolve().parents", IDENTITY),
    ("reign_cli/main_desktop.py", 'exe = proc.info.get("exe") or ""', IDENTITY),
    ("reign_cli/source_completion.py", 'if not (root / "reign_cli/source_completion.py").is_file():', SHIPPED),
    ("reign_cli/update_cmd_windows.py", '"reign_cli.main" in cmdline_low and (root_prefix in cmdline_low or _cwd_prefix(proc).startswith(root_prefix))', IDENTITY),
    ("reign_cli/update_cmd_windows.py", 'return "reign_cli.main" in (cmdline or "").lower() and _reign_holder_subcommand(cmdline) in _BACKEND_PURPOSES', IDENTITY),
    ("reign_cli/update_completion.py", 'str(root / "reign_cli/update_completion.py"),', SHIPPED),
    ("reign_cli/update_handoff.py", 'return [str(post_swap_python()), "-m", "reign_cli.main", "update", *argv_tail,', SHIPPED),
    ("reign_cli/update_owning_install.py", 'owner = venv.parent if (venv.parent / "reign_cli" / "main.py").is_file() else _pm_environment_owner(venv)', SHIPPED),
    ("reign_cli/update_owning_install.py", 'if install_key(owner) != state.name or not (owner / "reign_cli" / "main.py").is_file():', SHIPPED),
    ("reign_cli/update_owning_install.py", 'code = subprocess.call([sys.executable, "-m", "reign_cli.main", *sys.argv[1:]], cwd=owner, env=env)', SHIPPED),
    ("persistence/sqlite/_state/holders.py", "def _argv_scoped_to_other_home(", IDENTITY),
    ("scripts/code_health/py_rules.py", "def argv_identity(", IDENTITY),
    ("scripts/desktop-update/posix.sh", 'UPDATE_INVOKE=("$bin/python" -m reign_cli.main)', SHIPPED),
    ("scripts/desktop-update/posix.sh", 'if [ -f "$INSTALL_ROOT/reign_cli/_launchers.py" ]; then', SHIPPED),
    ("scripts/desktop-update/runtime.ps1", "[string]$Module = 'reign_cli.main'", SHIPPED),
    ("scripts/desktop-update/runtime.ps1", "if (Test-Path -LiteralPath (Join-Path $InstallRoot 'reign_cli/_launchers.py') -PathType Leaf) {", SHIPPED),
    ("scripts/desktop-update/windows.ps1", "$verifyCommand = @(Get-ReignRuntimeCommand -InstallRoot $InstallRoot -Module 'reign_cli.desktop_update_verify')", SHIPPED),
    ("scripts/install.ps1", "$completionArgs = @('-I', '-B', '-X', 'utf8', 'reign_cli/source_completion.py', '--source', $InstallDir)", SHIPPED),
    ("scripts/install.ps1", 'Invoke-Logged "Publishing the reign command" { & $bootPy -I -X utf8 reign_cli/_launchers.py $binDir }', SHIPPED),
    ("scripts/install.sh", '"$boot_py" -I -B -X utf8 reign_cli/source_completion.py "${args[@]}") \\', SHIPPED),
    ("setup-reign.sh", 'if ! "$boot_py" -I -X utf8 reign_cli/_launchers.py "$bin_dir"; then', SHIPPED),
    ("tests/reign_cli/test_stale_root_module_bridge.py", "def pre_handoff_purge(", OLD_NAMES),
    ("tests/test_reign_bootstrap.py", 'program = r"""\nimport importlib.util, os, sys\nfrom importlib.abc import MetaPathFinder', OLD_NAMES),
    ("tools/bot_desktop/runtime.py", 'Path(project_root_str()), module="tools.bot_desktop.idle_watch")),', SHIPPED),
    ("tools/mcp_tool_lifecycle.py", '"tui_gateway.slash_worker", "tui_gateway.entry",', IDENTITY),
    ("tui_gateway/host_supervisor.py", 'return "tui_gateway.compute_host" in _pid_command(pid)', IDENTITY),
    ("scripts/build/launcher_wrapper.py", 'importlib.import_module("reign_bootstrap")', PERSISTED),
)

BY_HAND: tuple[tuple[str, str], ...] = (
    ("cron/lifecycle_guard.py", 'r"|(?:\\b(?:p?kill|taskkill|stop-process)\\b[^\\n]*\\breign\\b[^\\n]*\\bgateway)"'),
    ("cron/lifecycle_guard.py", '_GATEWAY_CMDLINE_TOKEN_RE = re.compile(r"(?i)reign_cli|\\breign\\b[^\\n]*\\bgateway\\b|\\bgateway\\b[^\\n]*\\breign\\b")'),
    ("gateway/status.py", "def _gateway_command_subcommand("),
    ("gateway/status.py", 'entry = sys.modules.get("reign_cli.main")'),
    ("gateway/status_inline_source.py", 'r"\\s*from\\s+(?P<target>reign_cli\\.main)\\s+import\\s+main\\s*;\\s*sys\\.exit\\(\\s*main\\(\\)\\s*\\)")),'),
    ("reign_cli/gateway_runtime_service_identity.py", "module = next((name for name in ("),
    ("reign_cli/profiles.py", "_REIGN_ARGV_MARKERS = ("),
    ("reign_cli/update_cmd_windows.py", "def _is_entry("),
    ("reign_cli/update_receipt.py", 'if (parent / "reign_cli" / "main.py").is_file():'),
    ("reign_cli/windows_ssh_runtime.py", 'launches_module = logical_argv[1:3] == ["-m", "reign_cli.main"]'),
    ("persistence/sqlite/_state/holders.py", "_REIGN_PYTHON_MODULES = frozenset({"),
    ("tools/skill_lock.py", 'if verb == "reign" or (verb.startswith("python") and "reign_cli.main" in args):'),
)


def anchor_spans(source: str, anchor: str) -> list[tuple[int, int]]:
    """First and last line of every site ``anchor`` marks in ``source``."""
    if not anchor:
        return [(1, source.count("\n") + 1)]
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None
    statements: dict[tuple[int, int], int] = {}
    for node in ast.walk(tree) if tree is not None else ():
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign,
                             ast.Return)):
            key = (node.lineno, node.col_offset)
            statements[key] = max(statements.get(key, 0), node.end_lineno or node.lineno)
    spans, at = [], source.find(anchor)
    while at >= 0:
        line = source.count("\n", 0, at) + 1
        column = len(source[source.rfind("\n", 0, at) + 1:at].encode("utf-8"))
        spans.append((line, max(line + anchor.count("\n"), statements.get((line, column), 0))))
        at = source.find(anchor, at + 1)
    return spans
