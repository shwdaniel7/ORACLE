"""Tests for the Click CLI."""

from __future__ import annotations

import json
import re

from click.testing import CliRunner

from oracle.__about__ import __version__
from oracle.cli.main import cli

_ID_PATTERN = re.compile(r"([0-9a-f]{32})")


def _case_id(result) -> str:
    match = _ID_PATTERN.search(result.output)
    assert match is not None, result.output
    return match.group(1)


def _runner(tmp_path, monkeypatch) -> CliRunner:
    monkeypatch.setenv("ORACLE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ORACLE_CONFIG", str(tmp_path / "config.toml"))
    return CliRunner()


def test_version(tmp_path, monkeypatch) -> None:
    result = CliRunner().invoke(cli, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_init_creates_storage(tmp_path, monkeypatch) -> None:
    runner = _runner(tmp_path, monkeypatch)
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0, result.output
    assert "ORACLE" in result.output
    assert (tmp_path / "data").is_dir()


def test_case_lifecycle(tmp_path, monkeypatch) -> None:
    runner = _runner(tmp_path, monkeypatch)
    assert runner.invoke(cli, ["init"]).exit_code == 0

    created = runner.invoke(cli, ["case", "new", "Audit", "--description", "First run"])
    assert created.exit_code == 0, created.output
    case_id = _case_id(created)

    listed = runner.invoke(cli, ["case", "list"])
    assert listed.exit_code == 0
    assert "Audit" in listed.output

    showed = runner.invoke(cli, ["case", "show", case_id])
    assert showed.exit_code == 0, showed.output
    assert "Audit" in showed.output

    deleted = runner.invoke(cli, ["case", "delete", case_id, "--force"])
    assert deleted.exit_code == 0, deleted.output


def test_identity_add_and_list(tmp_path, monkeypatch) -> None:
    runner = _runner(tmp_path, monkeypatch)
    runner.invoke(cli, ["init"])
    created = runner.invoke(cli, ["case", "new", "Audit"])
    case_id = _case_id(created)

    added = runner.invoke(
        cli,
        ["identity", "add", case_id, "--type", "username", "--value", "example_user"],
    )
    assert added.exit_code == 0, added.output

    listed = runner.invoke(cli, ["identity", "list", case_id])
    assert listed.exit_code == 0
    assert "example_user" in listed.output


def test_finding_add_with_evidence(tmp_path, monkeypatch) -> None:
    runner = _runner(tmp_path, monkeypatch)
    runner.invoke(cli, ["init"])
    created = runner.invoke(cli, ["case", "new", "Audit"])
    case_id = _case_id(created)

    added = runner.invoke(
        cli,
        [
            "finding",
            "add",
            case_id,
            "--category",
            "Identity Correlation",
            "--severity",
            "HIGH",
            "--confidence",
            "CONFIRMED",
            "--description",
            "Username reuse across platforms.",
            "--source",
            "github.com",
        ],
    )
    assert added.exit_code == 0, added.output

    listed = runner.invoke(cli, ["finding", "list", case_id])
    assert listed.exit_code == 0
    tokens = set(
        re.split(
            r"[\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u2500\u2502\s]+",
            listed.output,
        )
    )
    assert tokens >= {"Identity", "Correlation", "HIGH", "CONFIRMED"}


def test_report_json_and_markdown(tmp_path, monkeypatch) -> None:
    runner = _runner(tmp_path, monkeypatch)
    runner.invoke(cli, ["init"])
    created = runner.invoke(cli, ["case", "new", "Audit"])
    case_id = _case_id(created)
    runner.invoke(
        cli,
        ["identity", "add", case_id, "--type", "email", "--value", "a@b.example"],
    )
    runner.invoke(
        cli,
        [
            "finding",
            "add",
            case_id,
            "--category",
            "Email Exposure",
            "--severity",
            "LOW",
            "--confidence",
            "POSSIBLE",
            "--description",
            "Public email.",
        ],
    )

    markdown = runner.invoke(cli, ["report", case_id, "--format", "markdown"])
    assert markdown.exit_code == 0, markdown.output
    assert "## Executive Summary" in markdown.output
    assert "a@b.example" in markdown.output

    json_output = runner.invoke(cli, ["report", case_id, "--format", "json"])
    assert json_output.exit_code == 0, json_output.output
    payload = json.loads(json_output.output)
    assert payload["oracle"]["version"] == __version__
    assert len(payload["assessment"]["identities"]) == 1


def test_missing_case_error(tmp_path, monkeypatch) -> None:
    runner = _runner(tmp_path, monkeypatch)
    runner.invoke(cli, ["init"])
    result = runner.invoke(cli, ["report", "nope"])
    assert result.exit_code != 0
    assert "case not found" in result.output
