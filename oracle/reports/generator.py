"""Report generation for ORACLE assessments.

Produces structured reports in JSON and Markdown formats suitable for
personal security audits.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from oracle.__about__ import __version__
from oracle.models import Case, Evidence, Finding, Identity, Relationship
from oracle.opsec.scoring import OPSECScore

_BRAND = {
    "name": "ORACLE",
    "subtitle": "PERSONAL OPSEC INTELLIGENCE ENGINE",
    "brand_line": "OBSERVATION · INTELLIGENCE · ANALYSIS",
}


@dataclass
class AssessmentBundle:
    """All data required to render a single assessment report."""

    case: Case
    identities: list[Identity]
    findings: list[Finding]
    relationships: list[Relationship]
    score: OPSECScore
    remediation: dict[str, list[str]]

    def to_dict(self) -> dict:
        return {
            "oracle": {**self._meta(), "version": __version__},
            "assessment": {
                "case": self.case.model_dump(mode="json"),
                "generated_at": self._now(),
                "identities": [i.model_dump(mode="json") for i in self.identities],
                "findings": [f.model_dump(mode="json") for f in self.findings],
                "relationships": [
                    r.model_dump(mode="json") for r in self.relationships
                ],
                "opsec_scores": self.score.to_dict(),
            },
            "remediation": self.remediation,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_markdown(self) -> str:
        lines: list[str] = [
            "# ORACLE OPSEC ASSESSMENT",
            "",
            "**PERSONAL OPSEC INTELLIGENCE ENGINE**",
            "",
            "OBSERVATION · INTELLIGENCE · ANALYSIS",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"- **Case:** {self.case.name}",
            f"- **Case ID:** {self.case.id}",
            f"- **Generated:** {self._now()}",
            f"- **Overall OPSEC Score:** {self.score.overall} / 100",
        ]
        if self.case.description:
            lines.extend(["", self.case.description])

        lines.extend(["", "## Identity Overview", ""])
        if self.identities:
            lines.extend(["", "| Type | Value | Label |", "|------|-------|-------|"])
            for identity in self.identities:
                label = identity.label or ""
                lines.append(f"| {identity.type.value} | {identity.value} | {label} |")
        else:
            lines.extend(["*No identities recorded.*"])

        if self.findings:
            lines.extend(["", "## Exposure Findings", ""])
            for finding in self.findings:
                lines.extend(
                    [
                        f"### [{finding.severity.value} · {finding.confidence.value}] {finding.category}",
                        "",
                        finding.description,
                        "",
                    ]
                )
                if finding.evidence:
                    lines.extend(["**Evidence:**", ""])
                    for evidence in finding.evidence:
                        lines.append(self._format_evidence(evidence))
                    lines.append("")
                if finding.recommendation:
                    lines.extend(
                        [
                            f"**Recommendation:** {finding.recommendation}",
                            "",
                        ]
                    )

        if self.relationships:
            lines.extend(["", "## Identity Correlations", ""])
            for relationship in self.relationships:
                lines.extend(
                    [
                        f"### {relationship.identity_a_id} ↔ {relationship.identity_b_id} "
                        f"({relationship.relationship_type}) — {relationship.confidence.value}",
                        "",
                    ]
                )
                if relationship.notes:
                    lines.extend([relationship.notes, ""])
                for evidence in relationship.evidence:
                    lines.append(self._format_evidence(evidence))
                lines.append("")

        lines.extend(
            [
                "",
                "## OPSEC Scores",
                "",
                "| Dimension | Score |",
                "|-----------|-------|",
            ]
        )
        for dimension, value in self.score.dimensions.items():
            lines.append(f"| {dimension} | {value} |")
        lines.append(f"| **Overall** | **{self.score.overall}** |")

        lines.extend(["", "## Remediation Plan", ""])
        for priority, items in self.remediation.items():
            lines.extend([f"### {priority}", ""])
            for item in items:
                lines.append(f"- [ ] {item}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _meta() -> dict[str, str]:
        return _BRAND

    @staticmethod
    def _format_evidence(evidence: Evidence) -> str:
        location = evidence.url if evidence.url else evidence.source
        if evidence.observed_data:
            return f"- **{evidence.source}** ({location}): {evidence.observed_data}"
        return f"- **{evidence.source}** ({location})"
