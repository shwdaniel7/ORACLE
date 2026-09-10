"""Shared HTTP client used by collectors.

Wraps httpx with sane timeouts, redirect handling and a descriptive
User-Agent. A transport can be injected for tests.
"""

from __future__ import annotations

import httpx

DEFAULT_TIMEOUT = 10.0

_DEFAULT_USER_AGENT = (
    "ORACLE-OPSEC/0.2 (+https://github.com/shwdaniel7/ORACLE; self-assessment only)"
)


class HttpClient:
    """Thin httpx wrapper with timeouts and redirect handling."""

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent or _DEFAULT_USER_AGENT},
            transport=transport,
        )

    def get(self, url: str) -> httpx.Response | None:
        """GET a URL; returns ``None`` on any transport-level error."""
        try:
            return self._client.get(url)
        except httpx.HTTPError:
            return None

    def close(self) -> None:
        self._client.close()
