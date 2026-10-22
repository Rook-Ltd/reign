"""A user's named MoA presets are not schema-defaulted config options."""

from reign_cli import config as reign_config


def test_missing_config_fields_ignores_user_named_presets_but_checks_schema_options(monkeypatch):
    """Custom preset names must not be compared against the built-in ``default`` name."""
    monkeypatch.setattr(
        reign_config,
        "load_config",
        lambda: {"moa": {"presets": {"keep_a": {}}}, "terminal": {}},
    )

    missing_keys = {field["key"] for field in reign_config.get_missing_config_fields()}

    assert not any(key.startswith("moa.presets.") for key in missing_keys)
    assert "terminal.backend" in missing_keys
