"""GitHub username collector (public REST API)."""

from __future__ import annotations

from urllib.parse import quote

from oracle.collectors.base import BaseCollector, ProbeResult, ProbeStatus
from oracle.collectors.http import HttpClient
from oracle.models import IdentityType

_API_URL = "https://api.github.com"


class GitHubCollector(BaseCollector):
    """Probes the public GitHub profile for a username."""

    name = "github"
    display_name = "GitHub"
    description = "Public GitHub profile via the REST API (one request per username)."
    supported_identifiers = frozenset({IdentityType.USERNAME})
    reliability = 1.0

    def probe(
        self,
        identifier_type: IdentityType,
        value: str,
        http: HttpClient,
    ) -> ProbeResult:
        api_url = f"{_API_URL}/users/{quote(value)}"
        response = http.get(api_url)
        if response is None:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=api_url, error_message="request failed",
            )

        status = response.status_code
        if status == 404:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.NOT_FOUND, url=api_url
            )
        if status in (403, 429):
            return self._fallback_profile(identifier_type, value, http, api_url)
        if status != 200:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=api_url, error_message=f"unexpected status {status}",
            )

        profile = response.json()
        snippet_parts = [
            part
            for part in (profile.get("bio"), profile.get("location"))
            if isinstance(part, str) and part
        ]
        snippet = (
            " ".join(snippet_parts)
            if snippet_parts
            else f"@{value} has a public GitHub profile"
        )
        return ProbeResult(
            self.name,
            value,
            identifier_type,
            ProbeStatus.FOUND,
            url=f"https://github.com/{quote(value)}",
            title=f"@{value} on GitHub",
            snippet=snippet,
        )

    def _fallback_profile(
        self,
        identifier_type: IdentityType,
        value: str,
        http: HttpClient,
        api_url: str,
    ) -> ProbeResult:
        """Verify presence via the profile page when the API is rate limited."""
        profile_url = f"https://github.com/{quote(value)}"
        fallback = http.get(profile_url)
        if fallback is None:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=api_url, error_message="rate limited by source",
            )
        if fallback.status_code == 200:
            return ProbeResult(
                self.name,
                value,
                identifier_type,
                ProbeStatus.FOUND,
                url=profile_url,
                title=f"@{value} on GitHub",
                snippet=f"@{value} has a public GitHub profile",
            )
        if fallback.status_code == 404:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.NOT_FOUND,
                url=profile_url,
            )
        return ProbeResult(
            self.name, value, identifier_type, ProbeStatus.ERROR,
            url=api_url,
            error_message=f"rate limited by source (fallback status {fallback.status_code})",
        )
