"""Tests for report generation."""

from __future__ import annotations

import json

from oracle.case.manager import CaseManager
from oracle.models import Confidence, Finding, Identity, IdentityType, Severity
from oracle.opsec.recommendations import build_remediation_plan
from oracle.opsec.scoring import score_findings
from oracle.reports.generator import AssessmentBundle


def _bundle(manager: CaseManager, case_id: str) -> AssessmentBundle:
    return manager.build_bundle(case_id)


def test_bundle_dict_structure(manager: CaseManager) -> None:
    case = manager.create_case("Audit")
    manager.add_identity(
        case.id, Identity(type=IdentityType.USERNAME, value="example_user")
    )
    manager.add_finding(
        case.id,
        Finding(
            category="Identity Correlation",
            severity=Severity.HIGH,
            confidence=Confidence.CONFIRMED,
            description="Username reused.",
        ),
    )
    bundle = _bundle(manager, case.id)
    data = bundle.to_dict()
    assert data["oracle"]["name"] == "ORACLE"
    assert data["assessment"]["case"]["name"] == "Audit"
    assert len(data["assessment"]["identities"]) == 1
    assert len(data["assessment"]["findings"]) == 1
    assert "Overall" in data["assessment"]["opsec_scores"]


def test_to_json_is_valid_json(manager: CaseManager) -> None:
    case = manager.create_case("Audit")
    bundle = _bundle(manager, case.id)
    parsed = json.loads(bundle.to_json())
    assert parsed["oracle"]["subtitle"] == "PERSONAL OPSEC INTELLIGENCE ENGINE"


def test_to_markdown_contains_sections(manager: CaseManager) -> None:
    case = manager.create_case("Audit")
    manager.add_identity(
        case.id, Identity(type=IdentityType.EMAIL, value="a@b.example")
    )
    manager.add_finding(
        case.id,
        Finding(
            category="Email Exposure",
            severity=Severity.MEDIUM,
            confidence=Confidence.POSSIBLE,
            description="Email found in a public repo.",
            recommendation="Remove the email from the repo.",
        ),
    )
    markdown = _bundle(manager, case.id).to_markdown()
    assert "# ORACLE OPSEC ASSESSMENT" in markdown
    assert "## Executive Summary" in markdown
    assert "## Identity Overview" in markdown
    assert "a@b.example" in markdown
    assert "## Exposure Findings" in markdown
    assert "Email found in a public repo." in markdown
    assert "Remove the email from the repo." in markdown
    assert "## OPSEC Scores" in markdown
    assert "## Remediation Plan" in markdown


def test_bundle_with_empty_case(manager: CaseManager) -> None:
    case = manager.create_case("Empty")
    bundle = _bundle(manager, case.id)
    assert bundle.score.overall == 100
    assert bundle.findings == []
    assert bundle.identities == []


def test_assessment_scores_and_remediation_derived_from_findings(
    manager: CaseManager,
) -> None:
    case = manager.create_case("Audit")
    manager.add_finding(
        case.id,
        Finding(
            category="Identity Correlation",
            severity=Severity.CRITICAL,
            confidence=Confidence.CONFIRMED,
            description="Critical correlation.",
            recommendation="Fix now.",
        ),
    )
    findings = manager.list_findings(case.id)
    score = score_findings(findings)
    plan = build_remediation_plan(findings)
    assert score.dimensions["Correlation Risk"] < 100
    assert plan["HIGH PRIORITY"] == ["Fix now."]
