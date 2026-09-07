"""Archival provider protocol and all concrete provider implementations.

Extracted from infrastructure.publishing.archival. Each provider implements
the ``ArchivalProvider`` protocol; concrete providers handle provider-specific
HTTP details.

``import requests`` is deferred to the first actual network call inside each
provider so that importing this module in a subprocess whose sys.path[0] is
``infrastructure/publishing/`` does not trigger the stdlib ``http`` namespace
conflict caused by the local ``infrastructure/publishing/http.py`` file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from infrastructure.core.exceptions import PublishingError, UploadError
from infrastructure.publishing._adapter_http import iter_bundle_files, lazy_session
from infrastructure.publishing.preflight import PublicationPayloadManifest
from infrastructure.publishing.zenodo.client import ZenodoClient
from infrastructure.publishing.zenodo.config import ZenodoConfig

from .models import (
    ArchivalError,  # noqa: F401 — re-exported for convenience
    ArchivalReceipt,
    _bundle_sha256,
    _missing_credential_receipt,
    _now_utc_iso,
)

__all__ = [
    "ArchivalProvider",
    "ZenodoProvider",
    "IPFSPinataProvider",
    "IPFSWeb3StorageProvider",
    "SoftwareHeritageProvider",
]


@runtime_checkable
class ArchivalProvider(Protocol):
    """Protocol every archival provider must implement.

    ``deposit`` is the only required action: take a bundle (a directory or a
    single file) and return a receipt. ``dry_run=True`` MUST be a no-op that
    still returns a receipt with ``status="dry-run"``.
    """

    name: str

    """Deposit a payload to the archival service."""

    def deposit(
        self,
        bundle: Path,
        *,
        dry_run: bool,
        manifest: PublicationPayloadManifest | None = None,
    ) -> ArchivalReceipt:
        """Deposit a bundle to the archival service, returning a receipt."""
        ...


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
        """Initialize the Zenodo provider with an API token and base URL."""
        self._token = token
        self._base_url = base_url.rstrip("/")

    def deposit(
        self,
        bundle: Path,
        *,
        dry_run: bool,
        manifest: PublicationPayloadManifest | None = None,
    ) -> ArchivalReceipt:
        """Deposit a payload to the archival service."""
        if manifest is not None:
            manifest.validate_current(bundle)
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

        import requests  # noqa: PLC0415 — deferred; see module docstring

        try:
            client = ZenodoClient(ZenodoConfig(access_token=self._token, base_url=self._base_url))
            deposition = client.create_deposition()

            for file_path in iter_bundle_files(bundle):
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


# ---------------------------------------------------------------------------
# IPFS — Pinata
# ---------------------------------------------------------------------------


class IPFSPinataProvider:
    """Pin a bundle to IPFS via Pinata's pinFileToIPFS endpoint.

    For a directory bundle, Pinata's "wrap with directory" option produces a
    single CID for the whole tree.

    ``session`` is accepted for testing with pytest-httpserver. When None the
    actual ``requests.Session`` is created lazily on the first real network call
    so that constructing an ``IPFSPinataProvider`` does not trigger a top-level
    ``import requests`` and the associated ``http.client`` resolution.
    """

    name: str = "ipfs_pinata"

    def __init__(
        self,
        jwt: str | None,
        *,
        base_url: str = "https://api.pinata.cloud",
        session: Any | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Pinata provider with a JWT and optional session/timeout."""
        self._jwt = jwt
        self._base_url = base_url.rstrip("/")
        self._session_arg = session  # None → lazily created on first network call
        self._timeout = timeout

    def deposit(
        self,
        bundle: Path,
        *,
        dry_run: bool,
        manifest: PublicationPayloadManifest | None = None,
    ) -> ArchivalReceipt:
        """Deposit a payload to the archival service."""
        if manifest is not None:
            manifest.validate_current(bundle)
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

        import requests  # noqa: PLC0415 — deferred; see module docstring

        try:
            session = lazy_session(self)
            files = self._build_files(bundle)
            resp = session.post(
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
        session: Any | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Web3.Storage provider with a token and optional session/timeout."""
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._session_arg = session
        self._timeout = timeout

    def deposit(
        self,
        bundle: Path,
        *,
        dry_run: bool,
        manifest: PublicationPayloadManifest | None = None,
    ) -> ArchivalReceipt:
        """Deposit a payload to the archival service."""
        if manifest is not None:
            manifest.validate_current(bundle)
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

        import requests  # noqa: PLC0415 — deferred; see module docstring

        try:
            session = lazy_session(self)
            # Web3.Storage supports CAR upload; for the bundle scaffold we POST
            # a tar-balled directory or a single file.
            if bundle.is_file():
                with bundle.open("rb") as fh:
                    resp = session.post(
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
                resp = session.post(
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
        session: Any | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Software Heritage provider with API base and optional session."""
        self._base_url = base_url.rstrip("/")
        self._session_arg = session
        self._timeout = timeout

    def deposit(
        self,
        bundle: Path,
        *,
        dry_run: bool,
        manifest: PublicationPayloadManifest | None = None,
    ) -> ArchivalReceipt:
        """Deposit a payload to the archival service."""
        if manifest is not None:
            manifest.validate_current(bundle)
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

        import requests  # noqa: PLC0415 — deferred; see module docstring

        try:
            session = lazy_session(self)
            resp = session.post(endpoint, timeout=self._timeout)
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

    def check_status(self, repo_url: str) -> ArchivalReceipt:
        """Read-only refresh of Software Heritage's public archival state.

        Queries the credential-free ``GET`` endpoints — the save-code-now
        queue entry and the origin visit history — and records the observed
        state with an as-of timestamp. Never posts: a save request cannot be
        triggered from here, so this is the evidence-only half of the
        archival contract.

        Software Heritage keys origins by exact URL, and Git remotes usually
        carry a trailing ``.git`` while the archived origin does not. Both
        variants are queried when they differ and the strongest evidence
        wins (verified > accepted > pending > excluded > unavailable).

        The recorded ``extra["state"]`` uses the tracker taxonomy:
        ``verified`` (a full visit or any visit exists), ``accepted`` /
        ``pending`` (queued, not yet archived), ``excluded`` (rejected or
        failed), ``unavailable`` (no save request and no visits), and
        ``rate-limited`` (the API answered 429). ``status`` stays ``ok``
        whenever all observations completed; only transport failures yield
        ``status = "error"``.
        """
        candidates = [repo_url]
        if repo_url.endswith(".git"):
            stripped = repo_url[: -len(".git")]
            if stripped and stripped not in candidates:
                candidates.append(stripped)

        import requests  # noqa: PLC0415 — deferred; see module docstring

        extra: dict[str, str] = {"repo_url": repo_url}
        states: list[str] = []
        try:
            session = lazy_session(self)
            for index, candidate in enumerate(candidates):
                suffix = "" if index == 0 else f"_normalized_{index}"
                save_url = f"{self._base_url}/origin/save/git/url/{candidate}/"
                visits_url = f"{self._base_url}/origin/{candidate}/visits/"
                save_resp = session.get(save_url, timeout=self._timeout)
                visits_resp = session.get(visits_url, timeout=self._timeout)
                if save_resp.status_code == 429 or visits_resp.status_code == 429:
                    return ArchivalReceipt(
                        provider=self.name,
                        status="ok",
                        identifier=repo_url,
                        url=save_url,
                        timestamp_utc=_now_utc_iso(),
                        bundle_sha256=None,
                        extra={**extra, "state": "rate-limited"},
                    )

                save_payload: dict = {}
                if save_resp.status_code == 200:
                    try:
                        raw_save = save_resp.json()
                    except ValueError:
                        raw_save = None
                    # SWH's save endpoint answers with a single object or a
                    # list of requests; the most recent entry carries the
                    # current state.
                    if isinstance(raw_save, list):
                        save_payload = next((e for e in raw_save if isinstance(e, dict)), {})
                    elif isinstance(raw_save, dict):
                        save_payload = raw_save
                visits: list = []
                if visits_resp.status_code == 200:
                    try:
                        raw_visits = visits_resp.json()
                    except ValueError:
                        raw_visits = None
                    visits = [e for e in raw_visits if isinstance(e, dict)] if isinstance(raw_visits, list) else []

                request_status = str(save_payload.get("save_request_status") or "")
                extra.update(
                    {
                        f"save_request_status{suffix}": request_status
                        or ("none" if save_resp.status_code == 404 else f"http_{save_resp.status_code}"),
                        f"save_task_status{suffix}": str(save_payload.get("save_task_status") or ""),
                        f"visit_status{suffix}": str(save_payload.get("visit_status") or ""),
                        f"visit_count{suffix}": str(len(visits))
                        if visits_resp.status_code == 200
                        else f"http_{visits_resp.status_code}",
                    }
                )
                if str(save_payload.get("visit_status") or "") == "full" or visits:
                    states.append("verified")
                elif request_status in {"rejected", "failed"}:
                    states.append("excluded")
                elif request_status == "pending":
                    states.append("pending")
                elif request_status == "accepted":
                    states.append("accepted")
                else:
                    states.append("unavailable")
        except requests.RequestException as exc:
            return ArchivalReceipt(
                provider=self.name,
                status="error",
                identifier=repo_url,
                url=f"{self._base_url}/origin/save/git/url/{repo_url}/",
                timestamp_utc=_now_utc_iso(),
                bundle_sha256=None,
                error=f"Software Heritage HTTP error: {exc}",
            )

        precedence = {"verified": 0, "accepted": 1, "pending": 2, "excluded": 3, "unavailable": 4}
        state = min(states, key=lambda value: precedence[value])
        return ArchivalReceipt(
            provider=self.name,
            status="ok",
            identifier=repo_url,
            url=f"{self._base_url}/origin/save/git/url/{candidates[0]}/",
            timestamp_utc=_now_utc_iso(),
            bundle_sha256=None,
            error=None,
            extra={**extra, "state": state},
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
