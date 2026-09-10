"""Certificate transparency collector (crt.sh) for a domain."""

from __future__ import annotations

from urllib.parse import quote

from oracle.collectors.base import BaseCollector, ProbeResult, ProbeStatus
from oracle.collectors.http import HttpClient
from oracle.models import IdentityType


class CrtCollector(BaseCollector):
    """Probes certificate transparency records for a domain via crt.sh."""

    name = "crt"
    display_name = "crt.sh"
    description = "Certificate transparency records for a domain (crt.sh)."
    supported_identifiers = frozenset({IdentityType.DOMAIN})
    reliability = 1.0

    def probe(
        self,
        identifier_type: IdentityType,
        value: str,
        http: HttpClient,
    ) -> ProbeResult:
        query = quote(f"%{value}", safe="")
        search_url = f"https://crt.sh/?q={query}&output=json"
        response = http.get(search_url)
        if response is None:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                url=search_url, error_message="request failed",
            )
        if response.status_code != 200:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.UNKNOWN,
                url=search_url, error_message=f"unexpected status {response.status_code}",
            )

        try:
            records = response.json()
        except ValueError:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.UNKNOWN,
                url=search_url, error_message="source returned a non-JSON response",
            )
        if not isinstance(records, list) or not records:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.NOT_FOUND, url=search_url
            )

        names: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                continue
            name_value = record.get("name_value") or record.get("common_name")
            if isinstance(name_value, str):
                for line in name_value.splitlines():
                    if line.strip():
                        names.add(line.strip())
        if not names:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.NOT_FOUND, url=search_url
            )

        return ProbeResult(
            self.name,
            value,
            identifier_type,
            ProbeStatus.FOUND,
            url=search_url,
            title=f"{value} in certificate transparency logs",
            snippet=f"{len(names)} certificate name(s) observed",
        )
