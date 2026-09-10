"""Relationship domain model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from oracle.models.enums import Confidence
from oracle.models.evidence import Evidence
from oracle.models.ids import new_id


class Relationship(BaseModel):
    """A relationship between two identities within an identity graph."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=new_id)
    case_id: str | None = None
    identity_a_id: str = Field(min_length=1)
    identity_b_id: str = Field(min_length=1)
    relationship_type: str = Field(min_length=1)
    confidence: Confidence
    evidence: list[Evidence] = Field(default_factory=list)
    notes: str | None = None

    def to_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "identity_a_id": self.identity_a_id,
            "identity_b_id": self.identity_b_id,
            "relationship_type": self.relationship_type,
            "confidence": self.confidence.value,
            "evidence": [e.to_summary() for e in self.evidence],
            "notes": self.notes,
        }
