"""Surface original job failures early; this summary never grants acceptance."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.release_readiness_profile import Requirement, required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

AUXILIARY_KINDS = frozenset({"roster", "docs", "oracle", "platform", "transfer", "pipeline", "domain", "live"})
OTHER_AUXILIARY_OWNERS = frozenset({"root:macos:process", "root:macos:rendering", "root:sandbox:transfer"})


def evaluate_original_outcome(
    kind: str, report: dict[str, Any], requirements: Sequence[Requirement], *, fingerprint: str
) -> dict[str, Any]:
    """Check DATA completeness/status for job control, not runtime provenance."""
    kinds = {"installed", "export"} if kind == "installed" else AUXILIARY_KINDS if kind == "auxiliary" else set()
    if not kinds:
        raise ValueError("original outcome requires the installed or Linux auxiliary owner")
    expected = {item.id for item in requirements if item.kind in kinds}
    gates = report.get("gates")
    if (
        not expected
        or report.get("schema_version") != SCHEMA_VERSION
        or report.get("source_fingerprint") != fingerprint
        or report.get("roster") != list(PUBLIC_PROJECT_NAMES)
        or not isinstance(gates, dict)
        or set(gates) != expected
    ):
        raise ValueError("original job report is absent, stale or incomplete")
    owned = expected if kind == "installed" else expected - OTHER_AUXILIARY_OWNERS
    if not owned:
        raise ValueError("original job has no declared owned obligations")
    if any(
        not isinstance(gates[key], dict) or gates[key].get("status") not in {"pass", "fail", "blocked"}
        for key in expected
    ):
        raise ValueError("original job contains an invalid gate outcome")
    if kind == "installed":
        matrix = report.get("installed_matrix")
        if not isinstance(matrix, dict):
            raise ValueError("installed original job omitted its runtime matrix")
        cells = matrix.get("results")
        expected_cells = {
            (scope, minor) for scope in ("root", *PUBLIC_PROJECT_NAMES) for minor in CANONICAL_CI_PYTHON_VERSIONS
        }
        if not isinstance(cells, list) or len(cells) != len(expected_cells):
            raise ValueError("installed original job omitted runtime observations")
        actual = [(cell.get("scope"), cell.get("python_version")) for cell in cells if isinstance(cell, dict)]
        if (
            set(actual) != expected_cells
            or len(set(actual)) != len(actual)
            or matrix.get("matrix_complete") is not True
            or matrix.get("source_current") is not True
        ):
            raise ValueError("installed original job repeated or narrowed its actual runtime selection")
        cell_failures = sum(cell.get("status") != "pass" for cell in cells)
    else:
        cell_failures = 0
    failures = sorted(key for key in owned if gates[key]["status"] != "pass")
    return {
        "schema_version": "template-original-job-outcome-v1",
        "kind": kind,
        "exit_code": 1 if failures or cell_failures else 0,
        "unpassed_gates": failures,
        "unpassed_cells": cell_failures,
        "owned_gate_count": len(owned),
        "release_acceptance_granted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--kind", choices=("installed", "auxiliary"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.repo_root.resolve(strict=True)
    reader = SnapshotReader(root)
    fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, reader, fingerprint)
    if faults:
        raise ValueError("original outcome requires a complete current Source profile")
    report = reader.read(args.receipt.absolute().relative_to(root).as_posix()).json_object()
    outcome = evaluate_original_outcome(args.kind, report, requirements, fingerprint=fingerprint)
    if source_fingerprint(root) != fingerprint or not reader.unchanged():
        raise ValueError("original job report changed during summary")
    print(json.dumps(outcome, sort_keys=True))
    return int(outcome["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
