"""GitLab username collector (public API)."""

from __future__ import annotations

from urllib.parse import quote

from oracle.collectors.base import BaseCollector, ProbeResult, ProbeStatus
from oracle.collectors.http import HttpClient
from oracle.models import IdentityType

_API_URL = "https://gitlab.com/api/v4/users"


class GitLabCollector(BaseCollector):
    """Probes the public GitLab profile (or namespace) for a username."""

    name = "gitlab"
    display_name = "GitLab"
    description = "Public GitLab profile via the REST API (username)."
    supported_identifiers = frozenset({IdentityType.USERNAME})
    reliability = 1.0

    def probe(
        self,
        identifier_type: IdentityType,
        value: str,
        http: HttpClient,
    ) -> ProbeResult:
        encoded = quote(value, safe="")
        api_url = f"{_API_URL}?username={encoded}"
        response = http.get(api_url)
        if response is None:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=api_url, error_message="request failed",
            )

        status = response.status_code
        if status in (403, 429):
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=api_url, error_message="rate limited by source",
            )
        if status != 200:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=api_url, error_message=f"unexpected status {status}",
            )

        try:
            users = response.json()
        except ValueError:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.UNKNOWN,
                url=api_url, error_message="invalid response",
            )
        if isinstance(users, list) and users:
            return ProbeResult(
                self.name,
                value,
                identifier_type,
                ProbeStatus.FOUND,
                url=f"https://gitlab.com/{encoded}",
                title=f"@{value} on GitLab",
            )
        return ProbeResult(
            self.name, value, identifier_type, ProbeStatus.NOT_FOUND, url=api_url
        )
