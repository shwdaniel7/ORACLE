"""SQLAlchemy ORM models for ORACLE persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oracle.database.base import Base


class CaseRecord(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    identities: Mapped[list[IdentityRecord]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    findings: Mapped[list[FindingRecord]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    relationships: Mapped[list[RelationshipRecord]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class IdentityRecord(Base):
    __tablename__ = "identities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(32))
    value: Mapped[str] = mapped_column(String(512))
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    case: Mapped[CaseRecord] = relationship(back_populates="identities")


class FindingRecord(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)

    case: Mapped[CaseRecord] = relationship(back_populates="findings")
    evidence: Mapped[list[EvidenceRecord]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )


class RelationshipRecord(Base):
    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    identity_a_id: Mapped[str] = mapped_column(String(32))
    identity_b_id: Mapped[str] = mapped_column(String(32))
    relationship_type: Mapped[str] = mapped_column(String(128))
    confidence: Mapped[str] = mapped_column(String(16))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped[CaseRecord] = relationship(back_populates="relationships")
    evidence: Mapped[list[EvidenceRecord]] = relationship(
        back_populates="relationship", cascade="all, delete-orphan"
    )


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    finding_id: Mapped[str | None] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    relationship_id: Mapped[str | None] = mapped_column(
        ForeignKey("relationships.id", ondelete="CASCADE"), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    observed_data: Mapped[str] = mapped_column(Text, default="")
    collected_at: Mapped[datetime] = mapped_column(DateTime)

    finding: Mapped[FindingRecord | None] = relationship(back_populates="evidence")
    relationship: Mapped[RelationshipRecord | None] = relationship(
        back_populates="evidence"
    )
