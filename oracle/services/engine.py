"""Assessment engine: orchestrates the ORACLE pipeline.

Covers the full workflow a user performs:
``case → identities → scan (Discover) → correlate (Analyze) → assess → remediate``.
The same engine backs both the CLI and the graphical dashboard.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from oracle.analyzers.correlation import build_correlation_plan
from oracle.case.manager import CaseManager
from oracle.collectors.base import BaseCollector
from oracle.collectors.http import HttpClient
from oracle.collectors.mapper import finding_from_probe, has_scan_evidence
from oracle.collectors.registry import (
    ProbeOutcome,
    build_collectors,
    plan_probes,
    run_scan,
)
from oracle.config import OracleConfig
from oracle.models import Finding, Relationship
from oracle.reports.generator import AssessmentBundle

DEFAULT_COLLECTORS: tuple[str, ...] = (
    "github",
    "gitlab",
    "reddit",
    "dns",
    "crt",
    "gravatar",
    "pwnedpass",
)


@dataclass(frozen=True)
class EngineSettings:
    """Tuning knobs for a scan session."""

    enabled_collectors: tuple[str, ...] = DEFAULT_COLLECTORS
    timeout_seconds: float = 10.0
    delay_seconds: float = 0.0
    max_probes_per_identity: int = 50


@dataclass(frozen=True)
class ScanProgress:
    """One progress event emitted while a scan runs."""

    total: int
    completed: int
    source: str | None
    identifier: str | None
    status: str
    detail: str


ScanProgressCallback = Callable[[ScanProgress], None]
CancelCallback = Callable[[], bool]


def settings_from_config(config: OracleConfig) -> EngineSettings:
    """Build engine settings honoring the user configuration."""
    enabled = (
        tuple(config.enabled_collectors)
        if config.enabled_collectors is not None
        else DEFAULT_COLLECTORS
    )
    return EngineSettings(
        enabled_collectors=enabled,
        timeout_seconds=config.collector_timeout,
        delay_seconds=config.collector_delay,
        max_probes_per_identity=config.collector_max_probes,
    )


class AssessmentEngine:
    """Runs discovery and correlation against a locally stored case."""

    def __init__(
        self,
        config: OracleConfig,
        manager: CaseManager | None = None,
    ) -> None:
        self.config = config
        self.manager = manager or CaseManager(config)
        self.settings = settings_from_config(config)

    def collectors(self, names: Iterable[str] | None = None) -> list[BaseCollector]:
        chosen = names if names is not None else self.settings.enabled_collectors
        return build_collectors(chosen)

    def scan(
        self,
        case_id: str,
        collector_names: Iterable[str] | None = None,
        *,
        persist: bool = True,
        progress: ScanProgressCallback | None = None,
        cancel: CancelCallback | None = None,
    ) -> list[Finding]:
        """Run discovery over the case's identities.

        Returns the findings that were produced (and persisted when
        ``persist`` is true). Re-running a probe for the same identity and
        source is de-duplicated against stored evidence.
        """
        identities = self.manager.list_identities(case_id)
        probes = plan_probes(identities, self.collectors(collector_names))
        total = len(probes)
        existing = self.manager.list_findings(case_id)
        created: list[Finding] = []
        http = HttpClient(timeout=self.settings.timeout_seconds)
        try:
            outcomes = run_scan(
                probes,
                http=http,
                delay_seconds=self.settings.delay_seconds,
                cancel=cancel,
                progress=(
                    None
                    if progress is None or total == 0
                    else _progress_emitter(progress, total)
                ),
            )
            for outcome in outcomes:
                if outcome.result is None:
                    continue
                finding = finding_from_probe(outcome.identity, outcome.result)
                if finding is None:
                    continue
                if _already_recorded(existing + created, outcome.result.source,
                                     outcome.identity.value):
                    continue
                if persist:
                    self.manager.add_finding(case_id, finding)
                created.append(finding)
        finally:
            http.close()
        return created

    def analyze(self, case_id: str) -> list[Relationship]:
        """Run minimal correlation analysis over the case's findings.

        Idempotent: re-running produces no duplicates, nor new profile
        identities or correlation findings that already exist.
        """
        identities = self.manager.list_identities(case_id)
        findings = self.manager.list_findings(case_id)
        plan = build_correlation_plan(identities, findings)

        existing_identities = {i.value for i in identities}
        existing_relationships = {
            (r.identity_a_id, r.relationship_type)
            for r in self.manager.list_relationships(case_id)
        }
        existing_descriptions = {f.description for f in findings}

        added: list[Relationship] = []
        for identity in plan.identities:
            if identity.value not in existing_identities:
                self.manager.add_identity(case_id, identity)
                existing_identities.add(identity.value)
        for finding in plan.findings:
            if finding.description in existing_descriptions:
                continue
            self.manager.add_finding(case_id, finding)
            existing_descriptions.add(finding.description)
        for relationship in plan.relationships:
            key = (relationship.identity_a_id, relationship.relationship_type)
            if key in existing_relationships:
                continue
            added.append(self.manager.add_relationship(case_id, relationship))
            existing_relationships.add(key)
        return added

    def run_assessment(
        self,
        case_id: str,
        *,
        collector_names: Iterable[str] | None = None,
        progress: ScanProgressCallback | None = None,
        cancel: CancelCallback | None = None,
    ) -> AssessmentBundle:
        """Run scan + analyze and return the full assessment bundle."""
        self.scan(case_id, collector_names, progress=progress, cancel=cancel)
        self.analyze(case_id)
        return self.manager.build_bundle(case_id)


def _already_recorded(findings: list[Finding], source: str, value: str) -> bool:
    return any(has_scan_evidence(f, source, value) for f in findings)


def _progress_emitter(
    progress: ScanProgressCallback, total: int
) -> Callable[[ProbeOutcome], None]:
    counter = 0

    def emit(outcome: ProbeOutcome) -> None:
        nonlocal counter
        counter += 1
        progress(
            ScanProgress(
                total=total,
                completed=counter,
                source=outcome.collector.name,
                identifier=outcome.identity.value,
                status=outcome.status,
                detail=outcome.detail,
            )
        )

    return emit
