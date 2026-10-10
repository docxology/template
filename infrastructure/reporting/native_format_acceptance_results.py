"""Final source identities and preservation of actual native failure outcomes."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_format_acceptance_contracts import (
    NativeDeadlineExpired,
    native_deadline_guard,
    public_source_digest,
)
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.release_readiness_profile import Requirement, required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _finalize_profile(root: Path, before: str) -> tuple[bool, str, tuple[Requirement, ...]]:
    """Derive final identities only after actual regeneration has settled."""
    current = public_source_digest(root) == before
    fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, SnapshotReader(root), fingerprint)
    if faults:
        raise ValueError("final source-owned readiness metadata is invalid or incomplete")
    return current, fingerprint, requirements


def _executed_failure_exit(codes: list[int]) -> int:
    """Post-execution finalization failures preserve stronger actual outcomes."""
    return 130 if 130 in codes else 124 if 124 in codes else 1


def _executed_failure_result(state: dict[str, Any], error: BaseException) -> dict[str, Any]:
    """Preserve attempts even when every subsequent confined write refuses."""
    codes = [item["observation"]["exit_code"] for item in state["admitted"]]
    if isinstance(error, KeyboardInterrupt):
        codes.append(130)
    if isinstance(error, (TimeoutError, NativeDeadlineExpired)) or time.monotonic() >= state["deadline"]:
        codes.append(124)
    summary = {
        "run_id": state["run_id"],
        "source_digest": state["before"],
        "source_current": False,
        "complete_selection": state["selected"] == PUBLIC_PROJECT_NAMES,
        "selected_projects": list(state["selected"]),
        "observed_projects": len(state["admitted"]),
        "diagnostic": str(error),
        "results": [
            {
                "project": item["scope"],
                "status": "fail",
                "observation": item["observation"],
                "process_artifact": item["process"],
                "native_execution_artifact": item["raw_binding"],
            }
            for item in state["admitted"]
        ],
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "platform_version": state["platform_version"],
        "source_fingerprint": state["fingerprint"],
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": {},
        "native_formats": summary,
    }
    binding = None
    try:
        if time.monotonic() < state["deadline"]:
            with native_deadline_guard(state["deadline"]):
                binding = write_json(state["root"], state["directory"] / "receipt.json", payload)
    except NativeDeadlineExpired as persistence_error:
        summary["persistence_diagnostic"] = str(persistence_error)
        codes.append(124)
    except Exception as persistence_error:  # noqa: BLE001 - original outcomes survive failed evidence persistence
        summary["persistence_diagnostic"] = str(persistence_error)
    if time.monotonic() >= state["deadline"]:
        codes.append(124)
    return {
        "receipt": binding,
        "native_formats": summary,
        "exit_code": _executed_failure_exit(codes),
    }
