"""Reddit username collector (public ``about.json`` endpoint)."""

from __future__ import annotations

from urllib.parse import quote

from oracle.collectors.base import BaseCollector, ProbeResult, ProbeStatus
from oracle.collectors.http import HttpClient
from oracle.models import IdentityType


class RedditCollector(BaseCollector):
    """Probes the public Reddit profile for a username."""

    name = "reddit"
    display_name = "Reddit"
    description = "Public Reddit profile via about.json (username)."
    supported_identifiers = frozenset({IdentityType.USERNAME})
    reliability = 1.0

    def probe(
        self,
        identifier_type: IdentityType,
        value: str,
        http: HttpClient,
    ) -> ProbeResult:
        encoded = quote(value, safe="")
        profile_url = f"https://www.reddit.com/user/{encoded}/about.json"
        response = http.get(profile_url)
        if response is None:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=profile_url, error_message="request failed",
            )

        status = response.status_code
        if status in (404, 410):
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.NOT_FOUND, url=profile_url
            )
        if status in (403, 429):
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=profile_url, error_message="rate limited by source",
            )
        if status != 200:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=profile_url, error_message=f"unexpected status {status}",
            )

        try:
            payload = response.json()
        except ValueError:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.UNKNOWN,
                url=profile_url, error_message="invalid response",
            )
        name = (payload or {}).get("data", {}).get("name")
        if not isinstance(name, str) or name.lower() != value.lower():
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.UNKNOWN,
                url=profile_url, error_message="inconclusive response",
            )
        return ProbeResult(
            self.name,
            value,
            identifier_type,
            ProbeStatus.FOUND,
            url=f"https://www.reddit.com/user/{encoded}/",
            title=f"u/{name} on Reddit",
        )
