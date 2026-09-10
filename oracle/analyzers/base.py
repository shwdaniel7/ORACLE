"""Base abstractions for analyzers.

Analyzers will be introduced during Phases 2 and 3. This module only
defines the contract they must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from oracle.models import Finding


class BaseAnalyzer(ABC):
    """Contract for an analyzer that produces findings."""

    name: str = "base"

    @abstractmethod
    def analyze(self, case_id: str, context: object) -> list[Finding]:
        """Analyze an investigation context and return findings."""
