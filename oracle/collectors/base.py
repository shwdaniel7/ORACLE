"""Abstractions for public-information collectors (Phase 2 · Discover).

Collectors probe user-owned identifiers against public sources. Design
rules, per the project spec:

- **Modular**: one collector per source, self-contained.
- **Limited**: presence-only probes, respect rate limits, cancellable.
- **Source-conscious**: ambiguous responses are never turned into facts.
- **Evidence-based**: findings are recorded only with supporting evidence;
  ``NOT_FOUND`` must never be interpreted as "does not exist".
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from oracle.collectors.http import HttpClient
from oracle.models import IdentityType


class ProbeStatus(str, Enum):
    """Outcome of probing one identifier against one source."""

    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


@dataclass
class ProbeResult:
    """Structured outcome of a single source probe."""

    source: str
    identifier: str
    identifier_type: IdentityType
    status: ProbeStatus
    url: str | None = None
    title: str | None = None
    snippet: str | None = None
    error_message: str | None = None

    @property
    def found(self) -> bool:
        return self.status is ProbeStatus.FOUND


class BaseCollector(ABC):
    """Contract for a public-information collector.

    A collector owns exactly one public source and answers one question
    per probe: does this identifier correspond to observable public
    information on that source?
    """

    name: str = "base"
    display_name: str = "Base"
    description: str = ""
    supported_identifiers: frozenset[IdentityType] = frozenset()
    reliability: float = 1.0

    @abstractmethod
    def probe(
        self,
        identifier_type: IdentityType,
        value: str,
        http: HttpClient,
    ) -> ProbeResult:
        """Probe a single identifier and report what was observed."""
