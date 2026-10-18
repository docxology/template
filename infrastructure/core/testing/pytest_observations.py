"""Stdlib-only reading of opt-in actual pytest performance observations.

Observations are functional/benchmark DATA, never release or Source authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DIRECTORY_ENV = "TEMPLATE_PYTEST_RECEIPT_DIRECTORY"
NONCE_ENV = "TEMPLATE_PYTEST_RECEIPT_NONCE"
ROOT_ENV = "TEMPLATE_PYTEST_RECEIPT_ROOT"


def read_execution_receipts(
    directory: Path, nonce: str, *, snapshots: tuple[bytes, ...] | None = None
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Require non-vacuous exact selected/report membership from real controllers."""
    selected: list[str] = []
    outcomes: list[str] = []
    controllers = 0
    calls_passed = 0
    originals = (
        snapshots
        if snapshots is not None
        else tuple(path.read_bytes() for path in sorted(directory.glob("execution-*.json")))
    )
    for raw in originals:
        value = json.loads(raw)
        if value.get("schema_version") != "template-pytest-execution/v1" or value.get("nonce") != nonce:
            raise ValueError("pytest observation schema/nonce differs")
        if value["worker"] != "controller":
            continue
        controllers += 1
        members = value["selected"]
        reports = value["reports"]
        if (
            not members
            or len(members) != len(set(members))
            or set(members) != set(reports)
            or value["collection_errors"] != 0
            or value["exit_code"] != 0
        ):
            raise ValueError("pytest execution was empty, incomplete or unsuccessful")
        for nodeid in members:
            if not isinstance(nodeid, str) or nodeid.startswith(("/", "\\")) or "\0" in nodeid:
                raise ValueError("pytest nodeid must remain repository-relative")
            phases = reports[nodeid]
            valid = {"passed", "skipped", "skipped:xfail", "passed:xfail"}
            if (
                phases.get("teardown") != "passed"
                or phases.get("setup") not in valid
                or any(outcome not in valid for outcome in phases.values())
                or (phases.get("setup") == "passed" and phases.get("call") not in valid)
            ):
                raise ValueError("pytest execution contains incomplete or failed phases")
            calls_passed += phases.get("call") in {"passed", "passed:xfail"}
            selected.append(nodeid)
            outcomes.append(nodeid + "|" + json.dumps(phases, sort_keys=True, separators=(",", ":")))
    if not controllers or not calls_passed or len(selected) != len(set(selected)):
        raise ValueError("pytest observations missing or repeat selected members")
    return tuple(sorted(selected)), tuple(sorted(outcomes))


def member_digest(members: tuple[str, ...]) -> str:
    return hashlib.sha256(json.dumps(members, separators=(",", ":")).encode()).hexdigest()


def read_execution_collection(
    directory: Path, nonce: str, *, snapshots: tuple[bytes, ...] | None = None
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, Any]]:
    """Read one serial controller's original prefilter collection and actual exclusions.

    Selected members still need genuine complete outcomes; deselection is an
    explicit collection observation, never successful execution or acceptance.
    """
    originals = (
        snapshots
        if snapshots is not None
        else tuple(path.read_bytes() for path in sorted(directory.glob("execution-*.json")))
    )
    selected, _ = read_execution_receipts(directory, nonce, snapshots=originals)
    controllers = []
    for raw in originals:
        value = json.loads(raw)
        if value.get("schema_version") != "template-pytest-execution/v1" or value.get("nonce") != nonce:
            raise ValueError("pytest observation schema/nonce differs")
        if value.get("worker") == "controller":
            controllers.append(value)
    if len(controllers) != 1:
        raise ValueError("collection accounting requires one original serial controller")
    value = controllers[0]
    profile = value.get("selection_profile")
    if (
        not isinstance(profile, dict)
        or set(profile) != {"arguments", "marker_expression", "keyword_expression", "workers", "ambient_addopts"}
        or not isinstance(profile["arguments"], list)
        or not profile["arguments"]
        or any(not isinstance(item, str) for item in profile["arguments"])
        or any(not isinstance(profile[key], str) for key in ("marker_expression", "keyword_expression"))
        or type(profile["ambient_addopts"]) is not bool
        or profile["workers"] is not None
        and (type(profile["workers"]) is not int or profile["workers"] != 0)
    ):
        raise ValueError("collection accounting requires the original serial selection profile")
    groups = []
    for key in ("collected", "deselected"):
        members = value.get(key)
        if (
            not isinstance(members, list)
            or any(
                not isinstance(node, str)
                or not node
                or node.startswith(("/", "\\"))
                or "\0" in node
                or ".." in Path(node.partition("::")[0]).parts
                for node in members
            )
            or len(members) != len(set(members))
        ):
            raise ValueError("collection accounting contains invalid or duplicate members")
        groups.append(tuple(sorted(members)))
    collected, deselected = groups
    if set(selected) & set(deselected) or set(collected) != set(selected) | set(deselected):
        raise ValueError("original collection differs from selected and explicitly deselected members")
    return collected, deselected, profile


__all__ = [
    "DIRECTORY_ENV",
    "NONCE_ENV",
    "ROOT_ENV",
    "read_execution_receipts",
    "read_execution_collection",
    "member_digest",
]
