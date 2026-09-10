"""DNS collector for a domain (stdlib resolver, offline)."""

from __future__ import annotations

import socket

from oracle.collectors.base import BaseCollector, ProbeResult, ProbeStatus
from oracle.collectors.http import HttpClient
from oracle.models import IdentityType


class DnsCollector(BaseCollector):
    """Probes whether a domain resolves to public A/AAAA records."""

    name = "dns"
    display_name = "DNS"
    description = "Public DNS resolution of a domain (A/AAAA) via the system resolver."
    supported_identifiers = frozenset({IdentityType.DOMAIN})
    reliability = 1.0

    def probe(
        self,
        identifier_type: IdentityType,
        value: str,
        http: HttpClient,
    ) -> ProbeResult:
        try:
            infos = socket.getaddrinfo(value, None)
        except socket.gaierror as exc:
            if exc.errno == socket.EAI_NONAME:
                return ProbeResult(
                    self.name, value, identifier_type, ProbeStatus.NOT_FOUND
                )
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                error_message=f"resolution failed: {exc}",
            )
        except OSError as exc:
            return ProbeResult(
                self.name, value, identifier_type, ProbeStatus.ERROR,
                error_message=str(exc),
            )

        addresses = sorted({str(info[4][0]) for info in infos})
        return ProbeResult(
            self.name,
            value,
            identifier_type,
            ProbeStatus.FOUND,
            title=f"{value} resolves publicly",
            snippet=", ".join(addresses) or "address records present",
        )
