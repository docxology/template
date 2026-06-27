#!/usr/bin/env python3
"""Tests for infrastructure.publishing.credential_check.

No mocks: a real local HTTP server (pytest-httpserver) stands in for the
provider APIs, and probes are redirected to it via ``override_base``.
"""

from __future__ import annotations

from pytest_httpserver import HTTPServer

from infrastructure.publishing.credential_check import (
    PROBES,
    ProbeResult,
    check_all,
    format_results,
    main,
    run_probe,
)


def _probe(name: str):
    return next(p for p in PROBES if p.name == name)


def test_skipped_when_no_token() -> None:
    result = run_probe(_probe("github"), env={})
    assert result.status == "skipped"
    assert not result.ok
    assert "GITHUB_TOKEN" in result.detail


def test_pypi_has_no_endpoint() -> None:
    result = run_probe(_probe("pypi"), env={"PYPI_TOKEN": "pypi-abc"})
    assert result.status == "no-endpoint"
    assert result.http_status is None


def test_pass_with_identity(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/user").respond_with_json({"login": "docxology"})
    result = run_probe(
        _probe("github"),
        env={"GITHUB_TOKEN": "tok"},
        override_base=httpserver.url_for("/"),
    )
    assert result.status == "pass"
    assert result.ok
    assert result.identity == "docxology"
    assert result.http_status == 200
    assert result.env_var == "GITHUB_TOKEN"


def test_fail_on_401(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/user").respond_with_json({"message": "Bad credentials"}, status=401)
    result = run_probe(
        _probe("github"),
        env={"GITHUB_TOKEN": "bad"},
        override_base=httpserver.url_for("/"),
    )
    assert result.status == "fail"
    assert result.http_status == 401
    assert "Bad credentials" in result.detail


def test_nested_identity_path(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/v2/users/me/").respond_with_json(
        {"data": {"attributes": {"full_name": "Daniel Friedman"}}}
    )
    result = run_probe(
        _probe("osf"),
        env={"OSF_TOKEN": "tok"},
        override_base=httpserver.url_for("/"),
    )
    assert result.status == "pass"
    assert result.identity == "Daniel Friedman"


def test_list_payload_identity(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/api/deposit/depositions").respond_with_json([{"id": 1}])
    result = run_probe(
        _probe("zenodo"),
        env={"ZENODO_PROD_TOKEN": "tok"},
        override_base=httpserver.url_for("/"),
    )
    assert result.status == "pass"
    assert result.identity == "1 item(s) visible"
    assert result.env_var == "ZENODO_PROD_TOKEN"


def test_check_all_only_filter() -> None:
    results = check_all(env={}, only=["github", "osf"])
    assert {r.name for r in results} == {"github", "osf"}
    assert all(isinstance(r, ProbeResult) for r in results)


def test_format_results_summarizes() -> None:
    results = [
        ProbeResult("github", "pass", 200, "docxology", "GITHUB_TOKEN", "ok"),
        ProbeResult("osf", "fail", 401, None, "OSF_TOKEN", "Unauthorized"),
        ProbeResult("pypi", "no-endpoint", None, None, None, "n/a"),
    ]
    text = format_results(results)
    assert "✅" in text and "❌" in text
    assert "1 passed, 1 failed" in text


def test_main_returns_zero_when_all_skipped(capsys) -> None:
    # An env with no publishing tokens -> everything skipped/no-endpoint -> rc 0.
    import infrastructure.publishing.credential_check as mod

    original = mod.os.environ
    try:
        mod.os.environ = {}  # type: ignore[assignment]
        rc = main([])
    finally:
        mod.os.environ = original  # type: ignore[assignment]
    assert rc == 0
    assert "credential check" in capsys.readouterr().out.lower()
