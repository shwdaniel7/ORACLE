"""Local case management for ORACLE assessments."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from oracle.config import OracleConfig
from oracle.database.engine import create_db_engine, init_db
from oracle.database.orm_models import (
    CaseRecord,
    EvidenceRecord,
    FindingRecord,
    IdentityRecord,
    RelationshipRecord,
)
from oracle.models import (
    Case,
    Confidence,
    Evidence,
    Finding,
    Identity,
    IdentityType,
    Relationship,
    Severity,
)
from oracle.models.ids import new_id
from oracle.opsec.recommendations import build_remediation_plan
from oracle.opsec.scoring import OPSECScore, score_findings
from oracle.reports.generator import AssessmentBundle

_CASE_LOADS = (
    selectinload(CaseRecord.identities),
    selectinload(CaseRecord.findings).selectinload(FindingRecord.evidence),
    selectinload(CaseRecord.relationships).selectinload(RelationshipRecord.evidence),
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CaseManager:
    """CRUD operations over locally stored assessment cases."""

    def __init__(self, config: OracleConfig) -> None:
        self.config = config
        self.engine: Engine = create_db_engine(config.database_path)
        init_db(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def create_case(self, name: str, description: str | None = None) -> Case:
        now = _utcnow()
        record = CaseRecord(
            id=new_id(),
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )
        with self.session_factory() as session:
            session.add(record)
            session.commit()
        return _case_from_record(record)

    def list_cases(self) -> list[Case]:
        with self.session_factory() as session:
            records = session.scalars(
                select(CaseRecord).options(*_CASE_LOADS).order_by(CaseRecord.created_at)
            ).all()
            return [_case_from_record(r) for r in records]

    def get_case(self, case_id: str) -> Case:
        with self.session_factory() as session:
            record = _get_case_record(session, case_id)
            return _case_from_record(record)

    def delete_case(self, case_id: str) -> None:
        with self.session_factory() as session:
            record = _get_case_record(session, case_id)
            session.delete(record)
            session.commit()

    def add_identity(self, case_id: str, identity: Identity) -> Identity:
        with self.session_factory() as session:
            _get_case_record(session, case_id)
            record = _identity_to_record(identity, case_id)
            session.add(record)
            session.commit()
            identity.case_id = case_id
        return identity

    def list_identities(self, case_id: str) -> list[Identity]:
        with self.session_factory() as session:
            _get_case_record(session, case_id)
            records = session.scalars(
                select(IdentityRecord)
                .where(IdentityRecord.case_id == case_id)
                .order_by(IdentityRecord.value)
            ).all()
            return [_identity_from_record(r) for r in records]

    def add_finding(self, case_id: str, finding: Finding) -> Finding:
        with self.session_factory() as session:
            _get_case_record(session, case_id)
            record = _finding_to_record(finding, case_id)
            record.evidence = [
                _evidence_to_record(e, finding_id=finding.id) for e in finding.evidence
            ]
            session.add(record)
            session.commit()
            finding.case_id = case_id
        return finding

    def list_findings(self, case_id: str) -> list[Finding]:
        with self.session_factory() as session:
            _get_case_record(session, case_id)
            records = session.scalars(
                select(FindingRecord)
                .options(selectinload(FindingRecord.evidence))
                .where(FindingRecord.case_id == case_id)
                .order_by(FindingRecord.timestamp)
            ).all()
            return [_finding_from_record(r) for r in records]

    def add_relationship(
        self, case_id: str, relationship: Relationship
    ) -> Relationship:
        with self.session_factory() as session:
            _get_case_record(session, case_id)
            record = _relationship_to_record(relationship, case_id)
            record.evidence = [
                _evidence_to_record(e, relationship_id=relationship.id)
                for e in relationship.evidence
            ]
            session.add(record)
            session.commit()
            relationship.case_id = case_id
        return relationship

    def list_relationships(self, case_id: str) -> list[Relationship]:
        with self.session_factory() as session:
            _get_case_record(session, case_id)
            records = session.scalars(
                select(RelationshipRecord)
                .options(selectinload(RelationshipRecord.evidence))
                .where(RelationshipRecord.case_id == case_id)
                .order_by(RelationshipRecord.relationship_type)
            ).all()
            return [_relationship_from_record(r) for r in records]

    def build_bundle(self, case_id: str) -> AssessmentBundle:
        case = self.get_case(case_id)
        identities = self.list_identities(case_id)
        findings = self.list_findings(case_id)
        relationships = self.list_relationships(case_id)
        score: OPSECScore = score_findings(findings)
        remediation = build_remediation_plan(findings)
        return AssessmentBundle(
            case=case,
            identities=identities,
            findings=findings,
            relationships=relationships,
            score=score,
            remediation=remediation,
        )


def _get_case_record(session: Session, case_id: str) -> CaseRecord:
    record = session.scalars(
        select(CaseRecord).options(*_CASE_LOADS).where(CaseRecord.id == case_id)
    ).one_or_none()
    if record is None:
        raise KeyError(f"case not found: {case_id}")
    return record


def _identity_to_record(identity: Identity, case_id: str) -> IdentityRecord:
    return IdentityRecord(
        id=identity.id,
        case_id=case_id,
        type=identity.type.value,
        value=identity.value,
        label=identity.label,
    )


def _identity_from_record(record: IdentityRecord) -> Identity:
    return Identity(
        id=record.id,
        case_id=record.case_id,
        type=IdentityType(record.type),
        value=record.value,
        label=record.label,
    )


def _evidence_to_record(
    evidence: Evidence,
    finding_id: str | None = None,
    relationship_id: str | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        id=evidence.id,
        finding_id=finding_id,
        relationship_id=relationship_id,
        source=evidence.source,
        url=evidence.url,
        observed_data=evidence.observed_data,
        collected_at=evidence.collected_at,
    )


def _evidence_from_record(record: EvidenceRecord) -> Evidence:
    return Evidence(
        id=record.id,
        source=record.source,
        url=record.url,
        observed_data=record.observed_data,
        collected_at=record.collected_at,
        finding_id=record.finding_id,
        relationship_id=record.relationship_id,
    )


def _finding_to_record(finding: Finding, case_id: str) -> FindingRecord:
    return FindingRecord(
        id=finding.id,
        case_id=case_id,
        category=finding.category,
        severity=finding.severity.value,
        confidence=finding.confidence.value,
        description=finding.description,
        recommendation=finding.recommendation,
        timestamp=finding.timestamp,
    )


def _finding_from_record(record: FindingRecord) -> Finding:
    return Finding(
        id=record.id,
        case_id=record.case_id,
        category=record.category,
        severity=Severity(record.severity),
        confidence=Confidence(record.confidence),
        description=record.description,
        recommendation=record.recommendation,
        timestamp=record.timestamp,
        evidence=[_evidence_from_record(e) for e in record.evidence],
    )


def _relationship_to_record(
    relationship: Relationship, case_id: str
) -> RelationshipRecord:
    return RelationshipRecord(
        id=relationship.id,
        case_id=case_id,
        identity_a_id=relationship.identity_a_id,
        identity_b_id=relationship.identity_b_id,
        relationship_type=relationship.relationship_type,
        confidence=relationship.confidence.value,
        notes=relationship.notes,
    )


def _relationship_from_record(record: RelationshipRecord) -> Relationship:
    return Relationship(
        id=record.id,
        case_id=record.case_id,
        identity_a_id=record.identity_a_id,
        identity_b_id=record.identity_b_id,
        relationship_type=record.relationship_type,
        confidence=Confidence(record.confidence),
        notes=record.notes,
        evidence=[_evidence_from_record(e) for e in record.evidence],
    )


def _case_from_record(record: CaseRecord) -> Case:
    return Case(
        id=record.id,
        name=record.name,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
