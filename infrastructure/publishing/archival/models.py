"""Data models, error types, and private helpers for archival publishing.

Extracted from infrastructure.publishing.archival so providers and the
orchestrator can import a shared type surface without circular imports.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

__all__ = [
    "ArchivalError",
    "ArchivalReceipt",
    "ArchivalRun",
    "ArchivalCredentials",
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


# ---------------------------------------------------------------------------
# Private helpers (consumed by providers and orchestrate)
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _bundle_sha256(bundle: Path) -> str:
    """SHA-256 of the bundle. For a directory, hashes the per-file hashes in path order."""

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
