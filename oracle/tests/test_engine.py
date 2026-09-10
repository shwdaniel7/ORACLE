"""End-to-end tests for the assessment engine."""

from __future__ import annotations

from oracle.collectors.base import BaseCollector, ProbeResult, ProbeStatus
from oracle.collectors.registry import _COLLECTOR_TYPES
from oracle.models import Identity, IdentityType
from oracle.services.engine import AssessmentEngine


class _FoundCollector(BaseCollector):
    """Deterministic collector that always finds a public profile."""

    name = "fake_found"
    display_name = "Fake Found"
    description = "test collector"
    supported_identifiers = frozenset({IdentityType.USERNAME, IdentityType.DOMAIN})
    reliability = 1.0

    def probe(self, identifier_type, value, http):
        return ProbeResult(
            source=self.name,
            identifier=value,
            identifier_type=identifier_type,
            status=ProbeStatus.FOUND,
            url=f"https://fake.local/{value}",
            title=f"{value} on Fake",
        )


class _MissingCollector(BaseCollector):
    name = "fake_missing"
    display_name = "Fake Missing"
    description = "test collector that finds nothing"
    supported_identifiers = frozenset({IdentityType.USERNAME})
    reliability = 1.0

    def probe(self, identifier_type, value, http):
        return ProbeResult(
            source=self.name,
            identifier=value,
            identifier_type=identifier_type,
            status=ProbeStatus.NOT_FOUND,
        )


class _FoundCollector2(_FoundCollector):
    name = "fake_found2"
    display_name = "Fake Found 2"


def _install_fakes(monkeypatch) -> None:
    monkeypatch.setitem(_COLLECTOR_TYPES, "fake_found", _FoundCollector)
    monkeypatch.setitem(_COLLECTOR_TYPES, "fake_found2", _FoundCollector2)
    monkeypatch.setitem(_COLLECTOR_TYPES, "fake_missing", _MissingCollector)


def _engine(manager):
    return AssessmentEngine(config=manager.config, manager=manager)


class TestEngine:
    def test_scan_creates_and_dedups_findings(self, manager, monkeypatch) -> None:
        _install_fakes(monkeypatch)
        case = manager.create_case("Audit")
        manager.add_identity(
            case.id, Identity(type=IdentityType.USERNAME, value="octopus")
        )
        engine = _engine(manager)

        created = engine.scan(case.id, collector_names=["fake_found"])
        assert len(created) == 1
        assert created[0].category == "Username Reuse"
        assert len(manager.list_findings(case.id)) == 1

        second = engine.scan(case.id, collector_names=["fake_found"])
        assert second == []
        assert len(manager.list_findings(case.id)) == 1

    def test_non_found_probes_do_not_create_findings(self, manager, monkeypatch) -> None:
        _install_fakes(monkeypatch)
        case = manager.create_case("Audit")
        manager.add_identity(
            case.id, Identity(type=IdentityType.USERNAME, value="ghost")
        )
        engine = _engine(manager)
        created = engine.scan(case.id, collector_names=["fake_missing"])
        assert created == []
        assert manager.list_findings(case.id) == []

    def test_scan_and_analyze_drive_correlation_risk(self, manager, monkeypatch) -> None:
        _install_fakes(monkeypatch)
        case = manager.create_case("Audit")
        manager.add_identity(
            case.id, Identity(type=IdentityType.USERNAME, value="octopus")
        )
        engine = _engine(manager)
        engine.scan(case.id, collector_names=["fake_found", "fake_found2"])

        relationships = engine.analyze(case.id)
        assert len(relationships) == 1
        assert relationships[0].relationship_type == "same_username"

        again = engine.analyze(case.id)
        assert again == []
        assert len(manager.list_relationships(case.id)) == 1
        assert len(manager.list_identities(case.id)) == 2  # username + public handle

        finding_count = len(manager.list_findings(case.id))
        assert finding_count == 3  # two username findings + one correlation

    def test_run_assessment_end_to_end(self, manager, monkeypatch) -> None:
        _install_fakes(monkeypatch)
        case = manager.create_case("Audit")
        manager.add_identity(
            case.id, Identity(type=IdentityType.USERNAME, value="octopus")
        )
        engine = _engine(manager)
        bundle = engine.run_assessment(
            case.id, collector_names=["fake_found", "fake_found2"]
        )
        assert bundle.score.overall > 0
        assert len(bundle.findings) == 3
        assert len(bundle.relationships) == 1
