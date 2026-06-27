"""Orchestration layer: load_credentials() and archive_publication().

Extracted from infrastructure.publishing.archival. This module coordinates
provider invocations and credential loading; it does not implement any
provider-specific HTTP logic.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import (
    ArchivalCredentials,
    ArchivalError,
    ArchivalReceipt,
    ArchivalRun,
    DEFAULT_CREDENTIALS_PATH,
    _now_utc_iso,
)
from .providers import ArchivalProvider

__all__ = [
    "load_credentials",
    "archive_publication",
]


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
