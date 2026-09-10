"""OPSEC assessment scoring.

Produces an explainable 0-100 score per assessment dimension from a set
of findings. The score is an assessment aid, never an objective measure
of security. Every score is derived from the contributing findings.
"""

from __future__ import annotations

from dataclasses import dataclass

from oracle.models import Confidence, Finding, Severity

ASSESSMENT_DIMENSIONS = (
    "Identity Separation",
    "Username Hygiene",
    "Email Exposure",
    "Metadata Hygiene",
    "Account Privacy",
    "Public Information",
    "Correlation Risk",
)

CATEGORY_DIMENSIONS = {
    "Identity Correlation": "Correlation Risk",
    "Identity Separation": "Identity Separation",
    "Username Reuse": "Username Hygiene",
    "Email Exposure": "Email Exposure",
    "Metadata Exposure": "Metadata Hygiene",
    "Account Privacy": "Account Privacy",
    "Public Information": "Public Information",
}

_SEVERITY_PENALTY = {
    Severity.LOW: 4,
    Severity.MEDIUM: 10,
    Severity.HIGH: 20,
    Severity.CRITICAL: 34,
}

_CONFIDENCE_WEIGHT = {
    Confidence.CONFIRMED: 1.0,
    Confidence.POSSIBLE: 0.6,
    Confidence.INFERRED: 0.4,
    Confidence.NOT_FOUND: 0.0,
}


@dataclass(frozen=True)
class OPSECScore:
    """Result of an OPSEC assessment over a case's findings."""

    dimensions: dict[str, int]
    overall: int

    def to_dict(self) -> dict[str, int]:
        return {**self.dimensions, "Overall": self.overall}


def score_findings(findings: list[Finding]) -> OPSECScore:
    penalties: dict[str, float] = {}
    for finding in findings:
        dimension = CATEGORY_DIMENSIONS.get(finding.category)
        if dimension is None:
            continue
        base_penalty = _SEVERITY_PENALTY.get(finding.severity, 5)
        weight = _CONFIDENCE_WEIGHT.get(finding.confidence, 0.5)
        penalties[dimension] = penalties.get(dimension, 0.0) + base_penalty * weight

    dimensions: dict[str, int] = {}
    for dimension in ASSESSMENT_DIMENSIONS:
        penalty = penalties.get(dimension, 0.0)
        dimensions[dimension] = max(0, min(100, int(round(100 - penalty))))

    overall = int(round(sum(dimensions.values()) / len(dimensions)))
    return OPSECScore(dimensions=dimensions, overall=overall)
