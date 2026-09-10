"""Enumerations shared across ORACLE domain models."""

from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    """Severity of an OPSEC finding."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def rank(self) -> int:
        ranks = {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        return ranks[self]


class Confidence(str, Enum):
    """Confidence state of a finding.

    ``NOT_FOUND`` must never be interpreted as "does not exist".
    """

    CONFIRMED = "CONFIRMED"
    POSSIBLE = "POSSIBLE"
    INFERRED = "INFERRED"
    NOT_FOUND = "NOT_FOUND"


class IdentityType(str, Enum):
    """Kind of digital identifier."""

    USERNAME = "username"
    EMAIL = "email"
    DOMAIN = "domain"
    PROFILE = "profile"
    OTHER = "other"
