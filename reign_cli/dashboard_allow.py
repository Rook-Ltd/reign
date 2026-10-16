"""``reign dashboard allow`` — manage who may sign in through the self-hosted OIDC provider.

Entries live in ``dashboard.oauth.self_hosted.allowed_emails``: an address (``alice@client.com``)
or a whole domain (``@client.com``). The provider reads the list at startup, so changes apply
after a dashboard/serve restart. An empty list lets any account the IDP accepts sign in, except
on a multi-tenant Microsoft Entra issuer, which refuses everyone until the list is set.
"""

from __future__ import annotations

import sys

_RESTART_HINT = "  Restart the dashboard (or `reign serve` service) to apply."


def _normalize(entry: str) -> str:
    entry = entry.strip().lower()
    local, at, domain = entry.rpartition("@")
    if not at or not domain or "." not in domain:
        sys.exit(f"  ✗ {entry!r} is not an email address or @domain.")
    return entry


def _section(cfg: dict) -> dict:
    oauth = cfg.setdefault("dashboard", {}).setdefault("oauth", {})
    return oauth.setdefault("self_hosted", {})


def _cmd_list(args) -> None:
    from reign_cli.config import load_config
    entries = list(_section(load_config()).get("allowed_emails") or [])
    if not entries:
        print("  No allowlist entries. Add one with `reign dashboard allow add <email|@domain>`.")
    for entry in sorted(entries):
        print(f"  {entry}")


def _cmd_add(args) -> None:
    from reign_cli.config import load_config, save_config
    cfg = load_config()
    section = _section(cfg)
    entries = list(section.get("allowed_emails") or [])
    added = [e for e in map(_normalize, args.entries) if e not in entries]
    section["allowed_emails"] = entries + added
    save_config(cfg)
    for entry in added:
        print(f"  ✓ Allowed {entry}")
    print(_RESTART_HINT)


def _cmd_remove(args) -> None:
    from reign_cli.config import load_config, save_config
    cfg = load_config()
    section = _section(cfg)
    entries = list(section.get("allowed_emails") or [])
    targets = set(map(_normalize, args.entries))
    missing = targets - set(entries)
    if missing:
        sys.exit(f"  ✗ Not in the allowlist: {', '.join(sorted(missing))}")
    section["allowed_emails"] = [e for e in entries if e not in targets]
    save_config(cfg)
    print(f"  ✓ Removed {', '.join(sorted(targets))}; their sessions stop working after the restart.")
    print(_RESTART_HINT)


_ACTIONS = {
    "list": _cmd_list, "ls": _cmd_list,
    "add": _cmd_add,
    "remove": _cmd_remove, "rm": _cmd_remove,
}


def cmd_dashboard_allow(args) -> None:
    action = getattr(args, "allow_action", None)
    if action not in _ACTIONS:
        sys.exit("  Usage: reign dashboard allow {list,add,remove}")
    _ACTIONS[action](args)
