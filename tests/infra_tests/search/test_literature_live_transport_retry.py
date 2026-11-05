"""Bounded retry and polite-pool identity for keyless literature HTTP workers.

These controls drive the supervised worker directly, so they exercise the real
request loop and the real metadata receipts without needing a live session.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.search.literature import live_transport
from infrastructure.search.literature.live_contract import LiteratureBlocked
from infrastructure.search.literature.live_providers import polite_pool_identity


def _worker(url: str, directory: Path, *, timeout_seconds: int = 60) -> int:
    return live_transport._http_worker(
        {"url": url, "allow_loopback": True, "timeout_seconds": timeout_seconds, "max_bytes": 4096},
        directory,
    )


def _metadata(directory: Path) -> dict:
    return json.loads((directory / "http.json").read_text())


def test_throttled_status_is_retried_within_the_request_budget(tmp_path, httpserver) -> None:
    """A transient 429 must not fail the gate; the retry is bounded and receipted."""
    responses = iter([429, 429, 200])

    def handler(_request):
        from werkzeug.wrappers import Response

        code = next(responses, 200)
        if code != 200:
            return Response(b"slow down", status=code, headers={"Retry-After": "0"})
        return Response(b'{"results": []}', status=200, content_type="application/json")

    httpserver.expect_request("/redirect-then-ok").respond_with_handler(handler)
    directory = tmp_path / "throttled"
    directory.mkdir()

    assert _worker(httpserver.url_for("/redirect-then-ok"), directory) == 0
    metadata = _metadata(directory)
    assert metadata["status"] == "passed" and metadata["status_code"] == 200
    assert [row["status_code"] for row in metadata["attempts"]] == [429, 429]


def test_persistent_throttling_still_blocks_after_a_bounded_number_of_attempts(tmp_path, httpserver) -> None:
    """Retrying is not a substitute for the provider: a real outage stays blocked."""
    httpserver.expect_request("/always-429").respond_with_data("slow down", status=429)
    directory = tmp_path / "persistent"
    directory.mkdir()

    with pytest.raises(LiteratureBlocked, match="returned status 429"):
        _worker(httpserver.url_for("/always-429"), directory)

    metadata = _metadata(directory)
    assert metadata["status"] == "blocked" and metadata["status_code"] == 429
    assert len(metadata["attempts"]) == live_transport._MAX_RETRY_ATTEMPTS


def test_unretryable_status_is_not_retried(tmp_path, httpserver) -> None:
    """Only the declared throttling statuses retry; a 404 fails on its first try."""
    httpserver.expect_request("/missing").respond_with_data("no such record", status=404)
    directory = tmp_path / "unretryable"
    directory.mkdir()

    with pytest.raises(LiteratureBlocked, match="returned status 404"):
        _worker(httpserver.url_for("/missing"), directory)
    assert _metadata(directory)["attempts"] == [{"attempt": 1, "status_code": 404}]


def test_a_retry_is_refused_when_it_would_exceed_a_one_second_budget(tmp_path, httpserver) -> None:
    """The retry cannot spend budget the caller did not grant."""
    httpserver.expect_request("/tight").respond_with_data("slow down", status=429)
    directory = tmp_path / "tight"
    directory.mkdir()

    with pytest.raises(LiteratureBlocked):
        _worker(httpserver.url_for("/tight"), directory, timeout_seconds=1)
    assert _metadata(directory)["attempts"] == [{"attempt": 1, "status_code": 429}]


@pytest.mark.parametrize("email", [None, "", "   ", "not-an-email", "has space@example.org"])
def test_absent_or_ineffective_contact_identity_stays_anonymous(email) -> None:
    """Never invent an address; an unusable one falls back to an honest UA only."""
    identity = polite_pool_identity(email)
    assert "mailto" not in identity
    assert identity["user_agent"].startswith("template-literature-acceptance/")


def test_declared_contact_identity_carries_mailto_and_user_agent() -> None:
    identity = polite_pool_identity("researcher@example.org")
    assert identity["mailto"] == "researcher@example.org"
    assert "mailto:researcher@example.org" in identity["user_agent"]
