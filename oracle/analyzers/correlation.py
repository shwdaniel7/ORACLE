"""Correlation analyzer (Phase 3 · minimal).

When the same username is observed on multiple sources, the analyzer
converts that observation into structured correlation: an
``Identity Correlation`` finding (drives the ``Correlation Risk``
dimension) plus a ``same_username`` relationship bound to the registered
identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from oracle.collectors.mapper import marker_source_value
from oracle.models import (
    Confidence,
    Evidence,
    Finding,
    Identity,
    IdentityType,
    Relationship,
    Severity,
)
from oracle.models.ids import new_id

MIN_CROSS_SOURCES = 2
_CORRELATION_CATEGORY = "Identity Correlation"


@dataclass
class CorrelationPlan:
    """Proposed changes resulting from correlation analysis."""

    findings: list[Finding] = field(default_factory=list)
    identities: list[Identity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


def build_correlation_plan(
    identities: list[Identity],
    findings: list[Finding],
) -> CorrelationPlan:
    """Detect username reuse across sources and produce correlations."""
    plan = CorrelationPlan()
    username_ids: dict[str, list[str]] = {}
    for identity in identities:
        if identity.type is IdentityType.USERNAME:
            username_ids.setdefault(identity.value.lower(), []).append(identity.id)

    reuse_by_value: dict[str, dict[str, list[Evidence]]] = {}
    for finding in findings:
        if finding.category != "Username Reuse":
            continue
        for evidence in finding.evidence:
            parsed = marker_source_value(evidence.observed_data)
            if parsed is None:
                continue
            source, value = parsed
            reuse_by_value.setdefault(value.lower(), {}) \
                .setdefault(source, []).append(evidence)

    for value, sources_evidence in reuse_by_value.items():
        if len(sources_evidence) < MIN_CROSS_SOURCES:
            continue
        identity_ids = username_ids.get(value, [])
        if not identity_ids:
            continue
        raw_evidence = [item for items in sources_evidence.values() for item in items]
        finding_evidence = _mint_evidence(raw_evidence)
        relationship_evidence = _mint_evidence(raw_evidence)
        sources = sorted(sources_evidence)
        plan.findings.append(
            Finding(
                category=_CORRELATION_CATEGORY,
                severity=Severity.MEDIUM,
                confidence=Confidence.CONFIRMED,
                description=(
                    f"Username '{value}' is publicly observable across "
                    f"{len(sources)} platforms ({', '.join(sources)})."
                ),
                evidence=finding_evidence,
                recommendation=(
                    "Separate identifiers between platforms to reduce the "
                    "ability to correlate accounts."
                ),
            )
        )
        profile_identity = Identity(
            id=new_id(),
            type=IdentityType.PROFILE,
            value=f"@{value} (across platforms)",
            label="Observed public handle",
        )
        plan.identities.append(profile_identity)
        plan.relationships.append(
            Relationship(
                identity_a_id=identity_ids[0],
                identity_b_id=profile_identity.id,
                relationship_type="same_username",
                confidence=Confidence.CONFIRMED,
                evidence=relationship_evidence,
                notes="Detected automatically from multiple public sources.",
            )
        )
    return plan


def _mint_evidence(items: list[Evidence]) -> list[Evidence]:
    """Clone evidence with fresh ids so persisted entities never collide.

    The observed evidence belongs to existing findings; correlations must
    reference their own copies.
    """
    from oracle.models.ids import new_id

    return [
        Evidence(
            id=new_id(),
            source=item.source,
            url=item.url,
            observed_data=item.observed_data,
            collected_at=item.collected_at,
        )
        for item in items
    ]
