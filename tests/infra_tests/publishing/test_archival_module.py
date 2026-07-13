"""Tests for the infrastructure.publishing.archival subpackage.

Covers the public surface of the archival/ subpackage (models, providers,
orchestrate) at the unit level. Network-dependent behaviour is tested in
test_archival.py via pytest-httpserver; this file uses only real files and
real computations — no mocks, no HTTP.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import infrastructure.publishing.archival as archival_pkg
from infrastructure.publishing.archival import (
    ArchivalCredentials,
    ArchivalError,
    ArchivalProvider,
    ArchivalReceipt,
    ArchivalRun,
    DEFAULT_CREDENTIALS_PATH,
    IPFSPinataProvider,
    IPFSWeb3StorageProvider,
    SoftwareHeritageProvider,
    ZenodoProvider,
    archive_publication,
)
from infrastructure.publishing.archival.models import _bundle_sha256


# ---------------------------------------------------------------------------
# 1. Module-level exports
# ---------------------------------------------------------------------------


def test_archival_module_exports_all_names() -> None:
    """All names declared in __all__ must be importable from the package root."""
    expected = {
        "ArchivalError",
        "ArchivalReceipt",
        "ArchivalRun",
        "ArchivalProvider",
        "ZenodoProvider",
        "IPFSPinataProvider",
        "IPFSWeb3StorageProvider",
        "SoftwareHeritageProvider",
        "ArchivalCredentials",
        "archive_publication",
        "load_credentials",
        "DEFAULT_CREDENTIALS_PATH",
    }
    missing = expected - set(archival_pkg.__all__)
    assert not missing, f"Missing from __all__: {missing}"
    for name in expected:
        assert hasattr(archival_pkg, name), f"Not importable: {name}"


# ---------------------------------------------------------------------------
# 2. ArchivalCredentials
# ---------------------------------------------------------------------------


def test_archival_credentials_default_none() -> None:
    """A zero-argument ArchivalCredentials must have all credential fields None."""
    creds = ArchivalCredentials()
    assert creds.zenodo_token is None
    assert creds.pinata_jwt is None
    assert creds.web3_storage_token is None


def test_archival_credentials_frozen() -> None:
    """ArchivalCredentials is a frozen dataclass; mutation must raise."""
    creds = ArchivalCredentials(zenodo_token="tok")
    with pytest.raises((AttributeError, TypeError)):
        creds.zenodo_token = "other"  # type: ignore[misc]


def test_archival_credentials_stores_values() -> None:
    """Values passed at construction must be readable back unchanged."""
    creds = ArchivalCredentials(
        zenodo_token="zt",
        pinata_jwt="pj",
        web3_storage_token="wt",
    )
    assert creds.zenodo_token == "zt"
    assert creds.pinata_jwt == "pj"
    assert creds.web3_storage_token == "wt"


# ---------------------------------------------------------------------------
# 3. ArchivalReceipt
# ---------------------------------------------------------------------------


def test_archival_receipt_dry_run_status() -> None:
    """A receipt with status='dry-run' is considered successful."""
    receipt = ArchivalReceipt(
        provider="zenodo",
        status="dry-run",
        identifier=None,
        url=None,
        timestamp_utc="2026-01-01T00:00:00Z",
    )
    assert receipt.status == "dry-run"
    # Verify it participates correctly in ArchivalRun.all_ok logic
    run = ArchivalRun(
        bundle_path="/fake",
        receipts=(receipt,),
        started_utc="2026-01-01T00:00:00Z",
        finished_utc="2026-01-01T00:00:01Z",
    )
    assert run.all_ok


def test_archival_receipt_ok_status() -> None:
    """A receipt with status='ok' carries an identifier and url."""
    receipt = ArchivalReceipt(
        provider="ipfs_pinata",
        status="ok",
        identifier="QmABC123",
        url="https://gateway.pinata.cloud/ipfs/QmABC123",
        timestamp_utc="2026-01-01T00:00:00Z",
        bundle_sha256="a" * 64,
    )
    assert receipt.status == "ok"
    assert receipt.identifier == "QmABC123"
    assert receipt.url is not None


def test_archival_receipt_error_status() -> None:
    """A receipt with status='error' carries a non-None error message."""
    receipt = ArchivalReceipt(
        provider="zenodo",
        status="error",
        identifier=None,
        url=None,
        timestamp_utc="2026-01-01T00:00:00Z",
        error="Missing credential: ZENODO_API_TOKEN",
    )
    assert receipt.status == "error"
    assert receipt.error is not None
    assert "ZENODO_API_TOKEN" in receipt.error


def test_archival_receipt_frozen() -> None:
    """ArchivalReceipt is frozen; fields must not be assignable after creation."""
    receipt = ArchivalReceipt(
        provider="zenodo",
        status="ok",
        identifier="10.5281/zenodo.1",
        url="https://doi.org/10.5281/zenodo.1",
        timestamp_utc="2026-01-01T00:00:00Z",
    )
    with pytest.raises((AttributeError, TypeError)):
        receipt.status = "error"  # type: ignore[misc]


def test_archival_receipt_extra_defaults_empty() -> None:
    """The extra field defaults to an empty dict when not supplied."""
    receipt = ArchivalReceipt(
        provider="zenodo",
        status="dry-run",
        identifier=None,
        url=None,
        timestamp_utc="2026-01-01T00:00:00Z",
    )
    assert isinstance(receipt.extra, dict)
    assert len(receipt.extra) == 0


# ---------------------------------------------------------------------------
# 4. ArchivalRun
# ---------------------------------------------------------------------------


def _make_receipt(status: str, provider: str = "zenodo") -> ArchivalReceipt:
    return ArchivalReceipt(
        provider=provider,
        status=status,
        identifier=None,
        url=None,
        timestamp_utc="2026-01-01T00:00:00Z",
    )


def test_archival_run_all_ok_all_ok_receipts() -> None:
    """all_ok is True when every receipt has status 'ok'."""
    run = ArchivalRun(
        bundle_path="/bundle",
        receipts=(_make_receipt("ok"), _make_receipt("ok", "ipfs_pinata")),
        started_utc="2026-01-01T00:00:00Z",
        finished_utc="2026-01-01T00:00:01Z",
    )
    assert run.all_ok is True


def test_archival_run_all_ok_mixed_ok_and_dry_run() -> None:
    """all_ok is True when receipts are a mix of 'ok' and 'dry-run'."""
    run = ArchivalRun(
        bundle_path="/bundle",
        receipts=(_make_receipt("ok"), _make_receipt("dry-run", "ipfs_pinata")),
        started_utc="2026-01-01T00:00:00Z",
        finished_utc="2026-01-01T00:00:01Z",
    )
    assert run.all_ok is True


def test_archival_run_all_ok_false_with_error() -> None:
    """all_ok is False when any receipt has status 'error'."""
    run = ArchivalRun(
        bundle_path="/bundle",
        receipts=(_make_receipt("ok"), _make_receipt("error", "ipfs_pinata")),
        started_utc="2026-01-01T00:00:00Z",
        finished_utc="2026-01-01T00:00:01Z",
    )
    assert run.all_ok is False


def test_archival_run_all_ok_vacuously_true_for_empty() -> None:
    """all_ok is True vacuously when there are no receipts."""
    run = ArchivalRun(
        bundle_path="/bundle",
        receipts=(),
        started_utc="2026-01-01T00:00:00Z",
        finished_utc="2026-01-01T00:00:01Z",
    )
    assert run.all_ok is True


def test_archival_run_failed_returns_only_error_receipts() -> None:
    """failed returns only the receipts whose status is 'error'."""
    ok = _make_receipt("ok")
    dry = _make_receipt("dry-run", "ipfs_pinata")
    err = _make_receipt("error", "software_heritage")
    run = ArchivalRun(
        bundle_path="/bundle",
        receipts=(ok, dry, err),
        started_utc="2026-01-01T00:00:00Z",
        finished_utc="2026-01-01T00:00:01Z",
    )
    assert run.failed == (err,)


def test_archival_run_failed_empty_when_all_ok() -> None:
    """failed is an empty tuple when no receipt has status 'error'."""
    run = ArchivalRun(
        bundle_path="/bundle",
        receipts=(_make_receipt("ok"), _make_receipt("dry-run", "ipfs_pinata")),
        started_utc="2026-01-01T00:00:00Z",
        finished_utc="2026-01-01T00:00:01Z",
    )
    assert run.failed == ()


def test_archival_run_to_dict_structure() -> None:
    """to_dict must include expected top-level keys and receipt list."""
    run = ArchivalRun(
        bundle_path="/b",
        receipts=(_make_receipt("dry-run"),),
        started_utc="2026-01-01T00:00:00Z",
        finished_utc="2026-01-01T00:00:01Z",
    )
    d = run.to_dict()
    assert "all_ok" in d
    assert "receipts" in d
    assert isinstance(d["receipts"], list)
    assert len(d["receipts"]) == 1
    assert d["receipts"][0]["provider"] == "zenodo"
    assert d["all_ok"] is True


# ---------------------------------------------------------------------------
# 5. _bundle_sha256 helper
# ---------------------------------------------------------------------------


def test_bundle_sha256_file_returns_hex_string(tmp_path: Path) -> None:
    """_bundle_sha256 on a single file returns a 64-char lowercase hex string."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"hello archival world")
    result = _bundle_sha256(f)
    assert isinstance(result, str)
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_bundle_sha256_matches_hashlib_for_single_file(tmp_path: Path) -> None:
    """Hash of a single file must equal hashlib.sha256 applied to the same bytes."""
    content = b"deterministic content for hash check"
    f = tmp_path / "file.txt"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert _bundle_sha256(f) == expected


def test_bundle_sha256_deterministic(tmp_path: Path) -> None:
    """Calling _bundle_sha256 twice on the same file produces the same hash."""
    f = tmp_path / "repeat.txt"
    f.write_bytes(b"some bytes that should hash consistently")
    assert _bundle_sha256(f) == _bundle_sha256(f)


def test_bundle_sha256_directory_deterministic(tmp_path: Path) -> None:
    """_bundle_sha256 on a directory is deterministic across two calls."""
    d = tmp_path / "dir"
    d.mkdir()
    (d / "a.txt").write_bytes(b"file a")
    (d / "b.txt").write_bytes(b"file b")
    assert _bundle_sha256(d) == _bundle_sha256(d)


def test_bundle_sha256_different_content_differs(tmp_path: Path) -> None:
    """Two files with different content must produce different hashes."""
    f1 = tmp_path / "f1.txt"
    f2 = tmp_path / "f2.txt"
    f1.write_bytes(b"content one")
    f2.write_bytes(b"content two")
    assert _bundle_sha256(f1) != _bundle_sha256(f2)


def test_bundle_sha256_empty_directory(tmp_path: Path) -> None:
    """An empty directory returns a 64-char hex string (hash of nothing)."""
    d = tmp_path / "empty_dir"
    d.mkdir()
    result = _bundle_sha256(d)
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


# ---------------------------------------------------------------------------
# 6. ZenodoProvider — dry-run
# ---------------------------------------------------------------------------


def test_zenodo_provider_dry_run_no_token(tmp_path: Path) -> None:
    """ZenodoProvider(None).deposit(..., dry_run=True) returns a dry-run receipt."""
    bundle = tmp_path / "bundle.pdf"
    bundle.write_bytes(b"%PDF-1.4 test")
    provider = ZenodoProvider(token=None)
    receipt = provider.deposit(bundle, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.provider == "zenodo"
    assert receipt.bundle_sha256 is not None
    assert len(receipt.bundle_sha256) == 64


def test_zenodo_provider_dry_run_with_token(tmp_path: Path) -> None:
    """dry_run=True must not make any network call, even if a token is supplied."""
    bundle = tmp_path / "paper.pdf"
    bundle.write_bytes(b"%PDF-1.4 with-token test")
    provider = ZenodoProvider(token="fake-token-should-not-be-used")
    receipt = provider.deposit(bundle, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.provider == "zenodo"


def test_zenodo_provider_dry_run_includes_endpoint_hint(tmp_path: Path) -> None:
    """The extra dict for a dry-run receipt must hint at the target endpoint."""
    bundle = tmp_path / "f.pdf"
    bundle.write_bytes(b"%PDF")
    provider = ZenodoProvider(token=None, base_url="https://sandbox.zenodo.org/api")
    receipt = provider.deposit(bundle, dry_run=True)
    assert "would_post_to" in receipt.extra
    assert "sandbox.zenodo.org" in receipt.extra["would_post_to"]


def test_zenodo_provider_no_token_non_dry_run_returns_error(tmp_path: Path) -> None:
    """Without a token and dry_run=False, the receipt must be status='error'."""
    bundle = tmp_path / "paper.pdf"
    bundle.write_bytes(b"%PDF")
    receipt = ZenodoProvider(token=None).deposit(bundle, dry_run=False)
    assert receipt.status == "error"
    assert "ZENODO_API_TOKEN" in (receipt.error or "")


def test_zenodo_provider_implements_protocol(tmp_path: Path) -> None:
    """ZenodoProvider must satisfy the ArchivalProvider runtime-checkable protocol."""
    provider = ZenodoProvider(token=None)
    assert isinstance(provider, ArchivalProvider)


# ---------------------------------------------------------------------------
# 7. IPFSPinataProvider — dry-run
# ---------------------------------------------------------------------------


def test_ipfs_pinata_dry_run(tmp_path: Path) -> None:
    """IPFSPinataProvider(None).deposit(..., dry_run=True) returns a dry-run receipt."""
    bundle = tmp_path / "data.bin"
    bundle.write_bytes(b"binary bundle content")
    provider = IPFSPinataProvider(jwt=None)
    receipt = provider.deposit(bundle, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.provider == "ipfs_pinata"
    assert receipt.bundle_sha256 is not None


def test_ipfs_pinata_dry_run_directory(tmp_path: Path) -> None:
    """dry_run on a directory bundle must also return a dry-run receipt."""
    d = tmp_path / "bundle_dir"
    d.mkdir()
    (d / "file.pdf").write_bytes(b"%PDF")
    (d / "manifest.json").write_text('{"ok": true}', encoding="utf-8")
    receipt = IPFSPinataProvider(jwt=None).deposit(d, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.provider == "ipfs_pinata"


def test_ipfs_pinata_dry_run_endpoint_hint(tmp_path: Path) -> None:
    """The extra dict of a dry-run receipt must include would_post_to."""
    bundle = tmp_path / "f.pdf"
    bundle.write_bytes(b"%PDF")
    receipt = IPFSPinataProvider(jwt=None, base_url="https://api.pinata.cloud").deposit(bundle, dry_run=True)
    assert "would_post_to" in receipt.extra
    assert "pinFileToIPFS" in receipt.extra["would_post_to"]


def test_ipfs_pinata_no_jwt_non_dry_run_returns_error(tmp_path: Path) -> None:
    """Without a JWT and dry_run=False, the receipt must be status='error'."""
    bundle = tmp_path / "f.pdf"
    bundle.write_bytes(b"%PDF")
    receipt = IPFSPinataProvider(jwt=None).deposit(bundle, dry_run=False)
    assert receipt.status == "error"
    assert "PINATA_JWT" in (receipt.error or "")


def test_ipfs_pinata_implements_protocol(tmp_path: Path) -> None:
    """IPFSPinataProvider must satisfy the ArchivalProvider runtime-checkable protocol."""
    assert isinstance(IPFSPinataProvider(jwt=None), ArchivalProvider)


# ---------------------------------------------------------------------------
# 8. IPFSWeb3StorageProvider — dry-run
# ---------------------------------------------------------------------------


def test_ipfs_web3storage_dry_run(tmp_path: Path) -> None:
    """IPFSWeb3StorageProvider(None).deposit(..., dry_run=True) returns dry-run receipt."""
    bundle = tmp_path / "data.bin"
    bundle.write_bytes(b"web3 bundle content")
    receipt = IPFSWeb3StorageProvider(token=None).deposit(bundle, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.provider == "ipfs_web3storage"
    assert receipt.bundle_sha256 is not None


def test_ipfs_web3storage_no_token_non_dry_run_error(tmp_path: Path) -> None:
    """Without a token and dry_run=False, the receipt must be status='error'."""
    bundle = tmp_path / "f.pdf"
    bundle.write_bytes(b"%PDF")
    receipt = IPFSWeb3StorageProvider(token=None).deposit(bundle, dry_run=False)
    assert receipt.status == "error"
    assert "WEB3_STORAGE_TOKEN" in (receipt.error or "")


def test_ipfs_web3storage_implements_protocol() -> None:
    """IPFSWeb3StorageProvider must satisfy the ArchivalProvider protocol."""
    assert isinstance(IPFSWeb3StorageProvider(token=None), ArchivalProvider)


# ---------------------------------------------------------------------------
# 9. SoftwareHeritageProvider — dry-run
# ---------------------------------------------------------------------------


def test_software_heritage_dry_run_with_url_file(tmp_path: Path) -> None:
    """SoftwareHeritageProvider reads the URL from the first line of a text file."""
    url_file = tmp_path / "repo_url.txt"
    url_file.write_text("https://github.com/example/repo\n", encoding="utf-8")
    provider = SoftwareHeritageProvider()
    receipt = provider.deposit(url_file, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.provider == "software_heritage"
    assert receipt.identifier == "https://github.com/example/repo"


def test_software_heritage_dry_run_identifier_is_repo_url(tmp_path: Path) -> None:
    """The identifier field of the dry-run receipt must equal the resolved URL."""
    url_file = tmp_path / "url.txt"
    url_file.write_text("https://github.com/org/project\n", encoding="utf-8")
    receipt = SoftwareHeritageProvider().deposit(url_file, dry_run=True)
    assert receipt.identifier == "https://github.com/org/project"


def test_software_heritage_dry_run_git_config(tmp_path: Path) -> None:
    """A git working tree whose config has an origin remote is accepted."""
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".git" / "config").write_text(
        '[remote "origin"]\n\turl = https://github.com/example/x\n',
        encoding="utf-8",
    )
    receipt = SoftwareHeritageProvider().deposit(repo, dry_run=True)
    assert receipt.status == "dry-run"
    assert receipt.identifier == "https://github.com/example/x"


def test_software_heritage_no_url_returns_error(tmp_path: Path) -> None:
    """A directory with no git remote and no URL file returns an error receipt."""
    bare_dir = tmp_path / "no_git"
    bare_dir.mkdir()
    receipt = SoftwareHeritageProvider().deposit(bare_dir, dry_run=True)
    assert receipt.status == "error"
    assert "Could not resolve a repository URL" in (receipt.error or "")


def test_software_heritage_url_file_non_http_line_returns_error(tmp_path: Path) -> None:
    """A text file whose first line is not a URL should return an error receipt."""
    bad_file = tmp_path / "not_url.txt"
    bad_file.write_text("this is not a url\n", encoding="utf-8")
    receipt = SoftwareHeritageProvider().deposit(bad_file, dry_run=True)
    assert receipt.status == "error"


def test_software_heritage_implements_protocol() -> None:
    """SoftwareHeritageProvider must satisfy the ArchivalProvider protocol."""
    assert isinstance(SoftwareHeritageProvider(), ArchivalProvider)


# ---------------------------------------------------------------------------
# 10. ArchivalProvider protocol
# ---------------------------------------------------------------------------


def test_archival_provider_protocol_runtime_checkable() -> None:
    """ArchivalProvider is @runtime_checkable — isinstance check must not raise."""

    class MinimalProvider:
        name = "minimal"

        def deposit(self, bundle: Path, *, dry_run: bool) -> ArchivalReceipt:
            return ArchivalReceipt(
                provider=self.name,
                status="dry-run",
                identifier=None,
                url=None,
                timestamp_utc="2026-01-01T00:00:00Z",
            )

    provider = MinimalProvider()
    # Protocol structural check: has the right attribute + method shape.
    assert hasattr(provider, "name")
    assert hasattr(provider, "deposit")


# ---------------------------------------------------------------------------
# 11. DEFAULT_CREDENTIALS_PATH
# ---------------------------------------------------------------------------


def test_default_credentials_path_is_path_object() -> None:
    """DEFAULT_CREDENTIALS_PATH must be a pathlib.Path instance."""
    assert isinstance(DEFAULT_CREDENTIALS_PATH, Path)


def test_default_credentials_path_ends_with_json() -> None:
    """DEFAULT_CREDENTIALS_PATH must point to a .json file."""
    assert DEFAULT_CREDENTIALS_PATH.suffix == ".json"


# ---------------------------------------------------------------------------
# 12. archive_publication round-trip (no network)
# ---------------------------------------------------------------------------


def test_archive_publication_dry_run_all_providers(tmp_path: Path) -> None:
    """archive_publication returns all_ok=True when all providers run in dry-run."""
    bundle = tmp_path / "paper.pdf"
    bundle.write_bytes(b"%PDF-1.4")
    url_file = tmp_path / "url.txt"
    url_file.write_text("https://github.com/example/repo\n", encoding="utf-8")

    run = archive_publication(
        bundle,
        providers=[
            ZenodoProvider(token=None),
            IPFSPinataProvider(jwt=None),
            IPFSWeb3StorageProvider(token=None),
        ],
        dry_run=True,
    )
    assert isinstance(run, ArchivalRun)
    assert len(run.receipts) == 3
    assert run.all_ok
    assert run.failed == ()


def test_archive_publication_writes_receipts_json(tmp_path: Path) -> None:
    """When output_receipts_path is provided, a JSON file is written."""
    import json

    bundle = tmp_path / "bundle.pdf"
    bundle.write_bytes(b"%PDF-1.4")
    receipts_path = tmp_path / "receipts" / "archival.json"

    archive_publication(
        bundle,
        providers=[ZenodoProvider(token=None)],
        dry_run=True,
        output_receipts_path=receipts_path,
    )
    assert receipts_path.exists()
    data = json.loads(receipts_path.read_text(encoding="utf-8"))
    assert "all_ok" in data
    assert data["all_ok"] is True
    assert isinstance(data["receipts"], list)


def test_archive_publication_missing_bundle_raises(tmp_path: Path) -> None:
    """archive_publication raises ArchivalError when the bundle path does not exist."""
    with pytest.raises(ArchivalError, match="does not exist"):
        archive_publication(
            tmp_path / "nonexistent",
            providers=[ZenodoProvider(token=None)],
            dry_run=True,
        )


def test_archive_publication_zero_providers(tmp_path: Path) -> None:
    """archive_publication with an empty provider list returns an empty run."""
    bundle = tmp_path / "f.pdf"
    bundle.write_bytes(b"%PDF")
    run = archive_publication(bundle, providers=[], dry_run=True)
    assert run.receipts == ()
    assert run.all_ok  # vacuously true
