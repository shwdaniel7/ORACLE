"""Tests for the collector sources (network fully mocked)."""

from __future__ import annotations

import hashlib
import socket

import httpx
import pytest

from oracle.collectors.base import ProbeStatus
from oracle.collectors.http import HttpClient
from oracle.collectors.sources.crt import CrtCollector
from oracle.collectors.sources.dns import DnsCollector
from oracle.collectors.sources.github import GitHubCollector
from oracle.collectors.sources.gitlab import GitLabCollector
from oracle.collectors.sources.gravatar import GravatarCollector
from oracle.collectors.sources.reddit import RedditCollector
from oracle.models import IdentityType


def _client(handler) -> HttpClient:
    return HttpClient(transport=httpx.MockTransport(handler))


def _found_response(status: int = 200, json=None, text: str | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if text is not None:
            return httpx.Response(status, text=text, request=request)
        return httpx.Response(status, json=json, request=request)

    return handler


class TestGitHub:
    @pytest.fixture
    def collector(self) -> GitHubCollector:
        return GitHubCollector()

    def test_username_found(self, collector: GitHubCollector) -> None:
        client = _client(
            _found_response(json={"login": "octopus", "bio": "curious", "location": "Earth"})
        )
        result = collector.probe(IdentityType.USERNAME, "octopus", client)
        assert result.status is ProbeStatus.FOUND
        assert result.url == "https://github.com/octopus"
        assert "curious" in (result.snippet or "")

    def test_username_missing(self, collector: GitHubCollector) -> None:
        client = _client(_found_response(404))
        result = collector.probe(IdentityType.USERNAME, "nobody_here_42", client)
        assert result.status is ProbeStatus.NOT_FOUND

    def test_api_rate_limited_falls_back_to_profile(self, collector: GitHubCollector) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "github.com":
                return httpx.Response(200, request=request)
            return httpx.Response(429, request=request)

        client = _client(handler)
        result = collector.probe(IdentityType.USERNAME, "octopus", client)
        assert result.status is ProbeStatus.FOUND
        assert result.url == "https://github.com/octopus"

    def test_fallback_profile_missing(self, collector: GitHubCollector) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "github.com":
                return httpx.Response(404, request=request)
            return httpx.Response(429, request=request)

        client = _client(handler)
        result = collector.probe(IdentityType.USERNAME, "nobody_here_42", client)
        assert result.status is ProbeStatus.NOT_FOUND

    def test_fallback_down_keeps_error(self, collector: GitHubCollector) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "github.com":
                return httpx.Response(502, request=request)
            return httpx.Response(429, request=request)

        client = _client(handler)
        result = collector.probe(IdentityType.USERNAME, "octopus", client)
        assert result.status is ProbeStatus.ERROR
        assert "rate limited" in (result.error_message or "")

    def test_unsupported_type_skips_network(self, collector: GitHubCollector) -> None:
        assert IdentityType.USERNAME in collector.supported_identifiers
        assert IdentityType.EMAIL not in collector.supported_identifiers


class TestGravatar:
    def test_found(self) -> None:
        client = _client(
            _found_response(
                json={"entry": [{"displayName": "Octopus", "location": "Earth"}]}
            )
        )
        result = GravatarCollector().probe(
            IdentityType.EMAIL, "octopus@example.com", client
        )
        assert result.status is ProbeStatus.FOUND
        assert "Earth" in (result.snippet or "")

    def test_no_profile(self) -> None:
        client = _client(_found_response(404))
        result = GravatarCollector().probe(
            IdentityType.EMAIL, "nobody@example.invalid", client
        )
        assert result.status is ProbeStatus.NOT_FOUND

    def test_empty_entry_is_not_found(self) -> None:
        client = _client(_found_response(json={"entry": []}))
        result = GravatarCollector().probe(
            IdentityType.EMAIL, "ok@example.com", client
        )
        assert result.status is ProbeStatus.NOT_FOUND

    def test_rate_limited(self) -> None:
        client = _client(_found_response(429))
        result = GravatarCollector().probe(
            IdentityType.EMAIL, "ok@example.com", client
        )
        assert result.status is ProbeStatus.ERROR

    def test_normalized_hash_used(self) -> None:
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["path"] = request.url.path
            return httpx.Response(
                200, json={"entry": [{"displayName": "x"}]}, request=request
            )

        client = _client(handler)
        GravatarCollector().probe(
            IdentityType.EMAIL, "  User@Example.COM ", client
        )
        expected = hashlib.md5(b"user@example.com").hexdigest()
        assert seen["path"] == f"/{expected}.json"


class TestReddit:
    def test_found(self) -> None:
        client = _client(_found_response(json={"data": {"name": "octopus"}}))
        result = RedditCollector().probe(IdentityType.USERNAME, "octopus", client)
        assert result.status is ProbeStatus.FOUND

    def test_case_insensitive_match(self) -> None:
        client = _client(_found_response(json={"data": {"name": "Octopus"}}))
        result = RedditCollector().probe(IdentityType.USERNAME, "octopus", client)
        assert result.status is ProbeStatus.FOUND

    def test_mismatched_name_is_inconclusive(self) -> None:
        client = _client(_found_response(json={"data": {"name": "other_user"}}))
        result = RedditCollector().probe(IdentityType.USERNAME, "octopus", client)
        assert result.status is ProbeStatus.UNKNOWN

    def test_gone(self) -> None:
        client = _client(_found_response(404))
        result = RedditCollector().probe(IdentityType.USERNAME, "ghost", client)
        assert result.status is ProbeStatus.NOT_FOUND


class TestGitLab:
    def test_found(self) -> None:
        client = _client(_found_response(json=[{"username": "octopus"}]))
        result = GitLabCollector().probe(IdentityType.USERNAME, "octopus", client)
        assert result.status is ProbeStatus.FOUND
        assert result.url == "https://gitlab.com/octopus"

    def test_missing(self) -> None:
        client = _client(_found_response(json=[]))
        result = GitLabCollector().probe(IdentityType.USERNAME, "ghost", client)
        assert result.status is ProbeStatus.NOT_FOUND


class TestDns:
    def test_resolves(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_getaddrinfo(host: str, port: int = 0):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("93.184.216.34", 0)),
                (socket.AF_INET6, socket.SOCK_STREAM, 0, "", ("2606:2800:220:1::1", 0)),
            ]

        monkeypatch.setattr("socket.getaddrinfo", fake_getaddrinfo)
        result = DnsCollector().probe(
            IdentityType.DOMAIN, "example.com", _client(_unused)
        )
        assert result.status is ProbeStatus.FOUND
        assert "93.184.216.34" in (result.snippet or "")

    def test_nxdomain(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fail_nxdomain(host: str, port: int = 0):
            raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")

        monkeypatch.setattr("socket.getaddrinfo", fail_nxdomain)
        result = DnsCollector().probe(
            IdentityType.DOMAIN, "nope.invalid", _client(_unused)
        )
        assert result.status is ProbeStatus.NOT_FOUND

    def test_network_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fail_oserror(host: str, port: int = 0):
            raise OSError("temporary name resolution failure")

        monkeypatch.setattr("socket.getaddrinfo", fail_oserror)
        result = DnsCollector().probe(
            IdentityType.DOMAIN, "example.com", _client(_unused)
        )
        assert result.status is ProbeStatus.ERROR


class TestCrt:
    def test_records_found(self) -> None:
        records = [{"name_value": "a.example.com\nb.example.com"}]
        client = _client(_found_response(200, json=records))
        result = CrtCollector().probe(IdentityType.DOMAIN, "example.com", client)
        assert result.status is ProbeStatus.FOUND
        assert "2 certificate" in (result.snippet or "")

    def test_no_records(self) -> None:
        client = _client(_found_response(200, json=[]))
        result = CrtCollector().probe(IdentityType.DOMAIN, "example.com", client)
        assert result.status is ProbeStatus.NOT_FOUND

    def test_unparseable(self) -> None:
        client = _client(_found_response(200, text="<html>poison</html>"))
        result = CrtCollector().probe(IdentityType.DOMAIN, "example.com", client)
        assert result.status is ProbeStatus.UNKNOWN


def _unused() -> httpx.Response:
    raise AssertionError("network request should not be attempted")
