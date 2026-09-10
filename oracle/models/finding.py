"""Finding domain model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from oracle.models.enums import Confidence, Severity
from oracle.models.evidence import Evidence
from oracle.models.ids import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Finding(BaseModel):
    """A structured OPSEC finding with evidence and context."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=new_id)
    case_id: str | None = None
    category: str = Field(min_length=1)
    severity: Severity
    confidence: Confidence
    description: str = Field(min_length=1)
    evidence: list[Evidence] = Field(default_factory=list)
    recommendation: str | None = None
    timestamp: datetime = Field(default_factory=_utcnow)

    def to_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "description": self.description,
            "evidence": [e.to_summary() for e in self.evidence],
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }
