"""Frozen upstream memory provider requiring the original home argument."""
import json
import os

from hermes_constants import get_hermes_home
from agent.memory_provider import MemoryProvider
from agent.secret_scope import get_secret


class UpstreamMemory(MemoryProvider):
    @property
    def name(self):
        return "upstream-memory"

    def is_available(self):
        return True

    def initialize(self, session_id, hermes_home, **kwargs):
        assert hermes_home == kwargs["reign_home"] == str(get_hermes_home())
        self.home = hermes_home

    def get_tool_schemas(self):
        return []

    def system_prompt_block(self):
        return json.dumps({"home": self.home, "secret": get_secret("PLUGIN_TEST_KEY"), "pid": os.getpid()})


def register(ctx):
    ctx.register_memory_provider(UpstreamMemory())
