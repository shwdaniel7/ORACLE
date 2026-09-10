"""OPSEC assessment engine."""

from __future__ import annotations

from oracle.opsec.recommendations import build_remediation_plan
from oracle.opsec.scoring import OPSECScore, score_findings

__all__ = ["OPSECScore", "build_remediation_plan", "score_findings"]
