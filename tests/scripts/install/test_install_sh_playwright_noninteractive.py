"""`run_playwright_install()` must never wait on the terminal.

playwright is not in the CLI install's node_modules (only apps/desktop pulls it
in), so `npx playwright` asks "Ok to install?". The timeout watchdog runs it in
a background process group, where reading that answer from the terminal stops
the process until the 600s timeout kills it and Chromium is silently skipped.

Drives the real functions out of `scripts/install.sh`.
"""

import subprocess
from pathlib import Path

INSTALL_SH = (
    Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "install.sh"
)
FUNCTIONS = (
    "run_with_timeout",
    "run_browser_install_with_timeout",
    "run_playwright_install",
)


def test_playwright_install_answers_npx_without_reading_the_terminal(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    record = tmp_path / "npx.record"
    npx = bin_dir / "npx"
    # Stand-in for npx's confirmation prompt: it only proceeds unattended when
    # told yes, and otherwise reads an answer from stdin.
    npx.write_text(
        "#!/bin/sh\n"
        f'[ "$npm_config_yes" = true ] || read -r answer\n'
        f'echo "yes=$npm_config_yes" > {record}\n',
        encoding="utf-8",
    )
    npx.chmod(0o755)

    defs = "".join(
        f"eval \"$(sed -n '/^{name}() {{/,/^}}/p' {INSTALL_SH})\"\n"
        for name in FUNCTIONS
    )
    script = (
        defs
        + "log_info(){ :; }; log_warn(){ :; }\n"
        + "playwright_host_unrecognized(){ return 1; }\n"
        + "run_playwright_install 5 npx playwright install chromium\n"
    )
    # stdin stays an open pipe that never delivers an answer, like an idle terminal.
    proc = subprocess.Popen(
        ["bash", "-c", script],
        stdin=subprocess.PIPE,
        env={"PATH": f"{bin_dir}:/usr/bin:/bin"},
    )
    try:
        assert proc.wait(timeout=30) == 0
    finally:
        proc.kill()
        proc.stdin.close()
    assert record.read_text(encoding="utf-8").strip() == "yes=true"
