"""Tests for the Pydantic domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from oracle.models import Case, Evidence, Finding
from oracle.models.enums import Confidence, IdentityType, Severity


def test_finding_defaults(sample_finding: Finding) -> None:
    assert sample_finding.severity is Severity.HIGH
    assert sample_finding.confidence is Confidence.CONFIRMED
    assert sample_finding.evidence == []
    assert sample_finding.recommendation
    assert sample_finding.id


def test_finding_strips_whitespace() -> None:
    finding = Finding(
        category="  Username Reuse ",
        severity="LOW",
        confidence="POSSIBLE",
        description="  description  ",
    )
    assert finding.category == "Username Reuse"
    assert finding.description == "description"


def test_finding_invalid_severity() -> None:
    with pytest.raises(ValidationError):
        Finding(
            category="x",
            severity="EXTREME",
            confidence="CONFIRMED",
            description="d",
        )


def test_finding_empty_category_rejected() -> None:
    with pytest.raises(ValidationError):
        Finding(
            category="",
            severity="LOW",
            confidence="CONFIRMED",
            description="d",
        )


def test_evidence_defaults() -> None:
    evidence = Evidence(source="github.com")
    assert evidence.url is None
    assert evidence.observed_data == ""
    assert evidence.id


def test_evidence_strips_whitespace() -> None:
    evidence = Evidence(source="  github.com  ")
    assert evidence.source == "github.com"


def test_finding_serializes() -> None:
    finding = Finding(
        category="Email Exposure",
        severity="MEDIUM",
        confidence="INFERRED",
        description="Email attached to a public repository.",
        evidence=[Evidence(source="github.com", url="https://github.com/x")],
    )
    data = finding.model_dump(mode="json")
    assert data["severity"] == "MEDIUM"
    assert data["confidence"] == "INFERRED"
    assert data["evidence"][0]["url"] == "https://github.com/x"


def test_case_model() -> None:
    case = Case(name="Audit")
    assert case.name == "Audit"
    assert case.id
    summary = case.to_summary()
    assert summary["name"] == "Audit"


def test_identity_type_enum() -> None:
    assert IdentityType("email") is IdentityType.EMAIL
    assert IdentityType.USERNAME.value == "username"


def test_severity_rank() -> None:
    assert Severity.LOW.rank < Severity.CRITICAL.rank
    assert Severity.HIGH.rank == 3
