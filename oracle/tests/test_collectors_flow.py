"""Tests for result mapping and the collector registry/runner."""

from __future__ import annotations

from oracle.collectors.base import ProbeResult, ProbeStatus
from oracle.collectors.mapper import (
    finding_from_probe,
    has_scan_evidence,
    marker_source_value,
)
from oracle.collectors.registry import build_collectors, plan_probes, run_scan
from oracle.models import Identity, IdentityType


class TestMapper:
    def test_found_username_becomes_evidence_backed_finding(self) -> None:
        identity = Identity(type=IdentityType.USERNAME, value="octopus")
        result = ProbeResult(
            source="github",
            identifier="octopus",
            identifier_type=IdentityType.USERNAME,
            status=ProbeStatus.FOUND,
            url="https://github.com/octopus",
            title="@octopus on GitHub",
            snippet="public profile",
        )
        finding = finding_from_probe(identity, result)
        assert finding is not None
        assert finding.category == "Username Reuse"
        assert finding.confidence.value == "CONFIRMED"
        assert finding.evidence[0].source == "github"
        assert finding.evidence[0].url == "https://github.com/octopus"

    def test_not_found_produces_nothing(self) -> None:
        identity = Identity(type=IdentityType.USERNAME, value="nobody")
        result = ProbeResult(
            source="github",
            identifier="nobody",
            identifier_type=IdentityType.USERNAME,
            status=ProbeStatus.NOT_FOUND,
        )
        assert finding_from_probe(identity, result) is None

    def test_unknown_produces_nothing(self) -> None:
        identity = Identity(type=IdentityType.USERNAME, value="weird")
        result = ProbeResult(
            source="reddit",
            identifier="weird",
            identifier_type=IdentityType.USERNAME,
            status=ProbeStatus.UNKNOWN,
        )
        assert finding_from_probe(identity, result) is None

    def test_marker_round_trip(self) -> None:
        identity = Identity(type=IdentityType.USERNAME, value="octopus")
        result = ProbeResult(
            source="gitlab",
            identifier="octopus",
            identifier_type=IdentityType.USERNAME,
            status=ProbeStatus.FOUND,
            title="@octopus on GitLab",
        )
        finding = finding_from_probe(identity, result)
        assert finding is not None
        observed = finding.evidence[0].observed_data
        assert has_scan_evidence(finding, "gitlab", "octopus")
        assert marker_source_value(observed) == ("gitlab", "octopus")


class _StubCollector:
    """Minimal collector used to exercise the registry runner."""

    name = "stub"
    display_name = "Stub"
    description = "test collector"
    supported_identifiers = frozenset({IdentityType.USERNAME})
    reliability = 1.0

    def __init__(self, status: ProbeStatus = ProbeStatus.FOUND) -> None:
        self._status = status

    def probe(self, identifier_type, value, http):
        return ProbeResult(
            source=self.name,
            identifier=value,
            identifier_type=identifier_type,
            status=self._status,
        )


class TestRegistry:
    def test_build_collectors_filters_unknown(self) -> None:
        names = ["github", "does-not-exist", "crt"]
        collectors = build_collectors(names)
        assert [c.name for c in collectors] == ["github", "crt"]

    def test_build_collectors_default(self) -> None:
        assert len(build_collectors()) == 7

    def test_plan_probes_pairs_by_type(self) -> None:
        username = Identity(type=IdentityType.USERNAME, value="octopus")
        domain = Identity(type=IdentityType.DOMAIN, value="example.com")
        domain_only = _StubCollector()
        domain_only.supported_identifiers = frozenset({IdentityType.DOMAIN})
        probes = plan_probes([username, domain], [domain_only])
        assert len(probes) == 1
        identity, collector = probes[0]
        assert collector is domain_only
        assert identity.value == "example.com"

    def test_run_scan_reports_progress_and_errors(self) -> None:
        class BoomCollector(_StubCollector):
            def probe(self, identifier_type, value, http):
                raise RuntimeError("network exploded")

        identity = Identity(type=IdentityType.USERNAME, value="octopus")
        probes = [
            (identity, _StubCollector(status=ProbeStatus.NOT_FOUND)),
            (identity, BoomCollector()),
            (identity, _StubCollector()),
        ]
        seen: list[str] = []
        outcomes = run_scan(
            probes, http=object(), progress=lambda o: seen.append(o.status)
        )
        assert [o.status for o in outcomes] == ["NOT_FOUND", "ERROR", "FOUND"]
        assert seen == ["NOT_FOUND", "ERROR", "FOUND"]
        assert outcomes[1].error == "network exploded"

    def test_run_scan_cancel(self) -> None:
        identity = Identity(type=IdentityType.USERNAME, value="octopus")
        probes = [(identity, _StubCollector()) for _ in range(3)]
        outcomes = run_scan(probes, http=object(), cancel=lambda: True)
        assert outcomes == []
