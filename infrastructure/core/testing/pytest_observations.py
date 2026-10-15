"""Stdlib-only reading of opt-in actual pytest performance observations.

Observations are functional/benchmark DATA, never release or Source authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DIRECTORY_ENV = "TEMPLATE_PYTEST_RECEIPT_DIRECTORY"
NONCE_ENV = "TEMPLATE_PYTEST_RECEIPT_NONCE"
ROOT_ENV = "TEMPLATE_PYTEST_RECEIPT_ROOT"


def read_execution_receipts(directory: Path, nonce: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Require non-vacuous exact selected/report membership from real controllers."""
    selected: list[str] = []
    outcomes: list[str] = []
    controllers = 0
    calls_passed = 0
    for path in sorted(directory.glob("execution-*.json")):
        value = json.loads(path.read_bytes())
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


__all__ = ["DIRECTORY_ENV", "NONCE_ENV", "ROOT_ENV", "read_execution_receipts", "member_digest"]
