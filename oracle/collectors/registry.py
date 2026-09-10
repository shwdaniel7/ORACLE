"""Collector registry and scan runner.

Collectors are discovered by name from a curated, opt-in list. The
runner executes probes against user-owned identifiers with progress
reporting and cancellation.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from oracle.collectors.base import BaseCollector, ProbeResult
from oracle.collectors.http import HttpClient
from oracle.collectors.sources.crt import CrtCollector
from oracle.collectors.sources.dns import DnsCollector
from oracle.collectors.sources.github import GitHubCollector
from oracle.collectors.sources.gitlab import GitLabCollector
from oracle.collectors.sources.gravatar import GravatarCollector
from oracle.collectors.sources.reddit import RedditCollector
from oracle.models import Identity

DEFAULT_COLLECTORS: tuple[str, ...] = (
    "github",
    "gitlab",
    "reddit",
    "dns",
    "crt",
    "gravatar",
)

_COLLECTOR_TYPES: dict[str, type[BaseCollector]] = {
    collector.name: collector
    for collector in (
        GitHubCollector,
        GitLabCollector,
        RedditCollector,
        DnsCollector,
        CrtCollector,
        GravatarCollector,
    )
}


@dataclass(frozen=True)
class CollectorInfo:
    """User-facing metadata about a collector source."""

    name: str
    display_name: str
    description: str
    supported_identifiers: tuple[str, ...]


@dataclass
class ProbeOutcome:
    """A single probe execution bound to its identity."""

    identity: Identity
    collector: BaseCollector
    result: ProbeResult | None
    error: str | None = None

    @property
    def status(self) -> str:
        if self.result is not None:
            return self.result.status.value
        return "ERROR"

    @property
    def detail(self) -> str:
        if self.result is not None:
            return self.result.snippet or self.result.error_message or ""
        return self.error or ""


def available_collectors() -> list[BaseCollector]:
    """Instantiate every registered collector without network access."""
    return [collector_type() for collector_type in _COLLECTOR_TYPES.values()]


def build_collectors(names: Iterable[str] | None = None) -> list[BaseCollector]:
    """Instantiate the requested collectors, ignoring unknown names."""
    chosen = list(names) if names is not None else list(DEFAULT_COLLECTORS)
    collectors: list[BaseCollector] = []
    for name in chosen:
        collector_type = _COLLECTOR_TYPES.get(name)
        if collector_type is not None:
            collectors.append(collector_type())
    return collectors


def collector_infos() -> list[CollectorInfo]:
    """Metadata for every registered collector, for UI configuration."""
    return [
        CollectorInfo(
            name=collector.name,
            display_name=collector.display_name,
            description=collector.description,
            supported_identifiers=tuple(t.value for t in collector.supported_identifiers),
        )
        for collector in available_collectors()
    ]


def run_scan(
    probes: Iterable[tuple[Identity, BaseCollector]],
    *,
    http: HttpClient,
    delay_seconds: float = 0.0,
    progress: Callable[[ProbeOutcome], None] | None = None,
    cancel: Callable[[], bool] | None = None,
) -> list[ProbeOutcome]:
    """Execute probes against identities and collect the outcomes.

    ``probes`` is an iterable of  ``(identity, collector)`` pairs, already
    filtered to supported identifier types. Errors at the source boundary
    are captured as outcomes instead of propagating, so one flaky source
    never aborts the scan.
    """
    outcomes: list[ProbeOutcome] = []
    for identity, collector in probes:
        if cancel is not None and cancel():
            break
        try:
            result = collector.probe(identity.type, identity.value, http)
        except Exception as exc:  # noqa: BLE001 - boundary: never abort a scan
            outcome = ProbeOutcome(identity, collector, None, error=str(exc))
        else:
            outcome = ProbeOutcome(identity, collector, result)
        outcomes.append(outcome)
        if progress is not None:
            progress(outcome)
        if delay_seconds > 0:
            time.sleep(delay_seconds)
    return outcomes


def plan_probes(
    identities: Iterable[Identity],
    collectors: Iterable[BaseCollector],
) -> list[tuple[Identity, BaseCollector]]:
    """Pair identities with the collectors that support their type."""
    probes: list[tuple[Identity, BaseCollector]] = []
    for identity in identities:
        for collector in collectors:
            if identity.type in collector.supported_identifiers:
                probes.append((identity, collector))
    return probes
