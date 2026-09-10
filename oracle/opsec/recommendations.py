"""Remediation plan generation.

Turns findings into an actionable, priority-ordered plan of recommendations.
"""

from __future__ import annotations

from oracle.models import Finding, Severity

_PRIORITY_ORDER = (
    ("HIGH PRIORITY", (Severity.CRITICAL, Severity.HIGH)),
    ("MEDIUM PRIORITY", (Severity.MEDIUM,)),
    ("LOW PRIORITY", (Severity.LOW,)),
)


def build_remediation_plan(findings: list[Finding]) -> dict[str, list[str]]:
    plan: dict[str, list[str]] = {key: [] for key, _ in _PRIORITY_ORDER}
    for priority, severities in _PRIORITY_ORDER:
        bucket = plan[priority]
        for finding in findings:
            if finding.severity not in severities:
                continue
            if finding.recommendation:
                bucket.append(finding.recommendation)
            else:
                bucket.append(_default_recommendation(finding))
    return plan


def _default_recommendation(finding: Finding) -> str:
    category = finding.category or "Unknown"
    return (
        f"Review and address the {category} exposure "
        f"(confidence: {finding.confidence.value})."
    )
