"""Configuration handling for ORACLE.

Configuration is stored as a TOML file. The default location is
``~/.oracle/config.toml`` and can be overridden with the ``ORACLE_CONFIG``
environment variable. The data directory can be overridden with
``ORACLE_DATA_DIR``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]

DEFAULT_APP_DIR = Path.home() / ".oracle"
DEFAULT_CONFIG_PATH = DEFAULT_APP_DIR / "config.toml"

_SAMPLE_CONFIG = """\
# ORACLE configuration

[storage]
# Directory where cases and the assessment database are stored.
data_dir = "{data_dir}"

[reports]
# Default report format: "json" or "markdown"
default_format = "{report_format}"

[cli]
verbose = false
"""


@dataclass(slots=True)
class OracleConfig:
    """Runtime configuration for an ORACLE session."""

    data_dir: Path = DEFAULT_APP_DIR
    default_report_format: str = "markdown"
    verbose: bool = False

    @property
    def database_path(self) -> Path:
        return self.data_dir / "oracle.db"

    @classmethod
    def load(
        cls,
        config_path: Path | None = None,
        data_dir: Path | None = None,
    ) -> OracleConfig:
        config = cls()
        if data_dir is not None:
            config.data_dir = data_dir

        path = config_path or _resolve_config_path()
        if path.is_file():
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
            storage = raw.get("storage", {})
            reports = raw.get("reports", {})
            cli = raw.get("cli", {})
            configured_dir = storage.get("data_dir")
            if configured_dir:
                config.data_dir = Path(os.path.expanduser(str(configured_dir)))
            config.default_report_format = str(
                reports.get("default_format", config.default_report_format)
            )
            config.verbose = bool(cli.get("verbose", config.verbose))

        env_dir = os.environ.get("ORACLE_DATA_DIR")
        if env_dir:
            config.data_dir = Path(env_dir).expanduser()

        return config

    def save(self, config_path: Path | None = None) -> None:
        path = config_path or _resolve_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            _SAMPLE_CONFIG.format(
                data_dir=str(self.data_dir.expanduser().resolve()).replace(
                    "\\", "\\\\"
                ),
                report_format=self.default_report_format,
            ),
            encoding="utf-8",
        )


def _resolve_config_path() -> Path:
    env = os.environ.get("ORACLE_CONFIG")
    if env:
        return Path(env).expanduser()
    return DEFAULT_CONFIG_PATH
