"""Catalog metadata names external code; only the host compatibility key changes."""

import json
from pathlib import Path

import pytest
from ruamel.yaml import YAML

import rebrand.rebrand as codemod


@pytest.mark.parametrize("as_json", [False, True])
def test_catalog_rebranding_preserves_external_plugin_identity(tmp_path, monkeypatch, as_json):
    mapping = YAML(typ="safe").load((Path(codemod.__file__).parent / "mapping.yaml").read_text())
    relative = "plugin-catalog/hermes-example.yaml"
    entry = tmp_path / relative
    entry.parent.mkdir()
    original = {
        "name": "hermes-example",
        "repo": "https://github.com/example/hermes-example",
        "subdir": "plugins/hermes-example",
        "description": "The external Hermes plugin keeps its HERMES_VENDOR_KEY credential name.",
        "requires_hermes": ">=0.23.0",
        "capabilities": {"provides_tools": ["hermes_lookup"], "requires_env": ["HERMES_VENDOR_KEY"]},
    }
    if as_json:
        entry.write_text(json.dumps(original))
    else:
        with entry.open("w") as stream:
            YAML().dump(original, stream)
    monkeypatch.setattr(codemod, "ROOT", tmp_path)
    rebrander = codemod.Rebrander(mapping)

    assert rebrander.rewrite_files([relative], apply=True) == []
    assert rebrander.rename_files([relative], apply=False) == []
    assert rebrander.post_replace_files([relative], apply=True) == [relative]

    result = YAML(typ="safe").load(entry.read_text())
    assert result.pop("requires_reign") == original.pop("requires_hermes")
    assert result == original
    assert rebrander.post_replace_files([relative], apply=False) == []
