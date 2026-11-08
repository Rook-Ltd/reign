"""`reign profile delete|rename` never removes another install's gateway service.

Service names derive from the profile name and the user unit dir is account-anchored, so a scratch-HOME
delete of `coder` named the ACCOUNT's real `reign-gateway-coder` unit and disabled, stopped and unlinked
it. Every service-manager seam is a recorder; nothing here executes one.
"""

from __future__ import annotations

import os

import pytest

from reign_cli import gateway as gw


def _unit(path, home) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'[Service]\nEnvironment="REIGN_HOME={home}"\nExecStart=/usr/bin/reign gateway run\n',
                    encoding="utf-8")


@pytest.mark.platforms("linux")
def test_profile_delete_from_scratch_home_leaves_the_accounts_profile_unit(tmp_path, monkeypatch, capsys):
    """``reign profile delete|rename coder`` with HOME=<scratch>: the name resolves the ACCOUNT's real
    ``reign-gateway-coder`` unit (account-anchored unit dir). It pins another home, so cleanup never
    disables, stops or unlinks it."""
    import reign_constants
    from reign_cli import profiles
    account, scratch = tmp_path / "account", tmp_path / "scratch"
    profile_dir = scratch / ".reign" / "profiles" / "coder"
    profile_dir.mkdir(parents=True)
    real_unit = account / ".config" / "systemd" / "user" / "reign-gateway-coder.service"
    _unit(real_unit, account / ".reign" / "profiles" / "coder")
    monkeypatch.delenv("REIGN_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(scratch))
    monkeypatch.setenv("REIGN_REAL_HOME", str(account))
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.setattr(reign_constants, "_account_home", lambda: account)
    monkeypatch.setattr(gw, "_SYSTEM_UNIT_DIR", tmp_path / "no-system-units")
    calls: list = []
    monkeypatch.setattr(profiles.subprocess, "run", lambda argv, *a, **k: calls.append(list(argv)))

    assert profiles._cleanup_gateway_service("coder", profile_dir) is False

    assert calls == [] and real_unit.exists()
    assert "another install's service, left alone" in capsys.readouterr().out
