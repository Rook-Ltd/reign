"""Hermes public Python names backed by the running Reign implementation.

Branding changed import and argument names, not their owning state. Aliases must
share canonical modules/classes so configuration, registries and profile scopes
cannot split into a second runtime. Removed upstream APIs stay removed.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import inspect
import re
import sys
from functools import cache, wraps
from types import ModuleType
from typing import Any, Mapping

_ROOTS = frozenset({"cli", "constants", "dir_acl", "logging", "platform", "state", "time", "yaml"})
_RENAMED_ARGUMENT = re.compile(r"(?<![A-Za-z0-9])(?:reign|Reign|REIGN)(?=_|[A-Z]|$)")
LEGACY_HOME_ARGUMENT = "hermes_home"
LEGACY_HOST_REQUIREMENT = "requires_hermes"


def canonical_module_name(name: str) -> str:
    """Translate host-owned namespaces only; third-party Hermes packages keep their names."""
    root, separator, suffix = name.partition(".")
    if not root.startswith("hermes_"):
        return name
    family = root.removeprefix("hermes_")
    if family not in _ROOTS and not family.startswith(("constants_", "state_")):
        return name
    return "reign_" + family + (separator + suffix if separator else "")


def canonical_export_name(name: str) -> str:
    return name.replace("hermes", "reign").replace("Hermes", "Reign").replace("HERMES", "REIGN")


@cache
def _keyword_adapter(function):
    aliases = {}
    for name in inspect.signature(function).parameters:
        legacy = _RENAMED_ARGUMENT.sub(
            lambda match: {"reign": "hermes", "Reign": "Hermes", "REIGN": "HERMES"}[match[0]], name)
        if legacy != name:
            aliases[legacy] = name
    if not aliases:
        return function

    @wraps(function)
    def call(*args, **kwargs):
        for old, new in aliases.items():
            if old in kwargs:
                if new in kwargs:
                    raise TypeError(f"{function.__name__}() received both {old!r} and {new!r}")
                kwargs[new] = kwargs.pop(old)
        return function(*args, **kwargs)

    return call


class _SharedModule(ModuleType):
    def __getattribute__(self, name):
        try:
            value = super().__getattribute__(name)
        except AttributeError:
            canonical = canonical_export_name(name)
            if canonical == name:
                raise
            value = super().__getattribute__(canonical)
        if not name.startswith("_") and inspect.isfunction(value):
            return _keyword_adapter(value)
        return value


class _AliasLoader(importlib.abc.Loader):
    def __init__(self, canonical: str):
        self.canonical = canonical

    def create_module(self, spec):
        module = importlib.import_module(self.canonical)
        self.metadata = (module.__name__, module.__package__, module.__loader__, module.__spec__)
        return module

    def exec_module(self, module):
        # module_from_spec assigns the alias spec even to an existing module.
        module.__name__, module.__package__, module.__loader__, module.__spec__ = self.metadata
        module.__class__ = _SharedModule


class _AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        canonical = canonical_module_name(fullname)
        if canonical == fullname:
            return None
        try:
            spec = importlib.util.find_spec(canonical)
        except ModuleNotFoundError as exc:
            if exc.name and (canonical == exc.name or canonical.startswith(exc.name + ".")):
                return None
            raise
        if spec is None:
            return None
        return importlib.util.spec_from_loader(
            fullname, _AliasLoader(canonical), is_package=spec.submodule_search_locations is not None)


_FINDER = _AliasFinder()


def install() -> None:
    """Install before plugin imports, including in probes and plugin-host children."""
    if _FINDER not in sys.meta_path:
        sys.meta_path.insert(0, _FINDER)


def select_entry_points(entry_points: Any, group: str) -> list:
    """Accept both host group names, with explicit Reign registrations taking priority."""
    def select(name):
        if hasattr(entry_points, "select"):
            return list(entry_points.select(group=name))
        if isinstance(entry_points, dict):
            return list(entry_points.get(name, []))
        return [entry for entry in entry_points if entry.group == name]

    current = select(group)
    if not group.startswith("reign_agent."):
        return current
    names = {entry.name for entry in current}
    return current + [entry for entry in select(group.replace("reign_agent.", "hermes_agent.", 1))
                      if entry.name not in names]


def host_requirement(manifest: Mapping[str, Any]) -> Any:
    """A Reign-specific constraint wins; otherwise honor the upstream host constraint."""
    return manifest.get("requires_reign") if "requires_reign" in manifest else manifest.get(LEGACY_HOST_REQUIREMENT)
