"""Tests for ``infrastructure.publishing.archival``.

Uses ``pytest-httpserver`` (no mocks) for HTTP-backed providers.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.publishing.archival import (
    ArchivalError,
    ArchivalRun,
    IPFSPinataProvider,
    IPFSWeb3StorageProvider,
    SoftwareHeritageProvider,
    ZenodoProvider,
    archive_publication,
    load_credentials,
)


@pytest.fixture
def bundle_dir(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manuscript.pdf").write_bytes(b"%PDF-1.4 example")
    (bundle / "manifest.json").write_text('{"schema": "1.0"}\n', encoding="utf-8")
    return bundle


@pytest.fixture
def bundle_single_file(tmp_path: Path) -> Path:
    f = tmp_path / "single.pdf"
    f.write_bytes(b"%PDF-1.4 single-file")
    return f


# ---------------------------------------------------------------------------
# load_credentials
# ---------------------------------------------------------------------------


def test_load_credentials_env_only(tmp_path: Path) -> None:
    creds = load_credentials(
        env={"ZENODO_API_TOKEN": "zt", "PINATA_JWT": "pj", "WEB3_STORAGE_TOKEN": "wt"},
        credentials_path=tmp_path / "nonexistent.json",
    )
    assert creds.zenodo_token == "zt"
    assert creds.pinata_jwt == "pj"
    assert creds.web3_storage_token == "wt"


def test_load_credentials_file_fallback(tmp_path: Path) -> None:
    creds_path = tmp_path / "creds.json"
    creds_path.write_text(
        json.dumps({"zenodo_token": "from-file", "pinata_jwt": "also-from-file"}),
        encoding="utf-8",
    )
    creds = load_credentials(env={}, credentials_path=creds_path)
    assert creds.zenodo_token == "from-file"
    assert creds.pinata_jwt == "also-from-file"
    assert creds.web3_storage_token is None


def test_load_credentials_env_overrides_file(tmp_path: Path) -> None:
    creds_path = tmp_path / "creds.json"
    creds_path.write_text(json.dumps({"zenodo_token": "from-file"}), encoding="utf-8")
    creds = load_credentials(
        env={"ZENODO_API_TOKEN": "from-env"},
        credentials_path=creds_path,
    )
    assert creds.zenodo_token == "from-env"


def test_load_credentials_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "creds.json"
    bad.write_text("not json {", encoding="utf-8")
    with pytest.raises(ArchivalError, match="not valid JSON"):
        load_credentials(env={}, credentials_path=bad)


# ---------------------------------------------------------------------------
# Dry-run receipts (no network)
# ---------------------------------------------------------------------------


def test_zenodo_dry_run_no_token(bundle_dir: Path) -> None:
    provider = ZenodoProvider(token=None)
    receipt = provider.deposit(bundle_dir, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.provider == "zenodo"
    assert receipt.bundle_sha256 is not None and len(receipt.bundle_sha256) == 64


def test_pinata_dry_run_no_token(bundle_dir: Path) -> None:
    provider = IPFSPinataProvider(jwt=None)
    receipt = provider.deposit(bundle_dir, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.provider == "ipfs_pinata"


def test_web3storage_dry_run_no_token(bundle_dir: Path) -> None:
    provider = IPFSWeb3StorageProvider(token=None)
    receipt = provider.deposit(bundle_dir, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.provider == "ipfs_web3storage"


def test_software_heritage_dry_run_no_repo(tmp_path: Path) -> None:
    # Bundle with no .git: provider returns an error receipt, not dry-run.
    provider = SoftwareHeritageProvider()
    receipt = provider.deposit(tmp_path, dry_run=True)
    assert receipt.status == "error"
    assert "Could not resolve a repository URL" in (receipt.error or "")


def test_software_heritage_dry_run_with_url_file(tmp_path: Path) -> None:
    url_file = tmp_path / "repo_url.txt"
    url_file.write_text("https://github.com/example/repo\n", encoding="utf-8")
    provider = SoftwareHeritageProvider()
    receipt = provider.deposit(url_file, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.identifier == "https://github.com/example/repo"


def test_software_heritage_dry_run_with_git_config(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".git" / "config").write_text(
        '[remote "origin"]\n\turl = https://github.com/example/x\n\tfetch = +refs/heads/*\n',
        encoding="utf-8",
    )
    provider = SoftwareHeritageProvider()
    receipt = provider.deposit(repo, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.identifier == "https://github.com/example/x"


# ---------------------------------------------------------------------------
# Missing credential paths (non-dry-run, no network)
# ---------------------------------------------------------------------------


def test_zenodo_missing_token_returns_error(bundle_dir: Path) -> None:
    receipt = ZenodoProvider(token=None).deposit(bundle_dir, dry_run=False)
    assert receipt.status == "error"
    assert "ZENODO_API_TOKEN" in (receipt.error or "")


def test_pinata_missing_jwt_returns_error(bundle_dir: Path) -> None:
    receipt = IPFSPinataProvider(jwt=None).deposit(bundle_dir, dry_run=False)
    assert receipt.status == "error"
    assert "PINATA_JWT" in (receipt.error or "")


def test_web3storage_missing_token_returns_error(bundle_dir: Path) -> None:
    receipt = IPFSWeb3StorageProvider(token=None).deposit(bundle_dir, dry_run=False)
    assert receipt.status == "error"
    assert "WEB3_STORAGE_TOKEN" in (receipt.error or "")


# ---------------------------------------------------------------------------
# Real HTTP path against a local httpserver (pytest-httpserver)
# ---------------------------------------------------------------------------


def test_zenodo_success_against_local_server(httpserver: HTTPServer, bundle_dir: Path) -> None:
    bucket_url = httpserver.url_for("/files/bucket-abc")
    httpserver.expect_request("/deposit/depositions", method="POST").respond_with_json(
        {"id": 999, "links": {"bucket": bucket_url}}
    )
    # Match the file upload endpoints under the bucket. The provider PUTs each file at
    # f"{bucket_url}/{rel_path_to_bundle_parent}".
    httpserver.expect_request("/files/bucket-abc/bundle/manuscript.pdf", method="PUT").respond_with_data(status=200)
    httpserver.expect_request("/files/bucket-abc/bundle/manifest.json", method="PUT").respond_with_data(status=200)
    httpserver.expect_request("/deposit/depositions/999/actions/publish", method="POST").respond_with_json(
        {
            "doi": "10.5281/zenodo.999999",
            "links": {"record_html": "https://zenodo.org/record/999999"},
        }
    )

    provider = ZenodoProvider(token="test-token", base_url=httpserver.url_for(""))
    receipt = provider.deposit(bundle_dir, dry_run=False)
    assert receipt.status == "ok", receipt.error
    assert receipt.identifier == "10.5281/zenodo.999999"
    assert receipt.url == "https://doi.org/10.5281/zenodo.999999"


def test_zenodo_http_error_returns_error_receipt(httpserver: HTTPServer, bundle_dir: Path) -> None:
    httpserver.expect_request("/deposit/depositions", method="POST").respond_with_data("server overload", status=503)
    provider = ZenodoProvider(token="t", base_url=httpserver.url_for(""))
    receipt = provider.deposit(bundle_dir, dry_run=False)
    assert receipt.status == "error"
    assert "Zenodo HTTP error" in (receipt.error or "")


def test_pinata_success_against_local_server(httpserver: HTTPServer, bundle_single_file: Path) -> None:
    httpserver.expect_request("/pinning/pinFileToIPFS", method="POST").respond_with_json(
        {"IpfsHash": "QmTestCID12345", "PinSize": 42}
    )

    provider = IPFSPinataProvider(jwt="t", base_url=httpserver.url_for(""))
    receipt = provider.deposit(bundle_single_file, dry_run=False)
    assert receipt.status == "ok"
    assert receipt.identifier == "QmTestCID12345"
    assert receipt.url is not None and "QmTestCID12345" in receipt.url


def test_pinata_missing_ipfshash(httpserver: HTTPServer, bundle_single_file: Path) -> None:
    httpserver.expect_request("/pinning/pinFileToIPFS", method="POST").respond_with_json({"unexpected": "field"})

    provider = IPFSPinataProvider(jwt="t", base_url=httpserver.url_for(""))
    receipt = provider.deposit(bundle_single_file, dry_run=False)
    assert receipt.status == "error"
    assert "missing IpfsHash" in (receipt.error or "")


def test_software_heritage_success(httpserver: HTTPServer, tmp_path: Path) -> None:
    url_file = tmp_path / "repo_url.txt"
    url_file.write_text("https://github.com/example/repo\n", encoding="utf-8")

    httpserver.expect_request(
        "/origin/save/git/url/https://github.com/example/repo/",
        method="POST",
    ).respond_with_json({"save_request_status": "accepted", "id": 12345})

    provider = SoftwareHeritageProvider(base_url=httpserver.url_for(""))
    receipt = provider.deposit(url_file, dry_run=False)
    assert receipt.status == "ok", receipt.error
    assert receipt.extra.get("save_request_status") == "accepted"


# ---------------------------------------------------------------------------
# archive_publication orchestrator
# ---------------------------------------------------------------------------


def test_archive_publication_dry_run_writes_receipts(bundle_dir: Path, tmp_path: Path) -> None:
    receipts_out = tmp_path / "receipts.json"
    run = archive_publication(
        bundle_dir,
        providers=[
            ZenodoProvider(token=None),
            IPFSPinataProvider(jwt=None),
        ],
        dry_run=True,
        output_receipts_path=receipts_out,
    )
    assert isinstance(run, ArchivalRun)
    assert len(run.receipts) == 2
    assert run.all_ok
    assert run.failed == ()
    persisted = json.loads(receipts_out.read_text(encoding="utf-8"))
    assert persisted["all_ok"] is True
    assert len(persisted["receipts"]) == 2


def test_archive_publication_partial_failure(httpserver: HTTPServer, bundle_dir: Path) -> None:
    httpserver.expect_request("/deposit/depositions", method="POST").respond_with_data("fail", status=500)
    run = archive_publication(
        bundle_dir,
        providers=[
            ZenodoProvider(token="t", base_url=httpserver.url_for("")),
            IPFSPinataProvider(jwt=None),  # dry-run path, but we're not dry-running
        ],
        dry_run=False,
    )
    assert not run.all_ok
    assert len(run.failed) >= 1


def test_archive_publication_nonexistent_bundle_raises(tmp_path: Path) -> None:
    with pytest.raises(ArchivalError):
        archive_publication(
            tmp_path / "does-not-exist",
            providers=[ZenodoProvider(token=None)],
            dry_run=True,
        )


def test_archive_publication_zero_providers(bundle_dir: Path) -> None:
    run = archive_publication(bundle_dir, providers=[], dry_run=True)
    assert run.receipts == ()
    assert run.all_ok  # vacuously true


def test_archive_publication_refuses_local_only_project_before_provider(tmp_path: Path) -> None:
    project = tmp_path / "projects/working/private"
    project.mkdir(parents=True)
    output = tmp_path / "output/working/private/executable_bundle"
    output.mkdir(parents=True)
    (output / "paper.pdf").write_bytes(b"%PDF-1.4 private")

    with pytest.raises(ValueError, match="local-only"):
        archive_publication(
            output,
            providers=[ZenodoProvider(token="should-not-be-used")],
            dry_run=False,
            repo_root=tmp_path,
            project_name="working/private",
            credential_sources={"zenodo": "environment"},
        )
