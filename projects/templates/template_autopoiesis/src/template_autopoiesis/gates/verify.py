"""Verify the integrity of a materialized child project.

Verification recomputes the tree hash from confined regular live files and
compares it with recorded provenance. Full verification also checks the
provenance schema. Selected-spec execution independently binds generator bytes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..core.common import CheckReport, CheckResult
from .integrity import tree_hash_from_content_hashes
from .custody_paths import confined_path


def verify_child(child_root: str | Path) -> CheckReport:
    """Verify that provenance.json exists and tree hash matches live files."""
    child_root = Path(child_root)
    checks: list[CheckResult] = []

    if child_root.is_symlink() or not child_root.is_dir():
        return CheckReport(
            child_root=str(child_root),
            checks=(CheckResult("child_root_confined", False, "child root must be a real directory"),),
        )

    prov_path = child_root / "provenance.json"
    if not prov_path.exists():
        checks.append(CheckResult("provenance_exists", False, "provenance.json missing"))
        return CheckReport(child_root=str(child_root), checks=tuple(checks))

    checks.append(CheckResult("provenance_exists", True))

    try:
        prov_path = confined_path(child_root, "provenance.json", regular=True)
        if prov_path.stat().st_size > 1048576:
            raise ValueError("provenance exceeds the 1MiB custody limit")
        prov = json.loads(prov_path.read_text())
        if not isinstance(prov, dict):
            raise ValueError("provenance must be a mapping")
    except (OSError, ValueError, TypeError) as exc:
        checks.append(CheckResult("provenance_parseable", False, str(exc)))
        return CheckReport(child_root=str(child_root), checks=tuple(checks))

    checks.append(CheckResult("provenance_parseable", True))

    recorded_hash = prov.get("tree_hash", "")
    recorded_files = prov.get("files")
    if (
        not isinstance(recorded_files, list)
        or not recorded_files
        or any(not isinstance(item, str) for item in recorded_files)
        or len(recorded_files) != len(set(recorded_files))
        or not isinstance(recorded_hash, str)
        or not re.fullmatch(r"[0-9a-f]{64}", recorded_hash)
    ):
        checks.append(
            CheckResult(
                "provenance_file_contract", False, "requires nonempty unique file paths and a SHA-256 tree hash"
            )
        )
        return CheckReport(child_root=str(child_root), checks=tuple(checks))

    # Recompute hash from listed files
    live: dict[str, str] = {}
    missing = []
    for rel in recorded_files:
        try:
            fp = confined_path(child_root, rel, regular=True)
            if fp.stat().st_size > 1048576:
                raise ValueError("child source exceeds the 1MiB custody limit")
            live[rel] = fp.read_text()
        except (OSError, ValueError):
            missing.append(rel)

    if missing:
        checks.append(CheckResult("all_files_present", False, f"Missing: {missing[:3]}"))
    else:
        checks.append(CheckResult("all_files_present", True))

    recomputed = tree_hash_from_content_hashes(live)
    if recomputed == recorded_hash:
        checks.append(CheckResult("tree_hash_matches", True))
    else:
        checks.append(
            CheckResult(
                "tree_hash_matches",
                False,
                f"recorded={recorded_hash[:8]} recomputed={recomputed[:8]}",
            )
        )

    return CheckReport(child_root=str(child_root), checks=tuple(checks))


def verify_seal(child_root: str | Path) -> CheckReport:
    """Verify that a seal record exists alongside provenance."""
    child_root = Path(child_root)
    checks: list[CheckResult] = []

    seal_path = child_root / "seal.json"
    if not seal_path.exists():
        checks.append(CheckResult("seal_exists", False, "seal.json missing"))
    else:
        checks.append(CheckResult("seal_exists", True))
        try:
            seal = json.loads(seal_path.read_text())
            checks.append(CheckResult("seal_parseable", True))
            if "spec_hash" in seal:
                checks.append(CheckResult("seal_has_spec_hash", True))
            else:
                checks.append(CheckResult("seal_has_spec_hash", False, "missing spec_hash"))
        except Exception as exc:  # noqa: BLE001  # pragma: no cover  # safety net: seal is optional
            checks.append(CheckResult("seal_parseable", False, str(exc)))

    return CheckReport(child_root=str(child_root), checks=tuple(checks))


def verify_child_full(child_root: str | Path) -> CheckReport:
    """Verify live source custody and provenance schema."""
    child_root = Path(child_root)
    base = verify_child(child_root)
    all_checks = list(base.checks)

    # Schema version check
    if base.all_passed:
        try:
            prov = json.loads(confined_path(child_root, "provenance.json", regular=True).read_text())
            schema = prov.get("schema_version", "")
            from .materialize import PROVENANCE_SCHEMA_VERSION

            if schema == PROVENANCE_SCHEMA_VERSION:
                all_checks.append(CheckResult("schema_version_correct", True))
            else:
                all_checks.append(
                    CheckResult(
                        "schema_version_correct",
                        False,
                        f"expected {PROVENANCE_SCHEMA_VERSION}, got {schema}",
                    )
                )
        except Exception:  # noqa: BLE001  # safety net: schema probe when provenance is corrupt
            pass

    return CheckReport(child_root=str(child_root), checks=tuple(all_checks))
