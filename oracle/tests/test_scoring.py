"""Tests for the OPSEC scoring engine."""

from __future__ import annotations

from oracle.models import Confidence, Finding, Severity
from oracle.opsec.scoring import ASSESSMENT_DIMENSIONS, score_findings


def _finding(category: str, severity: Severity, confidence: Confidence) -> Finding:
    return Finding(
        category=category,
        severity=severity,
        confidence=confidence,
        description="test finding",
    )


def test_empty_findings_score_perfect() -> None:
    score = score_findings([])
    assert score.overall == 100
    for dimension in ASSESSMENT_DIMENSIONS:
        assert score.dimensions[dimension] == 100


def test_high_confirmed_finding_reduces_dimension() -> None:
    score = score_findings(
        [_finding("Identity Correlation", Severity.HIGH, Confidence.CONFIRMED)]
    )
    assert score.dimensions["Correlation Risk"] == 80
    assert score.dimensions["Account Privacy"] == 100


def test_critical_confirmed_finding_max_penalty() -> None:
    score = score_findings(
        [_finding("Identity Correlation", Severity.CRITICAL, Confidence.CONFIRMED)]
    )
    assert score.dimensions["Correlation Risk"] == 66


def test_confidence_weights_penalty() -> None:
    confirmed = score_findings(
        [_finding("Username Reuse", Severity.HIGH, Confidence.CONFIRMED)]
    )
    inferred = score_findings(
        [_finding("Username Reuse", Severity.HIGH, Confidence.INFERRED)]
    )
    assert (
        confirmed.dimensions["Username Hygiene"]
        < inferred.dimensions["Username Hygiene"]
    )


def test_overall_is_mean_of_dimensions() -> None:
    score = score_findings(
        [_finding("Identity Correlation", Severity.CRITICAL, Confidence.CONFIRMED)]
    )
    expected = sum(score.dimensions.values()) // len(score.dimensions)
    assert score.overall == round(expected)


def test_unknown_category_does_not_affect_score() -> None:
    score = score_findings(
        [_finding("Unmapped Category", Severity.CRITICAL, Confidence.CONFIRMED)]
    )
    assert score.overall == 100
