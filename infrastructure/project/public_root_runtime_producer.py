"""Supervised prepared-interpreter Root v2 execution and genuine selected-interpreter readback."""

from __future__ import annotations

import json
import math
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import build_bounded_env
from infrastructure.core.execution_policy import apply_execution_policy
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.project.public_acceptance_evidence import cell_environment, evidence_directory
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_root_case_admission import load_policy
from infrastructure.project.public_root_case_contract import _artifact, _json, _root_identity
from infrastructure.project.public_root_case_units import declared_units
from infrastructure.project.public_root_lane_contract import write
from infrastructure.project.public_root_runtime_contract import (
    BUNDLE_ROLE,
    PROCESS_SCHEMA,
    SPEC_SCHEMA,
    reader_command,
    runtime_projection,
    worker_command,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def produce_runtime_cohort(
    root: Path,
    directory: Path,
    *,
    interpreter: Path,
    runtime_probe: object,
    mode: str = "core",
    timeout_seconds: int = 7200,
    census_timeout_seconds: int = 660,
    test_timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Include selected worker admission, census, units, readback and reporting in one guardian.

    The enclosing program supervises this public API if caller-side filesystem
    admission itself needs a hard deadline. No runtime/tool acquisition occurs.
    """
    started = time.monotonic()
    if (
        mode not in {"core", "live"}
        or any(
            type(value) is not int or not 1 <= value <= 14400
            for value in (timeout_seconds, census_timeout_seconds, test_timeout_seconds)
        )
        or not census_timeout_seconds < timeout_seconds
        or census_timeout_seconds > 3600
    ):
        raise ValueError("Root runtime cohort requires finite coherent whole/census/case budgets and explicit mode")
    root = root.resolve(strict=True)
    directory = evidence_directory(root, directory, fresh=True)
    identity = _root_identity(root)
    runtime = runtime_projection(runtime_probe)
    if str(interpreter.absolute()) != runtime["executable"]:
        raise ValueError("Root cohort interpreter differs from its actual selected runtime probe")
    reader = SnapshotReader(root)
    policy, policy_binding, prerequisites_binding, prerequisites = load_policy(reader)
    scope = RuntimeScope(root, "root")
    binding = write(
        root,
        directory / "runtime-spec.json",
        {
            "schema_version": SPEC_SCHEMA,
            "root": str(root),
            "root_identity": identity,
            "directory": directory.relative_to(root).as_posix(),
            "run_id": uuid.uuid4().hex,
            "nonce": uuid.uuid4().hex,
            "runtime": runtime,
            "source_identity": scope.source_identity(),
            "deliverables_identity": scope.deliverables_identity(),
            "mode": mode,
            "timeout_seconds": timeout_seconds,
            "census_timeout_seconds": census_timeout_seconds,
            "test_timeout_seconds": test_timeout_seconds,
            "policy_artifact": policy_binding,
            "prerequisites_artifact": prerequisites_binding,
        },
        identity,
    )
    snapshot = _artifact(reader, binding)
    spec = _json(snapshot)
    command = worker_command(interpreter.absolute(), root, snapshot)
    env = build_bounded_env(cell_environment(interpreter.absolute(), directory, repo_root=root))
    env = apply_execution_policy(env, root, mode=mode)
    if mode == "live":
        admitted_ids = {
            obligation
            for unit in declared_units(policy, prerequisites)
            if sys.platform in unit.platforms
            for obligation in unit.obligations
        }
        for prerequisite in prerequisites:
            if prerequisite.id in admitted_ids:
                for key in prerequisite.environment_keys:
                    if key in os.environ:
                        env[key] = os.environ[key]
    if not reader.unchanged() or _root_identity(root) != identity:
        raise ValueError("Root runtime admission source or original physical directory changed")
    admission_duration = time.monotonic() - started
    limit = math.floor(timeout_seconds - admission_duration)
    if limit < 1:
        raise TimeoutError("Root runtime whole deadline exhausted before selected worker launch")
    observed = run_with_policy(
        command,
        cwd=root,
        env=env,
        policy=SubprocessPolicy(
            policy_id="root-v2-runtime-cohort",
            source_path=__name__,
            timeout_seconds=limit,
            credential_free=mode == "core",
        ),
    )
    elapsed = time.monotonic() - started
    result_binding = None
    result: dict[str, Any] = {}
    try:
        held = SnapshotReader(root).read((directory / "runtime-cell.json").relative_to(root).as_posix())
        result_binding = {"path": held.relative, "sha256": held.sha256}
        result = _json(held)
    except (OSError, ValueError):
        pass
    native_binding = write(
        root,
        directory / "runtime-process.json",
        {
            "schema_version": PROCESS_SCHEMA,
            "run_id": spec["run_id"],
            "nonce": spec["nonce"],
            "spec_artifact": binding,
            "result_artifact": result_binding,
            "command": list(command),
            "returncode": observed.returncode,
            "original_returncode": observed.original_returncode,
            "timed_out": observed.timed_out,
            "custody_refused": observed.custody_refused,
            "command_error": observed.command_error,
            "admission_duration_seconds": admission_duration,
            "launch_budget_seconds": limit,
            "duration_seconds": elapsed,
        },
        identity,
    )
    code = (
        130
        if observed.returncode in {-2, 130}
        else 124
        if observed.timed_out or observed.returncode == 124 or elapsed >= timeout_seconds
        else 1
        if observed.custody_refused or observed.command_error
        else observed.returncode
        if observed.returncode in {0, 2, 75}
        else 1
    )
    if code == 0 and (
        type(result.get("exit_code")) is not int or result["exit_code"] != 0 or result.get("role") != BUNDLE_ROLE
    ):
        code = 1
    if time.monotonic() - started >= timeout_seconds and code != 130:
        code = 124
    bundle = {
        "role": BUNDLE_ROLE,
        "exit_code": code,
        "spec_artifact": binding,
        "result_artifact": result_binding,
        "process_artifact": native_binding,
    }
    bundle_binding = write(root, directory / "runtime-bundle.json", bundle, identity)
    return {"bundle": bundle, "bundle_artifact": bundle_binding}


def read_selected_runtime(reader: SnapshotReader, binding: object, *, timeout_seconds: int = 660) -> dict[str, Any]:
    """Run independent original-cohort readback in its exact prepared interpreter.

    Only the bytecode-audited source-owned reader executes; it cannot launch cases,
    live providers or install dependencies. Current Root source/physical identity
    must still agree before and after the selected-reader boundary.
    """
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600:
        raise ValueError("Root selected runtime readback requires a finite bounded deadline")
    started = time.monotonic()
    root = reader.root
    identity = _root_identity(root)
    source = RuntimeScope(root, "root").source_identity()
    snapshot = _artifact(reader, binding)
    bundle = _json(snapshot)
    spec_snapshot = _artifact(reader, bundle.get("spec_artifact"))
    spec = _json(spec_snapshot)
    runtime = runtime_projection(spec.get("runtime"))
    directory = evidence_directory(root, root / spec["directory"])
    if snapshot.path != directory / "runtime-bundle.json" or spec_snapshot.path != directory / "runtime-spec.json":
        raise ValueError("Root original bundle or spec is outside its exact runtime cohort")
    interpreter = Path(runtime["executable"])
    command = reader_command(interpreter, root, snapshot)
    limit = math.floor(timeout_seconds - (time.monotonic() - started))
    if limit < 1:
        raise TimeoutError("Root selected reader admission exhausted its whole deadline")
    observed = run_with_policy(
        command,
        cwd=root,
        env=cell_environment(interpreter, directory / "reader", repo_root=root),
        policy=SubprocessPolicy(
            policy_id="root-v2-selected-reader", source_path=__name__, timeout_seconds=limit, credential_free=True
        ),
    )
    if observed.returncode in {-2, 130}:
        raise KeyboardInterrupt("Root selected runtime reader interrupted")
    if observed.timed_out or observed.returncode == 124 or time.monotonic() - started >= timeout_seconds:
        raise TimeoutError("Root selected runtime reader deadline exhausted")
    if (
        observed.returncode != 0
        or observed.original_returncode != 0
        or observed.custody_refused
        or observed.command_error
    ):
        raise ValueError("actual source-audited selected runtime reader refused original evidence")
    value = json.loads(observed.stdout)
    if (
        not isinstance(value, dict)
        or value.get("role") != BUNDLE_ROLE
        or type(value.get("exit_code")) is not int
        or value["exit_code"] != 0
        or value.get("runtime") != runtime
        or value.get("source_identity") != source
        or not reader.unchanged()
        or RuntimeScope(root, "root").source_identity() != source
        or _root_identity(root) != identity
    ):
        raise ValueError("Root selected runtime reader source, exact interpreter or physical identity changed")
    return value
