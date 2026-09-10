"""Evidence domain model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from oracle.models.ids import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(BaseModel):
    """A piece of observed information supporting a finding or relationship."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=new_id)
    source: str = Field(min_length=1)
    url: str | None = None
    observed_data: str = ""
    collected_at: datetime = Field(default_factory=_utcnow)
    finding_id: str | None = None
    relationship_id: str | None = None

    def to_summary(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "url": self.url,
            "observed_data": self.observed_data,
            "collected_at": self.collected_at,
        }
