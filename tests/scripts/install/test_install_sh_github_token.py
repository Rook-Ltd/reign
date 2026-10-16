"""`clone_repo()` authenticates the private repo with REIGN_GITHUB_TOKEN.

Reign's repo is private, so a machine without GitHub access installs with a
read-only token. The token has to reach the clone, and it has to stay in
origin's URL: `reign update` fetches with plain git and no prompt, so a token
used once and dropped would leave the install unable to update. A checkout
that already exists gets the token applied before the installer's fetch.

Drives the real `clone_repo()` out of `scripts/install.sh` with real git. A
`url.<local bare repo>.insteadOf` rule stands in for github.com, so origin's
configured URL is what the installer wrote, while the bytes come from disk.
"""

import os
import subprocess
from pathlib import Path

INSTALL_SH = (
    Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "install.sh"
)
TOKEN = "github_pat_test0123456789"
TOKEN_URL = f"https://x-access-token:{TOKEN}@github.com/asxi9832/reign.git"
PLAIN_URL = "https://github.com/asxi9832/reign.git"


def _git(*args, cwd=None, env=None):
    return subprocess.run(
        ["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True
    ).stdout.strip()


def _env(tmp_path: Path, remote: Path) -> dict:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    rewrites = {
        f"file://{remote}": TOKEN_URL,
        f"file://{tmp_path}/no-ssh": "git@github.com:asxi9832/reign.git",
    }
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(home),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_COUNT": str(len(rewrites) + 1),
        "GIT_CONFIG_KEY_0": "protocol.file.allow",
        "GIT_CONFIG_VALUE_0": "always",
        "REIGN_GITHUB_TOKEN": TOKEN,
    }
    for i, (base, url) in enumerate(rewrites.items(), start=1):
        env[f"GIT_CONFIG_KEY_{i}"] = f"url.{base}.insteadOf"
        env[f"GIT_CONFIG_VALUE_{i}"] = url
    return env


def _remote(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    _git("init", "-q", "-b", "main", cwd=src)
    (src / "README.md").write_text("reign\n", encoding="utf-8")
    _git("add", ".", cwd=src)
    _git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init", cwd=src)
    remote = tmp_path / "remote.git"
    _git("clone", "-q", "--bare", str(src), str(remote))
    return remote


def _run_clone_repo(tmp_path: Path, install_dir: Path, env: dict):
    script = (
        "set -e\n"
        f"eval \"$(sed -n '/^REPO_URL_SSH=/,/^REIGN_HOME=/p' {INSTALL_SH})\"\n"
        f"eval \"$(sed -n '/^discard_update_lockfile_churn() {{/,/^}}/p' {INSTALL_SH})\"\n"
        f"eval \"$(sed -n '/^clone_repo() {{/,/^}}/p' {INSTALL_SH})\"\n"
        "log_info(){ :; }; log_warn(){ :; }; log_success(){ :; }; log_error(){ echo \"$*\" >&2; }\n"
        f"INSTALL_DIR={install_dir}; BRANCH=main; INSTALL_COMMIT=''; INSTALL_TAG=''\n"
        "clone_repo\n"
    )
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, env=env, cwd=tmp_path
    )


def test_fresh_clone_keeps_token_in_origin(tmp_path):
    env = _env(tmp_path, _remote(tmp_path))
    install_dir = tmp_path / "reign"

    result = _run_clone_repo(tmp_path, install_dir, env)

    assert result.returncode == 0, result
    assert (install_dir / "README.md").is_file()
    assert _git("config", "remote.origin.url", cwd=install_dir, env=env) == TOKEN_URL


def test_existing_checkout_gets_token_before_fetch(tmp_path):
    env = _env(tmp_path, _remote(tmp_path))
    install_dir = tmp_path / "reign"
    _git("clone", "-q", TOKEN_URL, str(install_dir), env=env)
    _git("remote", "set-url", "origin", PLAIN_URL, cwd=install_dir, env=env)

    result = _run_clone_repo(tmp_path, install_dir, env)

    assert result.returncode == 0, result
    assert _git("config", "remote.origin.url", cwd=install_dir, env=env) == TOKEN_URL
