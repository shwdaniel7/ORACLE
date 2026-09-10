"""Base abstractions for information collectors.

Collectors will be introduced during Phase 2 (Exposure Discovery). This
module only defines the contract they must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from oracle.models import IdentityType


@dataclass
class CollectionResult:
    """Raw information collected from a public source."""

    source: str
    data: str
    url: str | None = None


class BaseCollector(ABC):
    """Contract for a public-information collector."""

    name: str = "base"
    supported_identifiers: frozenset[IdentityType] = frozenset()

    @abstractmethod
    def collect(self, identifier: str) -> list[CollectionResult]:
        """Collect publicly accessible information for an identifier."""
