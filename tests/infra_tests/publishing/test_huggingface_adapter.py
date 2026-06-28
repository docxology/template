"""Tests for the HuggingFace Hub adapter.

No mocks — the real HTTP path runs against a local ``pytest-httpserver``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.publishing.huggingface import (
    HuggingFaceConfig,
    HuggingFaceHubAdapter,
    HFRepoType,
)


@pytest.fixture
def bundle_dir(tmp_path: Path) -> Path:
    d = tmp_path / "bundle"
    d.mkdir()
    (d / "paper.pdf").write_bytes(b"%PDF-1.7 minimal")
    (d / "manifest.json").write_text('{"ok": true}', encoding="utf-8")
    return d


def test_dry_run_is_noop_and_lists_files(bundle_dir: Path) -> None:
    adapter = HuggingFaceHubAdapter(
        HuggingFaceConfig(repo_id="ns/my-paper", token="t"),
    )
    result = adapter.publish(bundle_dir, dry_run=True)
    assert result.status == "dry-run"
    assert result.repo_type == "dataset"
    assert set(result.uploaded) == {"manifest.json", "paper.pdf"}
    assert "would_create" in result.extra


def test_missing_token_returns_error(bundle_dir: Path) -> None:
    adapter = HuggingFaceHubAdapter(
        HuggingFaceConfig(repo_id="ns/my-paper"),
        env={},  # no HUGGINGFACE_TOKEN / HF_TOKEN
    )
    result = adapter.publish(bundle_dir, dry_run=False)
    assert result.status == "error"
    assert "Missing HUGGINGFACE_TOKEN" in (result.error or "")


def test_token_resolved_from_env() -> None:
    adapter = HuggingFaceHubAdapter(
        HuggingFaceConfig(repo_id="ns/x"),
        env={"HF_TOKEN": "from-env"},
    )
    assert adapter.config.token == "from-env"


def test_success_against_local_server(httpserver: HTTPServer, bundle_dir: Path) -> None:
    httpserver.expect_request("/api/repos/create", method="POST").respond_with_json(
        {"url": "http://x/datasets/ns/my-paper", "name": "my-paper"}
    )
    httpserver.expect_request("/api/datasets/ns/my-paper/commit/main", method="POST").respond_with_json(
        {"commitUrl": "http://x/commit/abc123", "commitOid": "abc123"}
    )

    adapter = HuggingFaceHubAdapter(
        HuggingFaceConfig(repo_id="ns/my-paper", token="t", base_url=httpserver.url_for("")),
    )
    result = adapter.publish(bundle_dir, dry_run=False)
    assert result.status == "ok", result.error
    assert result.commit_url == "http://x/commit/abc123"
    assert set(result.uploaded) == {"manifest.json", "paper.pdf"}


def test_create_conflict_409_is_tolerated(httpserver: HTTPServer, bundle_dir: Path) -> None:
    httpserver.expect_request("/api/repos/create", method="POST").respond_with_data("exists", status=409)
    httpserver.expect_request("/api/datasets/ns/my-paper/commit/main", method="POST").respond_with_json(
        {"commitOid": "deadbeef"}
    )

    adapter = HuggingFaceHubAdapter(
        HuggingFaceConfig(repo_id="ns/my-paper", token="t", base_url=httpserver.url_for("")),
    )
    result = adapter.publish(bundle_dir, dry_run=False)
    assert result.status == "ok", result.error


def test_commit_http_error_returns_error_receipt(httpserver: HTTPServer, bundle_dir: Path) -> None:
    httpserver.expect_request("/api/repos/create", method="POST").respond_with_json({"name": "x"})
    httpserver.expect_request("/api/datasets/ns/my-paper/commit/main", method="POST").respond_with_data(
        "boom", status=500
    )

    adapter = HuggingFaceHubAdapter(
        HuggingFaceConfig(repo_id="ns/my-paper", token="t", base_url=httpserver.url_for("")),
    )
    result = adapter.publish(bundle_dir, dry_run=False)
    assert result.status == "error"
    assert "HTTP error" in (result.error or "")


def test_should_use_hub_is_false_for_custom_base_url() -> None:
    # Tests point base_url at a local server; the huggingface_hub LFS path must
    # never engage there (it would make a real network call), regardless of install.
    adapter = HuggingFaceHubAdapter(
        HuggingFaceConfig(repo_id="ns/x", token="t", base_url="http://localhost:9"),
    )
    assert adapter._should_use_hub() is False


def test_should_use_hub_tracks_availability_on_public_hub() -> None:
    from infrastructure.publishing.huggingface.adapter import _hub_available

    adapter = HuggingFaceHubAdapter(HuggingFaceConfig(repo_id="ns/x", token="t"))  # default public Hub
    assert adapter._should_use_hub() is _hub_available()


def test_model_repo_url_has_no_prefix() -> None:
    adapter = HuggingFaceHubAdapter(
        HuggingFaceConfig(repo_id="ns/m", token="t", repo_type=HFRepoType.MODEL),
    )
    assert adapter._repo_url.endswith("/ns/m")
    assert "models/" not in adapter._repo_url
