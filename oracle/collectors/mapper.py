"""Map probe outcomes to structured ORACLE findings.

Probes that did not observe anything (``NOT_FOUND``/``UNKNOWN``/``ERROR``)
never produce a finding. Every produced finding carries evidence that
points back to the exact source, URL and identifier observed. A stable
marker in ``observed_data`` lets the engine de-duplicate re-runs.
"""

from __future__ import annotations

from oracle.collectors.base import ProbeResult, ProbeStatus
from oracle.models import (
    Confidence,
    Evidence,
    Finding,
    Identity,
    IdentityType,
    Severity,
)

SCAN_MARKER = "oracle:scan"

_CATEGORY_BY_SOURCE = {
    "github": "Username Reuse",
    "gitlab": "Username Reuse",
    "reddit": "Username Reuse",
    "dns": "Public Information",
    "crt": "Public Information",
    "gravatar": "Email Exposure",
}

_SEVERITY_BY_SOURCE = {
    "github": Severity.MEDIUM,
    "gitlab": Severity.MEDIUM,
    "reddit": Severity.MEDIUM,
    "dns": Severity.LOW,
    "crt": Severity.MEDIUM,
    "gravatar": Severity.MEDIUM,
}

_RECOMMENDATION_BY_CATEGORY = {
    "Username Reuse": (
        "Consider whether this username must be reused across platforms; "
        "distinct, non-correlatable identifiers reduce linkage risk."
    ),
    "Email Exposure": (
        "An email address publicly linked to a profile can tie accounts "
        "together; consider whether the association is necessary."
    ),
    "Public Information": (
        "Review the publicly observable information and consider restricting "
        "or removing the exposed records."
    ),
}

_STATUS_REFUSED = frozenset({ProbeStatus.NOT_FOUND, ProbeStatus.UNKNOWN})


def finding_from_probe(identity: Identity, result: ProbeResult) -> Finding | None:
    """Build a Finding for a probe result, or ``None`` when nothing was observed."""
    if result.status is ProbeStatus.ERROR or result.status in _STATUS_REFUSED:
        return None

    category = _category_for(identity, result.source)
    description: str
    if identity.type is IdentityType.USERNAME:
        description = (
            f"Publicly accessible profile found for username '{identity.value}' "
            f"on {result.source}."
        )
    else:
        description = (
            f"Publicly observable information found for '{identity.value}' "
            f"on {result.source}."
        )
    return Finding(
        category=category,
        severity=_SEVERITY_BY_SOURCE.get(result.source, Severity.MEDIUM),
        confidence=Confidence.CONFIRMED,
        description=description,
        evidence=[Evidence(source=result.source, url=result.url,
                           observed_data=_observed_data(identity, result))],
        recommendation=_RECOMMENDATION_BY_CATEGORY.get(category),
    )


def _category_for(identity: Identity, source: str) -> str:
    explicit = _CATEGORY_BY_SOURCE.get(source)
    if explicit is not None:
        return explicit
    if identity.type is IdentityType.USERNAME:
        return "Username Reuse"
    return "Public Information"


def _observed_data(identity: Identity, result: ProbeResult) -> str:
    marker = f"{SCAN_MARKER}:{result.source}:{identity.value}"
    extra = " ".join(part for part in (result.title, result.snippet) if part)
    return f"{marker} | {extra}".rstrip() if extra else marker


def has_scan_evidence(finding: Finding, source: str, value: str) -> bool:
    """Whether a finding already records the given source+identifier probe."""
    marker = f"{SCAN_MARKER}:{source}:{value}"
    return any(marker in evidence.observed_data for evidence in finding.evidence)


def marker_source_value(observed_data: str) -> tuple[str, str] | None:
    """Parse ``oracle:scan:<source>:<value>`` back into source and value."""
    if not observed_data.startswith(SCAN_MARKER + ":"):
        return None
    parts = observed_data.split("|", 1)[0].strip().split(":", 3)
    if len(parts) != 4:
        return None
    return parts[2], parts[3]
