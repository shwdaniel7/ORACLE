"""Gravatar email collector (public profile images service)."""

from __future__ import annotations

import hashlib
from urllib.parse import quote

from oracle.collectors.base import BaseCollector, ProbeResult, ProbeStatus
from oracle.collectors.http import HttpClient
from oracle.models import IdentityType


class GravatarCollector(BaseCollector):
    """Probes whether an email has a public Gravatar profile.

    Gravatar exposes a per-email JSON profile keyed by the MD5 hash of
    the normalized email address. The request reveals only the hash to
    the service, and presence is confirmed only when the payload contains
    an actual profile entry.
    """

    name = "gravatar"
    display_name = "Gravatar"
    description = "Public Gravatar profile associated with an email address (MD5 lookup)."
    supported_identifiers = frozenset({IdentityType.EMAIL})
    reliability = 1.0

    def probe(
        self,
        identifier_type: IdentityType,
        value: str,
        http: HttpClient,
    ) -> ProbeResult:
        normalized = value.strip().lower()
        digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
        api_url = f"https://www.gravatar.com/{digest}.json"
        response = http.get(api_url)
        if response is None:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=api_url, error_message="request failed",
            )

        status = response.status_code
        if status in (404, 410):
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.NOT_FOUND, url=api_url
            )
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
            payload = response.json()
        except ValueError:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.UNKNOWN,
                url=api_url, error_message="invalid response",
            )

        entries = (payload or {}).get("entry")
        if not isinstance(entries, list) or not entries:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.NOT_FOUND, url=api_url
            )

        profile = entries[0]
        snippet_parts: list[str] = []
        for key in ("displayName", "profileUrl", "aboutMe", "location"):
            part = profile.get(key)
            if isinstance(part, str) and part:
                snippet_parts.append(part)
        snippet = (
            " ".join(snippet_parts)
            if snippet_parts
            else "an email address is linked to a Gravatar profile"
        )
        return ProbeResult(
            self.name,
            value,
            identifier_type,
            ProbeStatus.FOUND,
            url=quote(profile.get("profileUrl") or api_url, safe="/:"),
            title=f"{normalized} linked to a Gravatar profile",
            snippet=snippet,
        )
