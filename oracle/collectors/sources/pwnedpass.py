"""Pwned Passwords breach check for passwords (k-anonymity, free).

The password SHA-1 is computed locally and only its first 5 hexadecimal
characters reach the service. The response is the full set of matching
hash suffixes with their breach counts; the comparison happens on this
machine, so the password and its complete hash never leave it.
"""

from __future__ import annotations

import hashlib

from oracle.collectors.base import BaseCollector, ProbeResult, ProbeStatus
from oracle.collectors.http import HttpClient
from oracle.models import IdentityType

_API = "https://api.pwnedpasswords.com/range/{prefix}"

_HEX = frozenset("0123456789abcdefABCDEF")


class PwnedPassCollector(BaseCollector):
    """Presence probe: has this password appeared in known breaches?"""

    name = "pwnedpass"
    display_name = "Pwned Passwords"
    description = (
        "Whether a password appears in breached data "
        "(free k-anonymity SHA-1 lookup)."
    )
    supported_identifiers = frozenset({IdentityType.PASSWORD})
    reliability = 1.0

    def probe(
        self,
        identifier_type: IdentityType,
        value: str,
        http: HttpClient,
    ) -> ProbeResult:
        raw = value.strip()
        if len(raw) == 40 and all(character in _HEX for character in raw):
            digest = raw.upper()
        else:
            digest = hashlib.sha1(raw.encode("utf-8")).hexdigest().upper()
        prefix, suffix = digest[:5], digest[5:]
        api_url = _API.format(prefix=prefix)
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

        occurrences = self._occurrences(response.text, suffix)
        if occurrences == 0:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.NOT_FOUND, url=api_url
            )
        return ProbeResult(
            self.name,
            value,
            identifier_type,
            ProbeStatus.FOUND,
            url="https://haveibeenpwned.com/Passwords",
            title="password appears in breached data",
            snippet=f"password exposed {occurrences} time(s) in known breaches",
        )

    @staticmethod
    def _occurrences(body: str, suffix: str) -> int:
        for line in body.splitlines():
            item_suffix, separator, count = line.partition(":")
            if separator and item_suffix.upper() == suffix and count.isdigit():
                return int(count)
        return 0
