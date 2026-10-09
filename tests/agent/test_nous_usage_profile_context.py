from pathlib import Path

import pytest

from agent import account_usage, billing_usage
from reign_constants import (
    get_reign_home,
    reset_reign_home_override,
    set_reign_home_override,
)


@pytest.mark.parametrize(
    "fetcher",
    [account_usage._fetch_portal_account, billing_usage.fetch_nous_account],
)
def test_nous_account_fetch_preserves_profile_home_in_timeout_worker(
    monkeypatch, tmp_path: Path, fetcher
):
    """The bounded account fetch must read auth from the routed profile, not the launch profile."""
    launch_home = tmp_path / "launch"
    profile_home = tmp_path / "profiles" / "secondary"
    launch_home.mkdir()
    profile_home.mkdir(parents=True)
    monkeypatch.setenv("REIGN_HOME", str(launch_home))

    observed_homes: list[Path] = []

    def fake_account_fetch(*, force_fresh: bool = False):
        assert force_fresh is True
        observed_homes.append(get_reign_home())
        return observed_homes[-1]

    monkeypatch.setattr(
        "reign_cli.nous_account.get_nous_portal_account_info",
        fake_account_fetch,
    )

    token = set_reign_home_override(profile_home)
    try:
        assert get_reign_home() == profile_home
        assert fetcher(1.0) == profile_home
    finally:
        reset_reign_home_override(token)

    assert observed_homes == [profile_home]
