"""Retain literature producer originals before auxiliary capability admission."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.testing._ci_execution_files import _export, _remaining
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json


def retain_literature_originals(
    root: Path, project: Path, receipt: Path, directory: Path, deadline: float
) -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
    """Copy every regular original through the existing bounded stable transport."""
    base = project / "output/.pipeline/literature_acceptance"
    if (
        receipt.name != "receipt.json"
        or receipt.parent.parent != base
        or receipt.parent.resolve(strict=True) != receipt.parent
    ):
        raise ValueError("literature receipt must belong to a fresh child of the selected project run directory")
    destination = evidence_directory(root, directory / "literature-originals", fresh=True)
    destination.mkdir(parents=True)
    excluded: list[str] = []
    total = _export(receipt.parent, destination, deadline, exclusions=excluded)
    if excluded:
        raise ValueError("literature original transport cannot exclude producer files")
    native, bound, raw_receipt = _read_retained_literature_receipt(root, destination, directory)
    records = {}
    for path in sorted(destination.rglob("*")):
        _remaining(deadline)
        if path.is_symlink():
            raise ValueError("literature original transport refuses symlinks")
        if path.is_file():
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            records[path.relative_to(destination).as_posix()] = {
                "path": path.relative_to(root).as_posix(),
                "sha256": digest,
                "bytes": path.stat().st_size,
            }
    if records.get("receipt.json", {}).get("sha256") != raw_receipt["sha256"]:
        raise ValueError("retained literature receipt changed after bounded parsing")
    originals = write_json(
        root,
        directory / "literature-originals.json",
        {
            "receipt": bound,
            "original_receipt": raw_receipt,
            "bytes": total,
            "files": records,
            "acceptance_granted": False,
        },
    )
    _remaining(deadline)
    return native, bound, originals


def _read_retained_literature_receipt(
    root: Path, retained: Path, directory: Path
) -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
    """Derive admission DATA and its raw digest from one bounded exported snapshot."""
    path = retained / "receipt.json"
    raw = read_bytes_confined(root, path, max_bytes=32 * 1024 * 1024)
    native = json.loads(raw)
    if not isinstance(native, dict):
        raise ValueError("runtime evidence is not an object")
    bound = write_json(root, directory / "literature-native.json", native)
    original = {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(raw).hexdigest()}
    return native, bound, original


def literature_failure_context(
    native: dict[str, Any], capability: str, receipt: dict[str, str], originals: dict[str, str]
) -> str:
    """Expose bounded outcome/issue fields and retained bindings, never headers or environments."""
    issues = native.get("issues", [])
    summary = {
        "status": native.get("status"),
        "source_unchanged": native.get("source_unchanged"),
        "consumed_unchanged": native.get("consumed_unchanged"),
        "capability": capability,
        "issues": [" ".join(value.split())[:200] for value in issues[:3] if isinstance(value, str)]
        if isinstance(issues, list)
        else [],
    }
    return (
        f"receipt={receipt['path']}@{receipt['sha256']}; "
        f"originals={originals['path']}@{originals['sha256']}; "
        + json.dumps(summary, sort_keys=True, ensure_ascii=True)[:1024]
    )


__all__ = ["retain_literature_originals", "literature_failure_context"]
