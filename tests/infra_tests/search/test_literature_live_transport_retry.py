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
    assert [(row["attempt"], row["status_code"]) for row in _metadata(directory)["attempts"]] == [(1, 404)]


def test_a_retry_is_refused_when_it_would_exceed_a_one_second_budget(tmp_path, httpserver) -> None:
    """The retry cannot spend budget the caller did not grant."""
    httpserver.expect_request("/tight").respond_with_data("slow down", status=429)
    directory = tmp_path / "tight"
    directory.mkdir()

    with pytest.raises(LiteratureBlocked):
        _worker(httpserver.url_for("/tight"), directory, timeout_seconds=1)
    assert [(row["attempt"], row["status_code"]) for row in _metadata(directory)["attempts"]] == [(1, 429)]


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


def test_actual_error_quota_headers_are_retained_without_private_headers_or_body(tmp_path, httpserver) -> None:
    """Three genuine throttles stay blocked and retain only the five public fields."""
    offered = {
        "Retry-After": "0",
        "X-RateLimit-Limit": "100000",
        "x-ratelimit-remaining": "0",
        "X-RateLimit-Credits-Used": "12.25",
        "X-RateLimit-Reset": "1793923200",
        "Authorization": "Bearer PRIVATE_AUTH",
        "Set-Cookie": "PRIVATE_COOKIE",
        "X-Unrelated": "PRIVATE_UNRELATED",
    }
    httpserver.expect_request("/quota").respond_with_data("PRIVATE_BODY", status=429, headers=offered)
    directory = tmp_path / "quota"
    directory.mkdir()
    with pytest.raises(LiteratureBlocked, match="returned status 429"):
        _worker(httpserver.url_for("/quota"), directory)
    metadata = _metadata(directory)
    assert metadata["status"] == "blocked" and metadata["status_code"] == 429
    assert len(metadata["attempts"]) == 3
    for attempt in metadata["attempts"]:
        fields = attempt["error_response_headers"]
        assert set(fields) == {
            "Retry-After",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Credits-Used",
            "X-RateLimit-Reset",
        }
        assert fields["Retry-After"] == {"status": "observed", "value": "0", "format": "number"}
        assert fields["X-RateLimit-Remaining"]["value"] == "0"
        assert fields["X-RateLimit-Credits-Used"]["value"] == "12.25"
        assert fields["X-RateLimit-Reset"]["value"] == "1793923200"
    assert "PRIVATE_" not in json.dumps(metadata)
    assert not (directory / "body.bin").exists()


def test_actual_error_dates_and_absent_fields_are_observations_not_cooldown(tmp_path, httpserver) -> None:
    httpserver.expect_request("/dated").respond_with_data(
        "unavailable",
        status=404,
        headers={"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT", "X-RateLimit-Reset": "2026-11-06T00:00:00Z"},
    )
    directory = tmp_path / "dated"
    directory.mkdir()
    with pytest.raises(LiteratureBlocked, match="returned status 404"):
        _worker(httpserver.url_for("/dated"), directory)
    fields = _metadata(directory)["attempts"][0]["error_response_headers"]
    assert fields["Retry-After"] == {
        "status": "observed",
        "value": "Wed, 21 Oct 2015 07:28:00 GMT",
        "format": "http-date",
    }
    assert fields["X-RateLimit-Reset"] == {
        "status": "observed",
        "value": "2026-11-06T00:00:00Z",
        "format": "iso-date-time",
    }
    assert fields["X-RateLimit-Limit"] == {"status": "absent"}
    assert fields["X-RateLimit-Remaining"] == {"status": "absent"}
    assert fields["X-RateLimit-Credits-Used"] == {"status": "absent"}


def test_actual_error_duplicate_unsafe_oversized_and_invalid_fields_are_not_echoed(tmp_path, httpserver) -> None:
    from werkzeug.wrappers import Response

    def handler(_request):
        response = Response("PRIVATE_BODY", status=404)
        response.headers.add("X-RateLimit-Limit", "10")
        response.headers.add("X-RateLimit-Limit", "20")
        response.headers["Retry-After"] = "-1"
        response.headers["X-RateLimit-Remaining"] = "PRIVATE_UNSAFE"
        response.headers["X-RateLimit-Credits-Used"] = "9" * 65
        response.headers["X-RateLimit-Reset"] = "2026-99-06T00:00:00Z"
        return response

    httpserver.expect_request("/invalid").respond_with_handler(handler)
    directory = tmp_path / "invalid"
    directory.mkdir()
    with pytest.raises(LiteratureBlocked, match="returned status 404"):
        _worker(httpserver.url_for("/invalid"), directory)
    metadata = _metadata(directory)
    fields = metadata["attempts"][0]["error_response_headers"]
    assert fields["X-RateLimit-Limit"] == {"status": "unavailable", "reason": "multiple-values"}
    assert fields["X-RateLimit-Credits-Used"] == {
        "status": "unavailable",
        "reason": "invalid-or-oversized-value",
    }
    assert all(row["status"] == "unavailable" and "value" not in row for row in fields.values())
    assert "PRIVATE_" not in json.dumps(metadata)
    assert "9" * 65 not in json.dumps(metadata)


def test_unavailable_header_container_is_distinct_from_absent_error_fields(tmp_path, httpserver) -> None:
    """A genuine response with no quota fields differs from unavailable header metadata."""
    httpserver.expect_request("/no-fields").respond_with_data("unavailable", status=404)
    directory = tmp_path / "no-fields"
    directory.mkdir()
    with pytest.raises(LiteratureBlocked):
        _worker(httpserver.url_for("/no-fields"), directory)
    actual = _metadata(directory)["attempts"][0]["error_response_headers"]
    assert all(row == {"status": "absent"} for row in actual.values())
    unavailable = live_transport._error_header_observations(None)
    assert all(
        row == {"status": "unavailable", "reason": "response-headers-unavailable"} for row in unavailable.values()
    )


def test_transient_503_retains_error_headers_without_changing_the_success_outcome(tmp_path, httpserver) -> None:
    from werkzeug.wrappers import Response

    codes = iter((503, 200))

    def handler(_request):
        code = next(codes)
        return Response(
            b'{"results":[]}' if code == 200 else b"temporarily unavailable",
            status=code,
            headers={"Retry-After": "0"},
            content_type="application/json",
        )

    httpserver.expect_request("/temporary").respond_with_handler(handler)
    directory = tmp_path / "temporary"
    directory.mkdir()
    assert _worker(httpserver.url_for("/temporary"), directory) == 0
    metadata = _metadata(directory)
    assert metadata["status"] == "passed" and metadata["status_code"] == 200
    assert len(metadata["attempts"]) == 1 and metadata["attempts"][0]["status_code"] == 503
    assert metadata["attempts"][0]["error_response_headers"]["Retry-After"]["value"] == "0"
