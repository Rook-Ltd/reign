"""Frozen consumer of upstream public Python spellings; do not rebrand."""
import importlib
import os

import hermes_cli.config as config  # noqa: PLR0402 -- exercise the upstream dotted import form
import hermes_constants as constants
import hermes_state as state
from hermes_cli.env_loader import get_secret_source_values
from hermes_constants import get_hermes_home
from hermes_cli.profiles import _get_default_hermes_home
from agent.secret_scope import get_secret

assert constants is importlib.import_module("reign_constants")
assert config is importlib.import_module("reign_cli.config")
assert state.SessionDB is importlib.import_module("reign_state").SessionDB
assert config.__spec__.name == "reign_cli.config"
assert _get_default_hermes_home is importlib.import_module("reign_cli.profiles")._get_default_reign_home


def snapshot(session_id=None, **kwargs):
    home = get_hermes_home()
    # Exercise the old keyword even though the function itself kept its name.
    get_secret_source_values(hermes_home=home)
    return {"home": str(home), "secret": get_secret("PLUGIN_TEST_KEY"), "pid": os.getpid()}


def register(ctx):
    ctx.register_hook("on_session_start", snapshot)
