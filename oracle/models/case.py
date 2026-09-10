"""Case domain model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from oracle.models.ids import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Case(BaseModel):
    """An assessment case representing one OPSEC investigation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=new_id)
    name: str = Field(min_length=1)
    description: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def to_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
