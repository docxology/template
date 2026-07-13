"""Append-only publication release ledger for transmission bookends."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing.release_pairing import validate_release_pairing

logger = get_logger(__name__)

LEDGER_SCHEMA = "template-publication-ledger-v1"


def ledger_path_for_project(project_root: Path) -> Path:
    """Return the on-disk ledger path under a project workspace."""
    return project_root / "output" / "data" / "publication_ledger.json"


def _empty_ledger() -> dict[str, Any]:
    return {"schema": LEDGER_SCHEMA, "releases": []}


def _release_key(entry: dict[str, Any]) -> tuple[str, str]:
    return (str(entry.get("tag") or ""), str(entry.get("pdf_sha256") or ""))


def _entry_from_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    current = {
        "doi": receipt.get("doi"),
        "github_release_url": receipt.get("github_release_url"),
        "pdf_sha256": receipt.get("pdf_sha256"),
    }
    pairing = validate_release_pairing(current, require_doi=bool(receipt.get("doi")))
    return {
        "tag": receipt.get("tag"),
        "doi": receipt.get("doi"),
        "github_release_url": receipt.get("github_release_url"),
        "github_repo": receipt.get("github_repo"),
        "pdf_sha256": receipt.get("pdf_sha256"),
        "timestamp": receipt.get("timestamp"),
        "sandbox": receipt.get("sandbox"),
        "dry_run": receipt.get("dry_run"),
        "pairing_valid": pairing.valid,
    }


def write_publication_ledger(ledger_path: Path, ledger: dict[str, Any]) -> Path:
    """Persist a ledger payload to disk."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ledger_path


def append_release_entry(ledger_path: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    """Append a release receipt when ``(tag, pdf_sha256)`` is new."""
    if ledger_path.is_file():
        loaded = json.loads(ledger_path.read_text(encoding="utf-8"))
        ledger = loaded if isinstance(loaded, dict) else _empty_ledger()
    else:
        ledger = _empty_ledger()

    releases = list(ledger.get("releases") or [])
    entry = _entry_from_receipt(receipt)
    key = _release_key(entry)
    existing_keys = {_release_key(item) for item in releases if isinstance(item, dict)}
    if key not in existing_keys:
        releases.append(entry)
    ledger["schema"] = LEDGER_SCHEMA
    ledger["releases"] = releases
    write_publication_ledger(ledger_path, ledger)
    return ledger


def _receipt_path_candidates(repo_root: Path, project_name: str) -> list[Path]:
    return [
        repo_root / "output" / project_name / "release_bundle" / "RELEASE_RECEIPT.json",
        repo_root / "projects" / project_name / "output" / "release_bundle" / "RELEASE_RECEIPT.json",
    ]


def load_publication_ledger(
    project_root: Path,
    *,
    repo_root: Path | None = None,
    project_name: str | None = None,
) -> dict[str, Any]:
    """Load the ledger file, backfilling from ``RELEASE_RECEIPT.json`` when empty."""
    ledger_path = ledger_path_for_project(project_root)
    if ledger_path.is_file():
        loaded = json.loads(ledger_path.read_text(encoding="utf-8"))
        payload: dict[str, Any] = loaded if isinstance(loaded, dict) else _empty_ledger()
        if payload.get("releases"):
            return payload

    resolved_repo = repo_root or project_root.parent.parent
    resolved_name = project_name or project_root.name
    for receipt_path in _receipt_path_candidates(resolved_repo, resolved_name):
        if not receipt_path.is_file():
            continue
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read receipt %s: %s", receipt_path, exc)
            continue
        return append_release_entry(ledger_path, receipt)

    return _empty_ledger()
