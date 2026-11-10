"""Supervised aggregate reporting from exact typed multi-project results."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.files.secure_write import atomic_write_text_confined, read_bytes_confined
from infrastructure.core.implementation_custody import (
    bytecode_audit_bootstrap,
    capture_implementation_custody,
    verify_implementation_custody,
)
from infrastructure.core.pipeline.multi_project import MultiProjectResult
from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.core.pipeline.worker_transport import stage_results_to_payload
from infrastructure.project.project_info import ProjectInfo

SCHEMA = "template-multi-project-summary/1"
_ALLOWED = {"multi_project_summary.json", "multi_project_summary.md", "last-run-summary.md"}


def _summary_bootstrap(implementation: Path) -> str:
    return (
        "import runpy,sys\nsys.pycache_prefix=sys.argv.pop(1)\nsys.dont_write_bytecode=False\n"
        + bytecode_audit_bootstrap((implementation / "infrastructure", implementation / "scripts"), None)
        + "sys.path.insert(0,sys.argv.pop(1))\n"
        "runpy.run_module('infrastructure.core.pipeline.multi_project_summary_worker',run_name='__main__')\n"
    )


def _run_claim(run: RunResult) -> dict:
    return {
        "expected_stage_keys": run.expected_stage_keys,
        "outcomes": [outcome.to_dict() for outcome in run.outcomes],
    }


def _stable(result: MultiProjectResult) -> dict:
    """Keep the aggregate request stable across in-memory result changes."""
    shared = result.shared_infrastructure_result
    return {
        "project_results": {
            name: stage_results_to_payload(rows) for name, rows in result.project_results.items()
        },
        "infra_test_duration": result.infra_test_duration,
        "total_duration": result.total_duration,
        "successful_projects": result.successful_projects,
        "failed_projects": result.failed_projects,
        "expected_projects": result.expected_projects,
        "run_results": {name: _run_claim(run) for name, run in result.run_results.items()},
        "shared_infrastructure_exit_code": result.shared_infrastructure_exit_code,
        "shared_infrastructure_result": (
            {
                "stage_results": stage_results_to_payload(shared.stage_results),
                "run_result": _run_claim(shared.run_result),
            }
            if shared is not None
            else None
        ),
    }


def write_summary_reports(
    result: MultiProjectResult, projects: list[ProjectInfo], root: Path, *, deadline: float
) -> int:
    """Bound generation and publish only exact confined scratch artifact bytes.

    Reporting errors remain executed-run failures. Expiration cannot grant a
    passing aggregate even when the project stages already completed.
    """
    if time.monotonic() >= deadline:
        return 124
    with tempfile.TemporaryDirectory(prefix="template-multi-summary-") as temporary:
        scratch = Path(temporary).resolve(strict=True)
        custody = capture_implementation_custody()
        payload = {
            "schema_version": SCHEMA,
            "nonce": uuid.uuid4().hex,
            "custody": custody,
            "result": _stable(result),
            "projects": [asdict(project) for project in projects],
        }
        content = json.dumps(payload, sort_keys=True, default=str, allow_nan=False).encode()
        request = scratch / "request.json"
        request.write_bytes(content)
        request.chmod(0o400)
        digest = hashlib.sha256(content).hexdigest()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return 124
        implementation = Path(__file__).resolve().parents[3]
        command = [
            sys.executable,
            "-I",
            "-c",
            _summary_bootstrap(implementation),
            str(scratch / "bytecode"),
            str(implementation),
            "--request",
            str(request),
            "--sha256",
            digest,
        ]
        child = run_bounded_subprocess(command, cwd=root, env=build_bounded_env(), timeout=remaining)
        if child.timed_out or time.monotonic() >= deadline:
            return 124
        if child.custody_refused:
            return 75
        if child.returncode:
            return 1
        receipt = json.loads(read_bytes_confined(scratch, scratch / "receipt.json"))
        if (
            not isinstance(receipt, dict)
            or set(receipt) != {"schema_version", "nonce", "request_sha256", "artifacts"}
            or receipt["schema_version"] != SCHEMA
            or receipt["nonce"] != payload["nonce"]
            or receipt["request_sha256"] != digest
            or not isinstance(receipt["artifacts"], dict)
            or set(receipt["artifacts"]) != _ALLOWED
        ):
            raise ValueError("Aggregate summary differs from its bound typed input")
        artifacts = {name: read_bytes_confined(scratch, scratch / "reports" / name) for name in _ALLOWED}
        if any(hashlib.sha256(raw).hexdigest() != receipt["artifacts"][name] for name, raw in artifacts.items()):
            raise ValueError("Aggregate summary artifact changed after generation")
        verify_implementation_custody(custody)
        if time.monotonic() >= deadline:
            return 124
        for name, raw in artifacts.items():
            if time.monotonic() >= deadline:
                return 124
            target = root / "output/multi_project_summary" / name
            atomic_write_text_confined(root, target, raw.decode("utf-8"))
        verify_implementation_custody(custody)
        return 124 if time.monotonic() >= deadline else 0
