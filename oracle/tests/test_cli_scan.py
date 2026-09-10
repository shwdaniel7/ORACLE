"""Tests for the scan and analyze CLI commands (no real network)."""

from __future__ import annotations

import re

from click.testing import CliRunner

from oracle.cli.main import cli
from oracle.models import Confidence, Finding, Severity

_ID_PATTERN = re.compile(r"([0-9a-f]{32})")


def _runner(tmp_path, monkeypatch) -> CliRunner:
    monkeypatch.setenv("ORACLE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ORACLE_CONFIG", str(tmp_path / "config.toml"))
    return CliRunner()


def _new_case(runner: CliRunner) -> str:
    created = runner.invoke(cli, ["case", "new", "Audit"])
    assert created.exit_code == 0, created.output
    match = _ID_PATTERN.search(created.output)
    assert match is not None
    return match.group(1)


class _StubEngine:
    def __init__(self, config, manager=None) -> None:
        pass

    def scan(self, case_id, collector_names=None, *, persist=True, progress=None, cancel=None):
        assert not cancel
        return [
            Finding(
                category="Username Reuse",
                severity=Severity.MEDIUM,
                confidence=Confidence.CONFIRMED,
                description="Public profile on StubSource.",
            )
        ]

    def analyze(self, case_id):
        return []


def test_scan_cli_saves_findings(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("oracle.cli.main.AssessmentEngine", _StubEngine)
    runner = _runner(tmp_path, monkeypatch)
    assert runner.invoke(cli, ["init"]).exit_code == 0
    case_id = _new_case(runner)
    added = runner.invoke(
        cli,
        ["identity", "add", case_id, "--type", "username", "--value", "octopus"],
    )
    assert added.exit_code == 0, added.output

    scanned = runner.invoke(cli, ["scan", case_id, "--collector", "github"])
    assert scanned.exit_code == 0, scanned.output
    assert "1 finding(s) saved" in scanned.output


def test_analyze_reports_no_correlations(tmp_path, monkeypatch) -> None:
    runner = _runner(tmp_path, monkeypatch)
    assert runner.invoke(cli, ["init"]).exit_code == 0
    case_id = _new_case(runner)
    result = runner.invoke(cli, ["analyze", case_id])
    assert result.exit_code == 0, result.output
    assert "No correlations detected" in result.output
