"""Multi-target archival publishing for long-horizon redundancy.

Mirrors a publication bundle to N independent archival targets so that no
single archive's policy change can erase the artifact. Currently supported:

- Zenodo (CERN-backed, DOI assignment)
- IPFS via Pinata (content-addressed pinning)
- IPFS via Web3.Storage (content-addressed pinning, independent provider)
- Software Heritage (cross-host source-code archival via save-code-now)

Design rationale and threat scenarios mitigated:
``docs/maintenance/archival-targets.md``.

This module is intentionally a thin orchestrator. Each provider implements the
``ArchivalProvider`` protocol; concrete providers handle the provider-specific
HTTP details. The module does not invent cryptography, does not retry
indefinitely, and does not perform network operations without explicit opt-in
from the caller. ``dry_run=True`` is the default at every layer so accidental
imports cannot trigger real deposits.

Credentials are read from environment variables first (preferred for CI), then
from ``~/.config/template-archival/credentials.json`` as a fallback. Tokens are
never logged.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

import requests

from infrastructure.core.exceptions import PublishingError, UploadError
from infrastructure.publishing.zenodo.client import ZenodoClient
from infrastructure.publishing.zenodo.config import ZenodoConfig

__all__ = [
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
]


DEFAULT_CREDENTIALS_PATH: Final[Path] = Path.home() / ".config" / "template-archival" / "credentials.json"


class ArchivalError(Exception):
    """Raised when an archival deposit fails in a way the caller should see.

    Network/transport failures are wrapped in this so callers don't have to
    catch ``requests`` exceptions directly.
    """


@dataclass(frozen=True)
class ArchivalReceipt:
    """Structured record of a single archival deposit attempt.

    A successful receipt carries the canonical identifier returned by the
    provider (DOI, IPFS CID, SWHID). A failed receipt carries ``status =
    "error"`` and an ``error`` message. Receipts are committed to the
    publication branch as ``ARCHIVAL_RECEIPTS.json`` so future maintainers can
    re-verify deposits.
    """

    provider: str
    status: str  # "ok" | "error" | "dry-run"
    identifier: str | None
    url: str | None
    timestamp_utc: str
    bundle_sha256: str | None = None
    error: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ArchivalRun:
    """Aggregate result of an ``archive_publication`` call.

    Provides a quick view over all per-provider receipts plus convenience
    properties for "did all succeed" and "which ones failed."
    """

    bundle_path: str
    receipts: tuple[ArchivalReceipt, ...]
    started_utc: str
    finished_utc: str

    @property
    def all_ok(self) -> bool:
        """True if every receipt is status == "ok" (dry-run counts as ok)."""

        return all(r.status in {"ok", "dry-run"} for r in self.receipts)

    @property
    def failed(self) -> tuple[ArchivalReceipt, ...]:
        """Receipts with status == "error"."""

        return tuple(r for r in self.receipts if r.status == "error")

    def to_dict(self) -> dict[str, object]:
        """Serialize for committing to ``ARCHIVAL_RECEIPTS.json``."""

        return {
            "bundle_path": self.bundle_path,
            "started_utc": self.started_utc,
            "finished_utc": self.finished_utc,
            "all_ok": self.all_ok,
            "receipts": [asdict(r) for r in self.receipts],
        }


@dataclass(frozen=True)
class ArchivalCredentials:
    """Credentials for the supported providers.

    Any field may be ``None`` — providers whose credentials are missing emit
    a structured "error" receipt rather than raising, so a partial run is
    visible in the receipts file.
    """

    zenodo_token: str | None = None
    pinata_jwt: str | None = None
    web3_storage_token: str | None = None
    # Software Heritage save-code-now does not require a token for public repos.


@runtime_checkable
class ArchivalProvider(Protocol):
    """Protocol every archival provider must implement.

    ``deposit`` is the only required action: take a bundle (a directory or a
    single file) and return a receipt. ``dry_run=True`` MUST be a no-op that
    still returns a receipt with ``status="dry-run"``.
    """

    name: str

    def deposit(self, bundle: Path, *, dry_run: bool) -> ArchivalReceipt: ...


# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------


def load_credentials(
    *,
    env: dict[str, str] | None = None,
    credentials_path: Path | None = None,
) -> ArchivalCredentials:
    """Read provider credentials from env vars first, then a JSON file.

    Env vars (preferred — they don't end up in a file by accident):

    - ``ZENODO_API_TOKEN``
    - ``PINATA_JWT``
    - ``WEB3_STORAGE_TOKEN``

    JSON fallback structure (at ``~/.config/template-archival/credentials.json``)::

        {
            "zenodo_token": "...",
            "pinata_jwt": "...",
            "web3_storage_token": "..."
        }

    Either source can be partially populated; missing credentials surface in
    the per-provider receipt rather than as an exception.
    """

    source_env = env if env is not None else dict(os.environ)
    path = credentials_path if credentials_path is not None else DEFAULT_CREDENTIALS_PATH

    file_data: dict[str, str] = {}
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ArchivalError(f"Credentials file at {path} exists but is not valid JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ArchivalError(f"Credentials file at {path} must contain a JSON object, got {type(raw).__name__}")
        file_data = {str(k): str(v) for k, v in raw.items() if isinstance(v, (str, int))}

    def _read(env_key: str, file_key: str) -> str | None:
        return source_env.get(env_key) or file_data.get(file_key) or None

    return ArchivalCredentials(
        zenodo_token=_read("ZENODO_API_TOKEN", "zenodo_token"),
        pinata_jwt=_read("PINATA_JWT", "pinata_jwt"),
        web3_storage_token=_read("WEB3_STORAGE_TOKEN", "web3_storage_token"),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _bundle_sha256(bundle: Path) -> str:
    """SHA-256 of the bundle. For a directory, hashes the per-file hashes in path order."""

    import hashlib

    h = hashlib.sha256()
    if bundle.is_file():
        h.update(bundle.read_bytes())
        return h.hexdigest()

    for file_path in sorted(bundle.rglob("*")):
        if not file_path.is_file():
            continue
        h.update(str(file_path.relative_to(bundle)).encode("utf-8"))
        h.update(b"\x00")
        h.update(hashlib.sha256(file_path.read_bytes()).digest())
    return h.hexdigest()


def _missing_credential_receipt(provider_name: str, missing: str) -> ArchivalReceipt:
    return ArchivalReceipt(
        provider=provider_name,
        status="error",
        identifier=None,
        url=None,
        timestamp_utc=_now_utc_iso(),
        error=f"Missing credential: {missing}. See docs/maintenance/archival-targets.md.",
    )


# ---------------------------------------------------------------------------
# Zenodo
# ---------------------------------------------------------------------------


class ZenodoProvider:
    """Zenodo REST API deposit provider.

    Creates a new deposition, uploads each file in the bundle, publishes, and
    returns the assigned DOI. For dry_run, returns a receipt that includes
    what would have been deposited.

    Archival deposits use empty deposition metadata (bundle mirror only). Use
    ``publish_to_zenodo`` or ``cli.publish_zenodo_command`` for rich metadata.
    """

    name: str = "zenodo"

    def __init__(
        self,
        token: str | None,
        *,
        base_url: str = "https://zenodo.org/api",
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")

    def deposit(self, bundle: Path, *, dry_run: bool) -> ArchivalReceipt:
        sha = _bundle_sha256(bundle)

        if dry_run:
            return ArchivalReceipt(
                provider=self.name,
                status="dry-run",
                identifier=None,
                url=None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                extra={"would_post_to": f"{self._base_url}/deposit/depositions"},
            )

        if not self._token:
            return _missing_credential_receipt(self.name, "ZENODO_API_TOKEN")

        try:
            client = ZenodoClient(ZenodoConfig(access_token=self._token, base_url=self._base_url))
            deposition = client.create_deposition()

            for file_path in self._iter_files(bundle):
                object_key = str(file_path.relative_to(bundle.parent))
                client.upload_file(
                    deposition.bucket_url,
                    file_path,
                    object_key=object_key,
                )

            doi = client.publish(deposition.deposition_id)

            return ArchivalReceipt(
                provider=self.name,
                status="ok",
                identifier=doi or None,
                url=f"https://doi.org/{doi}" if doi else None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                extra={"deposition_id": deposition.deposition_id},
            )
        except (PublishingError, UploadError, requests.RequestException) as exc:
            return ArchivalReceipt(
                provider=self.name,
                status="error",
                identifier=None,
                url=None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                error=f"Zenodo HTTP error: {exc}",
            )

    @staticmethod
    def _iter_files(bundle: Path) -> list[Path]:
        if bundle.is_file():
            return [bundle]
        return [p for p in sorted(bundle.rglob("*")) if p.is_file()]


# ---------------------------------------------------------------------------
# IPFS — Pinata
# ---------------------------------------------------------------------------


class IPFSPinataProvider:
    """Pin a bundle to IPFS via Pinata's pinFileToIPFS endpoint.

    For a directory bundle, Pinata's "wrap with directory" option produces a
    single CID for the whole tree.
    """

    name: str = "ipfs_pinata"

    def __init__(
        self,
        jwt: str | None,
        *,
        base_url: str = "https://api.pinata.cloud",
        session: requests.Session | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._jwt = jwt
        self._base_url = base_url.rstrip("/")
        self._session = session if session is not None else requests.Session()
        self._timeout = timeout

    def deposit(self, bundle: Path, *, dry_run: bool) -> ArchivalReceipt:
        sha = _bundle_sha256(bundle)

        if dry_run:
            return ArchivalReceipt(
                provider=self.name,
                status="dry-run",
                identifier=None,
                url=None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                extra={"would_post_to": f"{self._base_url}/pinning/pinFileToIPFS"},
            )

        if not self._jwt:
            return _missing_credential_receipt(self.name, "PINATA_JWT")

        try:
            files = self._build_files(bundle)
            resp = self._session.post(
                f"{self._base_url}/pinning/pinFileToIPFS",
                headers={"Authorization": f"Bearer {self._jwt}"},
                files=files,
                data={"pinataOptions": json.dumps({"wrapWithDirectory": bundle.is_dir()})},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            payload = resp.json()
            cid = str(payload.get("IpfsHash") or "")
            return ArchivalReceipt(
                provider=self.name,
                status="ok" if cid else "error",
                identifier=cid or None,
                url=f"https://gateway.pinata.cloud/ipfs/{cid}" if cid else None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                error=None if cid else f"Pinata response missing IpfsHash: {payload!r}",
            )
        except requests.RequestException as exc:
            return ArchivalReceipt(
                provider=self.name,
                status="error",
                identifier=None,
                url=None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                error=f"Pinata HTTP error: {exc}",
            )

    @staticmethod
    def _build_files(bundle: Path) -> list[tuple[str, tuple[str, bytes]]]:
        if bundle.is_file():
            return [("file", (bundle.name, bundle.read_bytes()))]
        items: list[tuple[str, tuple[str, bytes]]] = []
        for p in sorted(bundle.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(bundle.parent)
            items.append(("file", (str(rel), p.read_bytes())))
        return items


# ---------------------------------------------------------------------------
# IPFS — Web3.Storage
# ---------------------------------------------------------------------------


class IPFSWeb3StorageProvider:
    """Pin a bundle to IPFS via Web3.Storage's HTTP upload endpoint."""

    name: str = "ipfs_web3storage"

    def __init__(
        self,
        token: str | None,
        *,
        base_url: str = "https://api.web3.storage",
        session: requests.Session | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._session = session if session is not None else requests.Session()
        self._timeout = timeout

    def deposit(self, bundle: Path, *, dry_run: bool) -> ArchivalReceipt:
        sha = _bundle_sha256(bundle)

        if dry_run:
            return ArchivalReceipt(
                provider=self.name,
                status="dry-run",
                identifier=None,
                url=None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                extra={"would_post_to": f"{self._base_url}/upload"},
            )

        if not self._token:
            return _missing_credential_receipt(self.name, "WEB3_STORAGE_TOKEN")

        try:
            # Web3.Storage supports CAR upload; for the bundle scaffold we POST
            # a tar-balled directory or a single file.
            if bundle.is_file():
                with bundle.open("rb") as fh:
                    resp = self._session.post(
                        f"{self._base_url}/upload",
                        headers={"Authorization": f"Bearer {self._token}"},
                        data=fh,
                        timeout=self._timeout,
                    )
            else:
                import io
                import tarfile

                buf = io.BytesIO()
                with tarfile.open(fileobj=buf, mode="w") as tar:
                    tar.add(bundle, arcname=bundle.name)
                buf.seek(0)
                resp = self._session.post(
                    f"{self._base_url}/upload",
                    headers={"Authorization": f"Bearer {self._token}"},
                    data=buf.getvalue(),
                    timeout=self._timeout,
                )

            resp.raise_for_status()
            payload = resp.json()
            cid = str(payload.get("cid") or "")
            return ArchivalReceipt(
                provider=self.name,
                status="ok" if cid else "error",
                identifier=cid or None,
                url=f"https://w3s.link/ipfs/{cid}" if cid else None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                error=None if cid else f"Web3.Storage response missing cid: {payload!r}",
            )
        except requests.RequestException as exc:
            return ArchivalReceipt(
                provider=self.name,
                status="error",
                identifier=None,
                url=None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                error=f"Web3.Storage HTTP error: {exc}",
            )


# ---------------------------------------------------------------------------
# Software Heritage
# ---------------------------------------------------------------------------


class SoftwareHeritageProvider:
    """Trigger Software Heritage's save-code-now for a public Git repository.

    Software Heritage harvests automatically over time, but save-code-now lets
    you request immediate archival. This provider is unusual because it
    deposits a URL reference (not a bundle); ``bundle`` is interpreted as a
    file containing the repository URL on the first line, or the path to a
    git working tree whose ``origin`` remote will be used.
    """

    name: str = "software_heritage"

    def __init__(
        self,
        *,
        base_url: str = "https://archive.softwareheritage.org/api/1",
        session: requests.Session | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = session if session is not None else requests.Session()
        self._timeout = timeout

    def deposit(self, bundle: Path, *, dry_run: bool) -> ArchivalReceipt:
        sha = _bundle_sha256(bundle)
        repo_url = self._resolve_repo_url(bundle)

        if repo_url is None:
            return ArchivalReceipt(
                provider=self.name,
                status="error",
                identifier=None,
                url=None,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                error=(
                    "Could not resolve a repository URL from the bundle. Software Heritage "
                    "archives Git origins, not bundle files. Pass a directory containing a "
                    "git working tree with an 'origin' remote, or a text file whose first "
                    "line is the repository URL."
                ),
            )

        endpoint = f"{self._base_url}/origin/save/git/url/{repo_url}/"

        if dry_run:
            return ArchivalReceipt(
                provider=self.name,
                status="dry-run",
                identifier=repo_url,
                url=endpoint,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                extra={"would_post_to": endpoint},
            )

        try:
            resp = self._session.post(endpoint, timeout=self._timeout)
            resp.raise_for_status()
            payload = resp.json()
            request_status = str(payload.get("save_request_status") or "")
            visit_id = str(payload.get("id") or "")
            return ArchivalReceipt(
                provider=self.name,
                status="ok" if request_status in {"accepted", "pending"} else "error",
                identifier=visit_id or repo_url,
                url=endpoint,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                extra={
                    "save_request_status": request_status,
                    "repo_url": repo_url,
                },
                error=(
                    None
                    if request_status in {"accepted", "pending"}
                    else f"Unexpected save_request_status: {request_status!r}"
                ),
            )
        except requests.RequestException as exc:
            return ArchivalReceipt(
                provider=self.name,
                status="error",
                identifier=None,
                url=endpoint,
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=sha,
                error=f"Software Heritage HTTP error: {exc}",
            )

    @staticmethod
    def _resolve_repo_url(bundle: Path) -> str | None:
        if bundle.is_file():
            first_line = bundle.read_text(encoding="utf-8").splitlines()[:1]
            if not first_line:
                return None
            candidate = first_line[0].strip()
            return candidate if candidate.startswith(("http://", "https://", "git@")) else None

        git_config = bundle / ".git" / "config"
        if not git_config.exists():
            return None
        for line in git_config.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("url = "):
                return line[len("url = ") :].strip()
        return None


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def archive_publication(
    bundle: Path,
    *,
    providers: list[ArchivalProvider],
    dry_run: bool = True,
    output_receipts_path: Path | None = None,
) -> ArchivalRun:
    """Mirror a publication bundle to N independent archival targets.

    ``dry_run=True`` is the default — pass ``dry_run=False`` to actually
    perform network deposits. The function NEVER raises on per-provider
    failure; failures surface as ``status="error"`` receipts in the run.

    If ``output_receipts_path`` is provided, the run's serialized result is
    written there as JSON (recommended: commit this file alongside the
    publication).
    """

    if not bundle.exists():
        raise ArchivalError(f"Bundle path does not exist: {bundle}")

    started = _now_utc_iso()
    receipts = tuple(provider.deposit(bundle, dry_run=dry_run) for provider in providers)
    finished = _now_utc_iso()

    run = ArchivalRun(
        bundle_path=str(bundle),
        receipts=receipts,
        started_utc=started,
        finished_utc=finished,
    )

    if output_receipts_path is not None:
        output_receipts_path.parent.mkdir(parents=True, exist_ok=True)
        output_receipts_path.write_text(
            json.dumps(run.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return run
