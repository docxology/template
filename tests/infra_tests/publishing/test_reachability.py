#!/usr/bin/env python3
"""Tests for infrastructure.publishing.reachability and --verify-reachability.

No mocks: every HTTP path is exercised against a real local
``pytest-httpserver`` instance, and negative controls assert the default
(offline) CLI path issues zero requests and renders byte-identical output.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.publishing.reachability import (
    STATUS_ERROR,
    STATUS_OK,
    STATUS_UNREACHABLE,
    ReachabilityCheck,
    apply_reachability,
    probe_url,
    verify_reachability,
)
from infrastructure.publishing.status_report import (
    PublicationState,
    compile_publishing_status,
    main,
    render_status_block,
    render_status_markdown,
)

CONFIG_YAML = """\
paper:
  title: "Search Project"
  version: "1.0.0"

publication:
  doi: "10.5281/zenodo.11111111"
  github_repository: "docxology/template_search_project"
  repository_url: "https://github.com/docxology/template_search_project"
"""


def _project(tmp_path: Path, config_text: str = CONFIG_YAML) -> Path:
    root = tmp_path / "proj"
    (root / "manuscript").mkdir(parents=True)
    (root / "manuscript" / "config.yaml").write_text(config_text, encoding="utf-8")
    return root


def _closed_port_url() -> str:
    """Return a URL on a port that was just released (connection refused)."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    return f"http://127.0.0.1:{port}/"


# ---------------------------------------------------------------------------
# probe_url
# ---------------------------------------------------------------------------


def test_probe_url_200_is_ok(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/ok").respond_with_data("fine")
    assert probe_url(httpserver.url_for("/ok")) == (STATUS_OK, "HTTP 200")


def test_probe_url_302_is_ok_and_redirect_not_followed(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/doi", method="HEAD").respond_with_data(
        status=302, headers={"Location": httpserver.url_for("/publisher")}
    )
    status, detail = probe_url(httpserver.url_for("/doi"), method="HEAD")
    assert (status, detail) == (STATUS_OK, "HTTP 302")
    # The redirect target must never be contacted.
    assert [req.path for req, _ in httpserver.log] == ["/doi"]


@pytest.mark.parametrize("code", [404, 410])
def test_probe_url_gone_codes_are_unreachable(httpserver: HTTPServer, code: int) -> None:
    httpserver.expect_request("/gone").respond_with_data(status=code)
    status, detail = probe_url(httpserver.url_for("/gone"))
    assert status == STATUS_UNREACHABLE
    assert detail == f"HTTP {code}"


@pytest.mark.parametrize("code", [403, 429, 500, 503])
def test_probe_url_other_failures_are_error_not_unreachable(httpserver: HTTPServer, code: int) -> None:
    httpserver.expect_request("/flaky").respond_with_data(status=code)
    status, detail = probe_url(httpserver.url_for("/flaky"))
    assert status == STATUS_ERROR
    assert detail == f"HTTP {code}"


def test_probe_url_connection_refused_is_error() -> None:
    status, detail = probe_url(_closed_port_url(), timeout=5.0)
    assert status == STATUS_ERROR
    assert detail.startswith("error: ")


def test_probe_url_rejects_non_http_scheme() -> None:
    assert probe_url("ftp://example.invalid/thing") == (STATUS_ERROR, "unsupported URL scheme")


# ---------------------------------------------------------------------------
# verify_reachability
# ---------------------------------------------------------------------------


def test_verify_reachability_probes_repo_and_doi(tmp_path: Path, httpserver: HTTPServer) -> None:
    httpserver.expect_request("/docxology/template_search_project", method="HEAD").respond_with_data("")
    httpserver.expect_request("/10.5281/zenodo.11111111", method="HEAD").respond_with_data(
        status=302, headers={"Location": "https://zenodo.org/records/11111111"}
    )
    report = compile_publishing_status(_project(tmp_path))
    checks = verify_reachability(
        report,
        github_base=httpserver.url_for(""),
        doi_base=httpserver.url_for(""),
    )
    by_platform = {c.platform: c for c in checks}
    assert by_platform["github"].status == STATUS_OK
    assert by_platform["github"].identifier == "docxology/template_search_project"
    assert by_platform["zenodo"].status == STATUS_OK
    assert by_platform["zenodo"].identifier == "10.5281/zenodo.11111111"
    assert sorted(req.path for req, _ in httpserver.log) == [
        "/10.5281/zenodo.11111111",
        "/docxology/template_search_project",
    ]


def test_verify_reachability_private_repo_is_unreachable(tmp_path: Path, httpserver: HTTPServer) -> None:
    # GitHub answers 404 for private repos on unauthenticated requests —
    # the exact template_search_project failure this module exists to catch.
    httpserver.expect_request("/docxology/template_search_project", method="HEAD").respond_with_data(status=404)
    httpserver.expect_request("/10.5281/zenodo.11111111", method="HEAD").respond_with_data(status=302)
    report = compile_publishing_status(_project(tmp_path))
    checks = verify_reachability(
        report,
        github_base=httpserver.url_for(""),
        doi_base=httpserver.url_for(""),
    )
    by_platform = {c.platform: c for c in checks}
    assert by_platform["github"].status == STATUS_UNREACHABLE
    assert by_platform["zenodo"].status == STATUS_OK


def test_verify_reachability_never_sends_auth_header(
    tmp_path: Path, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_should_never_be_sent")
    httpserver.expect_request("/docxology/template_search_project", method="HEAD").respond_with_data("")
    httpserver.expect_request("/10.5281/zenodo.11111111", method="HEAD").respond_with_data(status=302)
    verify_reachability(
        compile_publishing_status(_project(tmp_path)),
        github_base=httpserver.url_for(""),
        doi_base=httpserver.url_for(""),
    )
    for request, _ in httpserver.log:
        assert "Authorization" not in request.headers


def test_verify_reachability_empty_without_identifiers(tmp_path: Path) -> None:
    root = tmp_path / "bare"
    root.mkdir()
    assert verify_reachability(compile_publishing_status(root)) == ()


# ---------------------------------------------------------------------------
# apply_reachability + rendering
# ---------------------------------------------------------------------------


def _check(platform: str, status: str) -> ReachabilityCheck:
    return ReachabilityCheck(platform, "id", "http://x", status, "HTTP 404")


def test_apply_reachability_downgrades_unreachable_published_row(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    assert report.published_count == 2
    verified = apply_reachability(report, (_check("github", STATUS_UNREACHABLE),))
    by_name = {p.name: p for p in verified.platforms}
    assert by_name["github"].state is PublicationState.UNREACHABLE
    assert by_name["zenodo"].state is PublicationState.PUBLISHED
    assert verified.published_count == 1
    # Input report is not mutated.
    assert {p.name: p.state for p in report.platforms}["github"] is PublicationState.PUBLISHED


def test_apply_reachability_error_and_ok_do_not_downgrade(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    verified = apply_reachability(
        report,
        (_check("github", STATUS_ERROR), _check("zenodo", STATUS_OK)),
    )
    assert verified == report


def test_apply_reachability_never_demotes_reserved_doi(tmp_path: Path) -> None:
    # A Zenodo-reserved DOI is not registered with DataCite until publication,
    # so a resolver 404 is its NORMAL state — the 🔵 row must survive.
    cfg = CONFIG_YAML + '  doi_status: "DOI reserved"\n'
    report = compile_publishing_status(_project(tmp_path, cfg))
    assert {p.name: p.state for p in report.platforms}["zenodo"] is PublicationState.RESERVED
    verified = apply_reachability(report, (_check("zenodo", STATUS_UNREACHABLE),))
    assert {p.name: p.state for p in verified.platforms}["zenodo"] is PublicationState.RESERVED


def test_apply_reachability_downgrades_both_platforms(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    verified = apply_reachability(
        report,
        (_check("github", STATUS_UNREACHABLE), _check("zenodo", STATUS_UNREACHABLE)),
    )
    states = {p.name: p.state for p in verified.platforms}
    assert states["github"] is PublicationState.UNREACHABLE
    assert states["zenodo"] is PublicationState.UNREACHABLE
    assert verified.published_count == 0


def test_apply_reachability_is_idempotent(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    checks = (_check("github", STATUS_UNREACHABLE),)
    once = apply_reachability(report, checks)
    assert apply_reachability(once, checks) == once


def test_apply_reachability_never_touches_non_published_rows(tmp_path: Path) -> None:
    # github_pages is AVAILABLE (not PUBLISHED/RESERVED) — an unreachable
    # check for it must not demote the row.
    report = compile_publishing_status(_project(tmp_path))
    verified = apply_reachability(report, (_check("github_pages", STATUS_UNREACHABLE),))
    assert verified == report


def test_render_shows_unreachable_badge_and_conditional_legend(tmp_path: Path) -> None:
    report = compile_publishing_status(_project(tmp_path))
    verified = apply_reachability(report, (_check("github", STATUS_UNREACHABLE),))
    md = render_status_markdown(verified)
    assert "❌ unreachable" in md
    assert "--verify-reachability" in md  # legend fragment present


def test_default_render_has_no_unreachable_legend(tmp_path: Path) -> None:
    md = render_status_markdown(compile_publishing_status(_project(tmp_path)))
    assert "❌" not in md
    assert "unreachable" not in md


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_verify_flag_downgrades_and_reports(
    tmp_path: Path, httpserver: HTTPServer, capsys: pytest.CaptureFixture[str]
) -> None:
    httpserver.expect_request("/docxology/template_search_project", method="HEAD").respond_with_data(status=404)
    httpserver.expect_request("/10.5281/zenodo.11111111", method="HEAD").respond_with_data(status=302)
    root = _project(tmp_path)
    rc = main(
        [
            "--project",
            str(root),
            "--verify-reachability",
            "--github-base",
            httpserver.url_for(""),
            "--doi-base",
            httpserver.url_for(""),
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "❌ unreachable" in captured.out
    assert "✅ published" in captured.out  # zenodo row survives
    assert "reachability: github docxology/template_search_project -> unreachable (HTTP 404)" in captured.err
    assert "reachability: zenodo 10.5281/zenodo.11111111 -> ok (HTTP 302)" in captured.err


@pytest.mark.parametrize("persist_flag", ["--write", "--check"])
def test_cli_verify_flag_refuses_write_and_check(tmp_path: Path, httpserver: HTTPServer, persist_flag: str) -> None:
    """A network-derived ❌ must never reach a committed README (drift gate)."""
    root = _project(tmp_path)
    readme = root / "README.md"
    readme.write_text("# x\n\n## Publication and rendering\n\nprose\n", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "--project",
                str(root),
                persist_flag,
                "--verify-reachability",
                "--github-base",
                httpserver.url_for(""),
            ]
        )
    assert excinfo.value.code == 2  # argparse error
    assert httpserver.log == []  # refused before any network probe
    assert "unreachable" not in readme.read_text(encoding="utf-8")


def test_cli_default_is_offline_and_byte_identical(
    tmp_path: Path, httpserver: HTTPServer, capsys: pytest.CaptureFixture[str]
) -> None:
    """Negative control: without the flag, zero HTTP requests and unchanged output."""
    root = _project(tmp_path)
    rc = main(["--project", str(root)])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.strip() == render_status_block(compile_publishing_status(root))
    assert httpserver.log == []


def test_cli_base_overrides_without_flag_do_nothing(
    tmp_path: Path, httpserver: HTTPServer, capsys: pytest.CaptureFixture[str]
) -> None:
    """Base URL overrides alone must not opt in to network checks."""
    root = _project(tmp_path)
    rc = main(
        [
            "--project",
            str(root),
            "--github-base",
            httpserver.url_for(""),
            "--doi-base",
            httpserver.url_for(""),
        ]
    )
    assert rc == 0
    assert httpserver.log == []
    assert "unreachable" not in capsys.readouterr().out
