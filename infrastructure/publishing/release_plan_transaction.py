"""Retained, compensating metadata transaction; no remote or resolver effects.

Files are individually atomically replaced. The journal permits exact rollback
after interruption; this is not a filesystem-wide atomic commit. Concurrent
writers are unsupported and unexpected bytes are preserved, never overwritten.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined
from infrastructure.publishing.release_plan import (
    MAX_BYTES,
    _prepare,
    canonical,
    check_release_plan,
    git,
    read_input,
    sha256,
)


def _identity(root: Path) -> tuple[int, int]:
    observed = root.stat()
    return observed.st_dev, observed.st_ino


def _save(root: Path, path: Path, body: bytes, mode: int) -> None:
    atomic_write_text_confined(root, path, body.decode(), mode=mode, expected_root_identity=_identity(root))


def apply_release_plan(root: Path, plan: dict[str, Any], *, reviewed_sha256: str, journal: Path) -> dict[str, Any]:
    """Validate the exact review, retain all originals, apply and read back.

    The caller must serialize repository edits. Automatic rollback refuses any
    unrelated mutation; exact backups remain available if rollback is blocked.
    """
    root = root.absolute()
    journal = journal.absolute()
    if sha256(canonical(plan)) != reviewed_sha256:
        raise ValueError("release plan does not match the explicitly reviewed SHA256")
    check_release_plan(root, plan)
    actual, after = _prepare(root, plan["root_after"], plan["root_before"])
    if actual != plan:
        raise ValueError("release plan changed before application")
    if journal.is_relative_to(root) or journal.exists() or journal.is_symlink():
        raise ValueError("release journal must be fresh and outside the checkout")
    if journal.parent.resolve(strict=True) != journal.parent:
        raise ValueError("release journal ancestors must be real canonical directories")
    journal.mkdir(mode=0o700)
    modes = {row["path"]: row["mode"] for row in plan["inputs"]}
    # Complete backups are published before journal.json authorizes any writes.
    for index, row in enumerate(plan["changes"]):
        body, mode = read_input(root, row["path"])
        if sha256(body) != row["before_sha256"] or mode != modes[row["path"]]:
            raise ValueError("release target changed before backup")
        _save(journal, journal / f"{index:04d}.before", body, 0o600)
    record = {
        "schema_version": "template-release-plan-journal-v1",
        "root": str(root),
        "root_identity": list(_identity(root)),
        "reviewed_sha256": reviewed_sha256,
        "plan": plan,
    }
    _save(journal, journal / "journal.json", canonical(record), 0o600)
    # Check all fixed and unchanged inputs again after journal preparation.
    check_release_plan(root, plan)
    try:
        for row in plan["changes"]:
            path = row["path"]
            body, mode = read_input(root, path)
            if sha256(body) != row["before_sha256"] or mode != modes[path]:
                raise ValueError("release target changed before atomic replacement")
            _save(root, root / path, after[path], mode)
        for row in plan["inputs"]:
            expected = after.get(row["path"])
            body, mode = read_input(root, row["path"])
            if sha256(body) != (sha256(expected) if expected is not None else row["sha256"]) or mode != row["mode"]:
                raise ValueError("release transaction closing readback differs")
        if git(root, "rev-parse", "HEAD").decode().strip() != plan["base_commit"]:
            raise ValueError("Git HEAD changed during release transaction")
    except BaseException:
        rollback_release_plan(root, journal, reviewed_sha256=reviewed_sha256)
        raise
    result = {
        "role": "metadata-preparation-only",
        "reviewed_sha256": reviewed_sha256,
        "changed_files": len(plan["changes"]),
        "required_followup": plan["required_followup"],
    }
    _save(journal, journal / "applied.json", canonical(result), 0o600)
    return result


def rollback_release_plan(root: Path, journal: Path, *, reviewed_sha256: str) -> None:
    """Restore only reviewed before/after bytes; reject foreign data or HEAD."""
    root, journal = root.absolute(), journal.absolute()
    record = json.loads(read_bytes_confined(journal, journal / "journal.json"))
    plan = record["plan"]
    if (
        record.get("schema_version") != "template-release-plan-journal-v1"
        or record["root"] != str(root)
        or record["root_identity"] != list(_identity(root))
        or record["reviewed_sha256"] != reviewed_sha256
        or sha256(canonical(plan)) != reviewed_sha256
        or git(root, "rev-parse", "HEAD").decode().strip() != plan["base_commit"]
    ):
        raise ValueError("rollback journal is not bound to the reviewed repository and plan")
    # Reconstruct the old plan in memory by temporarily reading backup metadata
    # is intentionally avoided: no caller-controlled path may enlarge writes.
    allowed = {
        row["path"]
        for row in plan["inputs"]
        if row["path"].endswith(("/pyproject.toml", "/uv.lock", "/manuscript/config.yaml"))
        or row["path"] in {"pyproject.toml", "uv.lock"}
    }
    from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

    canonical_paths = {name for name in ("pyproject.toml", "uv.lock")}
    canonical_paths.update(
        f"projects/{scope}/{name}"
        for scope in PUBLIC_PROJECT_NAMES
        for name in ("pyproject.toml", "uv.lock", "manuscript/config.yaml")
    )
    if not allowed <= canonical_paths or len({row["path"] for row in plan["changes"]}) != len(plan["changes"]):
        raise ValueError("rollback plan contains noncanonical or repeated writes")
    modes = {row["path"]: row["mode"] for row in plan["inputs"]}
    backups = []
    for index, row in enumerate(plan["changes"]):
        if row["path"] not in allowed:
            raise ValueError("rollback target is outside the canonical metadata manifest")
        before = read_bytes_confined(journal, journal / f"{index:04d}.before", max_bytes=MAX_BYTES)
        current, mode = read_input(root, row["path"])
        if (
            sha256(before) != row["before_sha256"]
            or sha256(current) not in {row["before_sha256"], row["after_sha256"]}
            or mode != modes[row["path"]]
        ):
            raise ValueError("rollback refuses changed backups or unrelated current bytes")
        backups.append((row["path"], before, mode))
    for path, before, mode in reversed(backups):
        if read_input(root, path) != (before, mode):
            _save(root, root / path, before, mode)
    for path, before, mode in backups:
        if read_input(root, path) != (before, mode):
            raise ValueError("rollback closing readback differs from retained original")
    _save(journal, journal / "rolled-back.json", canonical({"reviewed_sha256": reviewed_sha256}), 0o600)
