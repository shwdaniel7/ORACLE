"""Tests for the remediation plan builder."""

from __future__ import annotations

from oracle.models import Confidence, Finding, Severity
from oracle.opsec.recommendations import build_remediation_plan


def _finding(severity: Severity, recommendation: str | None = None) -> Finding:
    return Finding(
        category="Username Reuse",
        severity=severity,
        confidence=Confidence.CONFIRMED,
        description="test",
        recommendation=recommendation,
    )


def test_empty_findings_produce_empty_plan() -> None:
    plan = build_remediation_plan([])
    assert plan == {
        "HIGH PRIORITY": [],
        "MEDIUM PRIORITY": [],
        "LOW PRIORITY": [],
    }


def test_critical_and_high_land_in_high_priority() -> None:
    plan = build_remediation_plan(
        [
            _finding(Severity.CRITICAL, "Fix this first."),
            _finding(Severity.HIGH, "Also urgent."),
            _finding(Severity.MEDIUM, "Later."),
        ]
    )
    assert plan["HIGH PRIORITY"] == ["Fix this first.", "Also urgent."]
    assert plan["MEDIUM PRIORITY"] == ["Later."]


def test_default_recommendation_fallback() -> None:
    plan = build_remediation_plan([_finding(Severity.HIGH)])
    assert len(plan["HIGH PRIORITY"]) == 1
    assert "Username Reuse" in plan["HIGH PRIORITY"][0]
