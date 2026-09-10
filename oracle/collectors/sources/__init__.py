"""Concrete public-information collectors (one module per source)."""

from __future__ import annotations

from oracle.collectors.sources.crt import CrtCollector
from oracle.collectors.sources.dns import DnsCollector
from oracle.collectors.sources.github import GitHubCollector
from oracle.collectors.sources.gitlab import GitLabCollector
from oracle.collectors.sources.gravatar import GravatarCollector
from oracle.collectors.sources.reddit import RedditCollector

__all__ = [
    "CrtCollector",
    "DnsCollector",
    "GitHubCollector",
    "GitLabCollector",
    "GravatarCollector",
    "RedditCollector",
]
