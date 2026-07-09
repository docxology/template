"""Integrity manifest creation, persistence, and verification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.files.operations import calculate_file_hash
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def create_integrity_manifest(output_dir: Path) -> dict[str, Any]:
    """Create an integrity manifest for all output files."""
    manifest: dict[str, Any] = {
        "timestamp": output_dir.stat().st_ctime if output_dir.exists() else None,
        "file_count": 0,
        "total_size": 0,
        "file_hashes": {},
        "directory_structure": {},
    }

    if not output_dir.exists():
        return manifest

    file_count = 0
    total_size = 0

    for item in output_dir.rglob("*"):
        if item.is_file():
            rel_path = str(item.relative_to(output_dir))
            file_hash = calculate_file_hash(item)
            file_size = item.stat().st_size

            manifest["file_hashes"][rel_path] = {
                "hash": file_hash,
                "size": file_size,
                "modified": item.stat().st_mtime,
            }

            file_count += 1
            total_size += file_size

    manifest["file_count"] = file_count
    manifest["total_size"] = total_size

    for dir_path in output_dir.rglob("*"):
        if dir_path.is_dir():
            rel_path = str(dir_path.relative_to(output_dir))
            manifest["directory_structure"][rel_path] = {
                "file_count": len(list(dir_path.glob("*"))),
                "total_size": sum(f.stat().st_size for f in dir_path.glob("*") if f.is_file()),
            }

    return manifest


def save_integrity_manifest(manifest: dict[str, Any], output_path: Path) -> None:
    """Save integrity manifest to JSON file.

    Raises:
        OSError: If the file cannot be written (intentionally not caught — callers
            must handle write failures, unlike ``load_integrity_manifest`` which
            returns None on failure because a missing manifest is a normal state).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        with open(_tmp, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        _tmp.replace(output_path)
    except OSError as e:
        logger.debug("Failed to write integrity manifest to %s: %s", _tmp, e)
        _tmp.unlink(missing_ok=True)
        raise


def load_integrity_manifest(manifest_path: Path) -> dict[str, Any] | None:
    """Load integrity manifest from JSON file, or None on failure.

    Returns None (rather than raising) because a missing or corrupt manifest is
    a normal state during first runs and after output directory cleanup. This is
    intentionally asymmetric with ``save_integrity_manifest`` which raises on
    write failure.
    """
    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result
    except (OSError, json.JSONDecodeError) as e:
        logger.debug(f"Could not load manifest from {manifest_path}: {e}")
        return None


def verify_integrity_against_manifest(
    current_manifest: dict[str, Any], saved_manifest: dict[str, Any]
) -> dict[str, Any]:
    """Verify current integrity against a saved manifest."""
    verification = {
        "file_count_changed": current_manifest["file_count"] != saved_manifest["file_count"],
        "total_size_changed": current_manifest["total_size"] != saved_manifest["total_size"],
        "files_changed": 0,
        "files_added": 0,
        "files_removed": 0,
        "details": {},
    }

    current_files = set(current_manifest["file_hashes"].keys())
    saved_files = set(saved_manifest["file_hashes"].keys())

    for file_path in current_files & saved_files:
        current_hash = current_manifest["file_hashes"][file_path]["hash"]
        saved_hash = saved_manifest["file_hashes"][file_path]["hash"]

        if current_hash != saved_hash:
            verification["files_changed"] += 1
            verification["details"][file_path] = "modified"

    for file_path in current_files - saved_files:
        verification["files_added"] += 1
        verification["details"][file_path] = "added"

    for file_path in saved_files - current_files:
        verification["files_removed"] += 1
        verification["details"][file_path] = "removed"

    return verification
