"""Tests for configuration parsing including collectors and gui sections."""

from __future__ import annotations

from oracle.config import OracleConfig


def test_load_collectors_and_gui_sections(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[storage]\n"
        f'data_dir = "{tmp_path.as_posix()}/data"\n'
        "[collectors]\n"
        'enabled = ["github", "crt"]\n'
        "timeout_seconds = 5.0\n"
        "delay_seconds = 0.5\n"
        "max_probes_per_identity = 10\n"
        "[gui]\n"
        'theme = "light"\n',
        encoding="utf-8",
    )
    config = OracleConfig.load(config_path=config_path)
    assert config.enabled_collectors == ("github", "crt")
    assert config.collector_timeout == 5.0
    assert config.collector_delay == 0.5
    assert config.collector_max_probes == 10
    assert config.gui_theme == "light"


def test_defaults_keep_all_collectors_enabled() -> None:
    config = OracleConfig()
    assert config.enabled_collectors is None
    assert config.gui_theme == "dark"


def test_save_round_trips_collector_config(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config = OracleConfig(data_dir=tmp_path / "data")
    config.enabled_collectors = ("github",)
    config.gui_theme = "light"
    config.save(config_path)

    reloaded = OracleConfig.load(config_path=config_path)
    assert reloaded.enabled_collectors == ("github",)
    assert reloaded.gui_theme == "light"
    assert "[collectors]" in config_path.read_text(encoding="utf-8")


def test_environment_override_wins(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ORACLE_DATA_DIR", str(tmp_path / "env"))
    config = OracleConfig.load(config_path=tmp_path / "absent.toml")
    assert config.data_dir == tmp_path / "env"
