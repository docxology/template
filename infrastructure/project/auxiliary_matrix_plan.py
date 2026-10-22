"""Versioned complete project-scoped auxiliary execution partition.

Each cell owns one original 1800-second operation. Parallel cells deliberately
change the aggregate scheduling allowance; they never qualify a global run.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

SCHEMA = "template-auxiliary-project-matrix-v1"
TIMEOUT_SECONDS = 1800
KINDS = frozenset({"roster", "docs", "oracle", "platform", "transfer", "pipeline", "domain", "live"})
DARWIN_GATES = frozenset({"root:macos:process", "root:macos:rendering"})
TRANSFER_GATE = "root:sandbox:transfer"


def matrix_plan(requirements: Sequence[Any]) -> dict[str, tuple[str, ...]]:
    """Partition the complete Source profile without accepting a DATA allowlist."""
    scopes = {"root": "root", **{Path(scope).name: scope for scope in PUBLIC_PROJECT_NAMES}}
    if len(scopes) != len(PUBLIC_PROJECT_NAMES) + 1:
        raise ValueError("auxiliary matrix cell names must uniquely identify every public scope")
    auxiliary = [row for row in requirements if row.kind in KINDS]
    ids = [row.id for row in auxiliary]
    if len(ids) != len(set(ids)) or not DARWIN_GATES.union({TRANSFER_GATE}).issubset(ids):
        raise ValueError("auxiliary profile has duplicate or absent mandatory host/transfer gates")
    excluded = DARWIN_GATES | {TRANSFER_GATE}
    result = {
        cell: tuple(row.id for row in auxiliary if row.scope == scope and row.id not in excluded)
        for cell, scope in scopes.items()
    }
    flattened = [gate for gates in result.values() for gate in gates]
    if (
        any(not gates for gates in result.values())
        or len(flattened) != len(set(flattened))
        or set(flattened) != set(ids) - excluded
    ):
        raise ValueError("auxiliary matrix must cover every Linux gate exactly once")
    return result


def selection(requirements: Sequence[Any], cell: str) -> dict[str, Any]:
    """Declare the immutable cell selection and its single operation clock."""
    plan = matrix_plan(requirements)
    if cell not in plan:
        raise ValueError("unknown Source-owned auxiliary matrix cell")
    return {
        "schema_version": SCHEMA,
        "cell": cell,
        "gates": list(plan[cell]),
        "timeout_seconds": TIMEOUT_SECONDS,
        "workers": 1,
    }


def validate_cell(report: dict[str, Any], requirements: Sequence[Any], cell: str) -> None:
    """Require the full original cell, never a successful subset of its gates."""
    declared = report.get("auxiliary_selection")
    if (
        not isinstance(declared, dict)
        or type(declared.get("timeout_seconds")) is not int
        or type(declared.get("workers")) is not int
    ):
        raise ValueError("auxiliary matrix operation clock and worker count require exact integers")
    if declared != selection(requirements, cell) or set(report.get("gates", {})) != set(
        matrix_plan(requirements)[cell]
    ):
        raise ValueError("auxiliary original changed its complete Source-owned matrix selection")
    if type(report.get("auxiliary_workers")) is not int or report["auxiliary_workers"] != 1:
        raise ValueError("one project-scoped auxiliary operation must run serially")


def receipt_path(cell: str) -> str:
    """Fixed transport location; caller must first admit the Source cell name."""
    if cell not in {"root", *(Path(scope).name for scope in PUBLIC_PROJECT_NAMES)}:
        raise ValueError("unknown Source-owned auxiliary matrix cell")
    return f"output/readiness/auxiliary-linux/{cell}/receipt.json"
