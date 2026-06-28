"""Tests for the OSF (Open Science Framework) adapter.

No mocks — the real HTTP path runs against a local ``pytest-httpserver``.
OSF splits metadata (api base) and file I/O (files base); both point at the
same local server here with distinct paths.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.publishing.osf import OSFAdapter, OSFConfig


@pytest.fixture
def bundle_dir(tmp_path: Path) -> Path:
    d = tmp_path / "bundle"
    d.mkdir()
    (d / "paper.pdf").write_bytes(b"%PDF-1.7 minimal")
    (d / "manifest.json").write_text('{"ok": true}', encoding="utf-8")
    return d


@pytest.fixture
def single_file(tmp_path: Path) -> Path:
    f = tmp_path / "paper.pdf"
    f.write_bytes(b"%PDF-1.7 minimal")
    return f


def test_dry_run_new_node(bundle_dir: Path) -> None:
    adapter = OSFAdapter(OSFConfig(title="My Paper", token="t"))
    result = adapter.publish(bundle_dir, dry_run=True)
    assert result.status == "dry-run"
    assert result.node_id is None
    assert result.extra["would_create_node"].endswith("/nodes/")
    assert set(result.uploaded) == {"manifest.json", "paper.pdf"}


def test_missing_token_returns_error(single_file: Path) -> None:
    adapter = OSFAdapter(OSFConfig(title="x"), env={})
    result = adapter.publish(single_file, dry_run=False)
    assert result.status == "error"
    assert "Missing OSF_TOKEN" in (result.error or "")


def test_token_resolved_from_env() -> None:
    adapter = OSFAdapter(OSFConfig(title="x"), env={"OSF_TOKEN": "env-tok"})
    assert adapter.config.token == "env-tok"


def test_create_node_and_upload(httpserver: HTTPServer, single_file: Path) -> None:
    httpserver.expect_request("/v2/nodes/", method="POST").respond_with_json({"data": {"id": "ab12c", "type": "nodes"}})
    httpserver.expect_request("/v1/resources/ab12c/providers/osfstorage/", method="PUT").respond_with_json(
        {"data": {"id": "osfstorage/xyz"}}, status=201
    )

    adapter = OSFAdapter(
        OSFConfig(
            title="My Paper",
            token="t",
            api_base=httpserver.url_for("/v2"),
            files_base=httpserver.url_for("/v1"),
        )
    )
    result = adapter.publish(single_file, dry_run=False)
    assert result.status == "ok", result.error
    assert result.node_id == "ab12c"
    assert result.url == "https://osf.io/ab12c/"
    assert result.uploaded == ("paper.pdf",)


def test_existing_node_skips_creation(httpserver: HTTPServer, bundle_dir: Path) -> None:
    # No /v2/nodes/ handler registered — creation must NOT be called.
    httpserver.expect_request("/v1/resources/zzzzz/providers/osfstorage/", method="PUT").respond_with_json(
        {"data": {"id": "ok"}}, status=201
    )

    adapter = OSFAdapter(
        OSFConfig(
            token="t",
            node_id="zzzzz",
            api_base=httpserver.url_for("/v2"),
            files_base=httpserver.url_for("/v1"),
        )
    )
    result = adapter.publish(bundle_dir, dry_run=False)
    assert result.status == "ok", result.error
    assert result.node_id == "zzzzz"
    assert set(result.uploaded) == {"manifest.json", "paper.pdf"}


def test_node_creation_http_error(httpserver: HTTPServer, single_file: Path) -> None:
    httpserver.expect_request("/v2/nodes/", method="POST").respond_with_data("unauthorized", status=401)
    adapter = OSFAdapter(
        OSFConfig(
            title="x",
            token="bad",
            api_base=httpserver.url_for("/v2"),
            files_base=httpserver.url_for("/v1"),
        )
    )
    result = adapter.publish(single_file, dry_run=False)
    assert result.status == "error"
    assert "HTTP error" in (result.error or "")
