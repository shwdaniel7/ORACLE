"""Tests for the correlation analyzer."""

from __future__ import annotations

from oracle.analyzers.correlation import build_correlation_plan
from oracle.collectors.mapper import SCAN_MARKER
from oracle.models import (
    Confidence,
    Evidence,
    Finding,
    Identity,
    IdentityType,
    Severity,
)


def _scan_finding(category: str, source: str, value: str) -> Finding:
    return Finding(
        category=category,
        severity=Severity.MEDIUM,
        confidence=Confidence.CONFIRMED,
        description=f"{source} exposure",
        evidence=[
            Evidence(
                source=source,
                url=f"https://{source}/{value}",
                observed_data=f"{SCAN_MARKER}:{source}:{value}",
            )
        ],
    )


class TestCorrelation:
    def test_single_source_produces_no_correlation(self) -> None:
        identity = Identity(type=IdentityType.USERNAME, value="octopus")
        findings = [_scan_finding("Username Reuse", "github", "octopus")]
        plan = build_correlation_plan([identity], findings)
        assert plan.findings == []
        assert plan.relationships == []

    def test_multi_source_detects_correlation(self) -> None:
        identity = Identity(type=IdentityType.USERNAME, value="octopus")
        findings = [
            _scan_finding("Username Reuse", "github", "octopus"),
            _scan_finding("Username Reuse", "reddit", "octopus"),
        ]
        plan = build_correlation_plan([identity], findings)

        assert len(plan.relationships) == 1
        relationship = plan.relationships[0]
        assert relationship.relationship_type == "same_username"
        assert relationship.confidence is Confidence.CONFIRMED
        assert relationship.identity_a_id == identity.id
        assert len(relationship.evidence) == 2

        assert len(plan.identities) == 1
        assert plan.identities[0].value == "@octopus (across platforms)"

        assert len(plan.findings) == 1
        correlation = plan.findings[0]
        assert correlation.category == "Identity Correlation"
        assert "2" in correlation.description
        assert "github" in correlation.description
        assert "reddit" in correlation.description

    def test_unrelated_findings_do_not_correlate(self) -> None:
        identity = Identity(type=IdentityType.USERNAME, value="octopus")
        findings = [
            _scan_finding("Email Exposure", "github", "octopus"),
            _scan_finding("Public Information", "crt", "example.com"),
        ]
        plan = build_correlation_plan([identity], findings)
        assert plan.findings == []
        assert plan.relationships == []

    def test_different_usernames_do_not_correlate(self) -> None:
        identities = [
            Identity(type=IdentityType.USERNAME, value="octopus"),
            Identity(type=IdentityType.USERNAME, value="another"),
        ]
        findings = [
            _scan_finding("Username Reuse", "github", "octopus"),
            _scan_finding("Username Reuse", "reddit", "another"),
        ]
        plan = build_correlation_plan(identities, findings)
        assert plan.findings == []
        assert plan.relationships == []
