"""``reign dashboard users`` — manage username/password dashboard logins.

Extra logins live in ``dashboard.basic_auth.users`` as ``{username: scrypt hash}``; the basic
dashboard-auth plugin reads them at startup, so changes apply after a dashboard/serve restart.
The primary ``dashboard.basic_auth.username`` (or ``REIGN_DASHBOARD_BASIC_AUTH_USERNAME``) is
shown but never edited here.
"""

from __future__ import annotations

import getpass
import os
import secrets
import sys

_RESTART_HINT = "  Restart the dashboard (or `reign serve` service) to apply."


def _basic_section(cfg: dict) -> dict:
    return cfg.setdefault("dashboard", {}).setdefault("basic_auth", {})


def _primary_username(section: dict) -> str:
    return (os.environ.get("REIGN_DASHBOARD_BASIC_AUTH_USERNAME", "").strip()
            or str(section.get("username") or "").strip())


def _read_password(args) -> str:
    if args.password_stdin:
        return sys.stdin.readline().rstrip("\n")
    password = getpass.getpass(f"  Password for {args.username}: ")
    if password != getpass.getpass("  Confirm password: "):
        sys.exit("  ✗ Passwords don't match — aborting.")
    return password


def _cmd_list(args) -> None:
    from reign_cli.config import load_config
    section = _basic_section(load_config())
    primary = _primary_username(section)
    names = sorted(set(section.get("users") or {}) | ({primary} if primary else set()))
    if not names:
        print("  No dashboard users configured. Add one with `reign dashboard users add <name>`.")
        return
    for name in names:
        print(f"  {name}" + ("  (primary)" if name == primary else ""))


def _cmd_add(args) -> None:
    from plugins.dashboard_auth.basic import hash_password
    from reign_cli.config import load_config, save_config
    from reign_cli.plugins_cmd import ensure_basic_auth_plugin_enabled_in_config

    username = args.username.strip()
    if not username:
        sys.exit("  ✗ Username must not be empty.")
    cfg = load_config()
    section = _basic_section(cfg)
    if username == _primary_username(section):
        sys.exit(f"  ✗ {username!r} is the primary login (dashboard.basic_auth.username); "
                 "change its password there instead.")
    password = _read_password(args)
    if not password:
        sys.exit("  ✗ Empty password — aborting.")
    users = dict(section.get("users") or {})
    existed = username in users
    users[username] = hash_password(password)
    section["users"] = users
    # Without a stable signing secret every restart would log everyone out.
    if not (str(section.get("secret") or "").strip()
            or os.environ.get("REIGN_DASHBOARD_BASIC_AUTH_SECRET", "").strip()):
        section["secret"] = secrets.token_urlsafe(32)
    ensure_basic_auth_plugin_enabled_in_config(cfg)
    save_config(cfg)
    print(f"  ✓ {'Updated password for' if existed else 'Added'} dashboard user {username!r}.")
    print(_RESTART_HINT)


def _cmd_remove(args) -> None:
    from reign_cli.config import load_config, save_config

    cfg = load_config()
    section = _basic_section(cfg)
    users = dict(section.get("users") or {})
    if args.username not in users:
        sys.exit(f"  ✗ No dashboard user {args.username!r} in dashboard.basic_auth.users.")
    del users[args.username]
    section["users"] = users
    save_config(cfg)
    print(f"  ✓ Removed dashboard user {args.username!r}; their sessions stop working after the restart.")
    print(_RESTART_HINT)


_ACTIONS = {
    "list": _cmd_list, "ls": _cmd_list,
    "add": _cmd_add,
    "remove": _cmd_remove, "rm": _cmd_remove,
}


def cmd_dashboard_users(args) -> None:
    action = getattr(args, "users_action", None)
    if action not in _ACTIONS:
        sys.exit("  Usage: reign dashboard users {list,add,remove}")
    _ACTIONS[action](args)
