"""Tests for the CaseManager persistence layer."""

from __future__ import annotations

import pytest

from oracle.case.manager import CaseManager
from oracle.models import (
    Confidence,
    Evidence,
    Finding,
    Identity,
    IdentityType,
    Relationship,
    Severity,
)


def test_create_and_get_case(manager: CaseManager) -> None:
    case = manager.create_case("Primary Audit", "Initial assessment")
    loaded = manager.get_case(case.id)
    assert loaded.name == "Primary Audit"
    assert loaded.description == "Initial assessment"


def test_list_cases_ordered(manager: CaseManager) -> None:
    manager.create_case("First")
    manager.create_case("Second")
    names = [c.name for c in manager.list_cases()]
    assert names == ["First", "Second"]


def test_delete_case(manager: CaseManager) -> None:
    case = manager.create_case("Temp")
    manager.delete_case(case.id)
    with pytest.raises(KeyError):
        manager.get_case(case.id)


def test_get_missing_case_raises(manager: CaseManager) -> None:
    with pytest.raises(KeyError):
        manager.get_case("does-not-exist")


def test_add_and_list_identities(manager: CaseManager) -> None:
    case = manager.create_case("Audit")
    identity = manager.add_identity(
        case.id,
        Identity(type=IdentityType.USERNAME, value="example_user"),
    )
    assert identity.case_id == case.id
    identities = manager.list_identities(case.id)
    assert len(identities) == 1
    assert identities[0].value == "example_user"


def test_add_finding_with_evidence(manager: CaseManager) -> None:
    case = manager.create_case("Audit")
    finding = manager.add_finding(
        case.id,
        Finding(
            category="Identity Correlation",
            severity=Severity.HIGH,
            confidence=Confidence.CONFIRMED,
            description="Username reused across platforms.",
            evidence=[Evidence(source="github.com", url="https://github.com/x")],
        ),
    )
    assert finding.case_id == case.id
    findings = manager.list_findings(case.id)
    assert len(findings) == 1
    stored = findings[0]
    assert stored.category == "Identity Correlation"
    assert stored.severity is Severity.HIGH
    assert len(stored.evidence) == 1
    assert stored.evidence[0].source == "github.com"


def test_add_and_list_relationships(manager: CaseManager) -> None:
    case = manager.create_case("Audit")
    first = manager.add_identity(
        case.id, Identity(type=IdentityType.USERNAME, value="alice")
    )
    second = manager.add_identity(
        case.id, Identity(type=IdentityType.EMAIL, value="alice@example.com")
    )
    manager.add_relationship(
        case.id,
        Relationship(
            identity_a_id=first.id,
            identity_b_id=second.id,
            relationship_type="same_email",
            confidence=Confidence.CONFIRMED,
        ),
    )
    relationships = manager.list_relationships(case.id)
    assert len(relationships) == 1
    assert relationships[0].identity_b_id == second.id


def test_case_isolation(manager: CaseManager) -> None:
    case_a = manager.create_case("A")
    case_b = manager.create_case("B")
    manager.add_identity(
        case_a.id, Identity(type=IdentityType.USERNAME, value="only-in-a")
    )
    assert manager.list_identities(case_a.id)
    assert not manager.list_identities(case_b.id)
