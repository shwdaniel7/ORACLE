"""Identity domain model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from oracle.models.enums import IdentityType
from oracle.models.ids import new_id


class Identity(BaseModel):
    """A digital identifier owned or used by the investigated user."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=new_id)
    case_id: str | None = None
    type: IdentityType
    value: str = Field(min_length=1)
    label: str | None = None

    def to_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "value": self.value,
            "label": self.label,
        }
