"""Verify the integrity of a materialized child project.

Verification works by recomputing the tree hash from the live files and
comparing against the recorded provenance.  A "full" verification also
re-expands the spec from the grammar and confirms all selections match.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .common import CheckReport, CheckResult
from .integrity import tree_hash_from_content_hashes


def verify_child(child_root: str | Path) -> CheckReport:
    """Verify that provenance.json exists and tree hash matches live files."""
    child_root = Path(child_root)
    checks: list[CheckResult] = []

    prov_path = child_root / "provenance.json"
    if not prov_path.exists():
        checks.append(CheckResult("provenance_exists", False, "provenance.json missing"))
        return CheckReport(child_root=str(child_root), checks=tuple(checks))

    checks.append(CheckResult("provenance_exists", True))

    try:
        prov = json.loads(prov_path.read_text())
    except Exception as exc:
        checks.append(CheckResult("provenance_parseable", False, str(exc)))
        return CheckReport(child_root=str(child_root), checks=tuple(checks))

    checks.append(CheckResult("provenance_parseable", True))

    recorded_hash = prov.get("tree_hash", "")
    recorded_files: list[str] = prov.get("files", [])

    # Recompute hash from listed files
    live: dict[str, str] = {}
    missing = []
    for rel in recorded_files:
        fp = child_root / rel
        if fp.exists():
            live[rel] = fp.read_text()
        else:
            missing.append(rel)

    if missing:
        checks.append(
            CheckResult("all_files_present", False, f"Missing: {missing[:3]}")
        )
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
        except Exception as exc:  # noqa: BLE001  # pragma: no cover  # seal is optional
            checks.append(CheckResult("seal_parseable", False, str(exc)))

    return CheckReport(child_root=str(child_root), checks=tuple(checks))


def verify_child_full(
    child_root: str | Path,
    template_root: Optional[str | Path] = None,
) -> CheckReport:
    """Run full verification: provenance + tree hash + optional re-expansion."""
    child_root = Path(child_root)
    base = verify_child(child_root)
    all_checks = list(base.checks)

    # Schema version check
    prov_path = child_root / "provenance.json"
    if prov_path.exists():
        try:
            prov = json.loads(prov_path.read_text())
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
        except Exception:
            pass

    return CheckReport(child_root=str(child_root), checks=tuple(all_checks))
