"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from oracle.case.manager import CaseManager
from oracle.config import OracleConfig
from oracle.models import Confidence, Finding, Severity


@pytest.fixture
def config(tmp_path) -> OracleConfig:
    return OracleConfig(data_dir=tmp_path)


@pytest.fixture
def manager(config: OracleConfig) -> CaseManager:
    return CaseManager(config)


@pytest.fixture
def sample_finding() -> Finding:
    return Finding(
        category="Identity Correlation",
        severity=Severity.HIGH,
        confidence=Confidence.CONFIRMED,
        description="The same username is publicly associated with multiple identities.",
        recommendation="Separate identifiers between personal and public-facing identities.",
    )
