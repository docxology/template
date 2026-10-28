"""Whole-budget Root v2 lane API; only original supervised outcomes can pass."""

from __future__ import annotations

import argparse
import math
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import BoundedSubprocessResult
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.project.public_acceptance_evidence import (
    bootstrap_command,
    cell_environment,
    evidence_directory,
)
from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy
from infrastructure.project.public_root_case_contract import _artifact, _json, _root_identity
from infrastructure.project.public_root_lane_contract import (
    LAUNCH_SCHEMA,
    COORDINATOR_SCHEMA,
    COORDINATOR_PROCESS_SCHEMA,
    admission,
    environment,
    lane_command,
    prepared_model_environment,
    write,
)
from infrastructure.project.public_root_lane_readback import _read_lane_result
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def coordinator_command(root: Path, snapshot: ArtifactSnapshot, *, origin: Any = None) -> tuple[str, ...]:
    launch = (
        (lambda module, *args: origin.bootstrap(root, module, *args))
        if origin
        else (lambda module, *args: bootstrap_command(Path(sys.executable), root, module, *args))
    )
    return launch(
        __name__,
        "--root",
        str(root),
        "--spec",
        str(snapshot.path),
        "--spec-sha256",
        snapshot.sha256,
    )


def _code(observed: BoundedSubprocessResult, exhausted: bool = False) -> int:
    if observed.returncode in (-2, 130):
        return 130
    if observed.timed_out or observed.returncode == 124 or exhausted:
        return 124
    if observed.custody_refused or observed.command_error:
        return 1
    return 75 if observed.returncode == 75 else 0 if observed.returncode == 0 else 1


class _AdmissionError(ValueError):
    """Source-owned configuration refused before any actual test worker."""


def _coordinate(root: Path, snapshot_path: Path, expected: str) -> int:
    started = time.monotonic()
    try:
        reader = SnapshotReader(root)
        snapshot = reader.read(snapshot_path.relative_to(root).as_posix())
        if snapshot.sha256 != expected:
            raise ValueError("Root lane specification changed before actual coordinator admission")
        spec, admitted = admission(reader, snapshot)
        directory = root / spec["directory"]
        deadline = started + spec["timeout_seconds"]
        command = lane_command(root, snapshot)
        env = environment(admitted, spec["lane"], root, directory / "coordinator", spec["mode"])
    except MissingRootCasePolicy:
        raise
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise _AdmissionError("Root lane source-owned admission refused") from error
    admitted_duration = time.monotonic() - started
    remaining = math.floor(spec["timeout_seconds"] - admitted_duration)
    if remaining < 1:
        raise TimeoutError("Root lane deadline exhausted before actual worker admission")
    observed = run_with_policy(
        command,
        cwd=root,
        env=env,
        policy=SubprocessPolicy(
            policy_id="root-v2-lane-coordinator",
            source_path=__name__,
            timeout_seconds=remaining,
            credential_free=spec["mode"] == "core",
        ),
    )
    original_duration = time.monotonic() - started
    result_binding = None
    try:
        held = SnapshotReader(root).read((directory / "lane.json").relative_to(root).as_posix())
        result_binding = {"path": held.relative, "sha256": held.sha256}
    except OSError, ValueError:
        pass
    process_binding = write(
        root,
        directory / "lane-process.json",
        {
            "schema_version": COORDINATOR_PROCESS_SCHEMA,
            "run_id": spec["run_id"],
            "nonce": spec["nonce"],
            "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
            "result_artifact": result_binding,
            "command": list(command),
            "returncode": observed.returncode,
            "original_returncode": observed.original_returncode,
            "timed_out": observed.timed_out,
            "custody_refused": observed.custody_refused,
            "command_error": observed.command_error,
            "admission_duration_seconds": admitted_duration,
            "launch_budget_seconds": remaining,
            "duration_seconds": original_duration,
        },
        spec["root_identity"],
    )
    bundle = {
        "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "process_artifact": process_binding,
        "result_artifact": result_binding,
    }
    code = _code(observed, time.monotonic() >= deadline)
    if code == 0:
        try:
            _read_lane_result(reader, bundle)
        except OSError, ValueError, TypeError, KeyError:
            code = 1
    if time.monotonic() >= deadline and code != 130:
        code = 124
    write(
        root,
        directory / "lane-coordinator-bundle.json",
        {"role": "actual-root-lane", "exit_code": code, **bundle},
        spec["root_identity"],
    )
    return code


def produce_root_lane(
    root: Path,
    directory: Path,
    *,
    census_bundle: object,
    lane: str,
    mode: str = "core",
    timeout_seconds: int = 7200,
    test_timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Supervise policy admission, lock, chunks, reports and independent readback.

    This API uses the actual selected interpreter. It never acquires tools or
    providers. Core is the default mode; selecting a live lane still needs an
    explicit live mode and every source-owned prerequisite.
    """
    started = time.monotonic()
    if (
        not isinstance(lane, str)
        or re.fullmatch("[a-z][a-z0-9:-]{0,80}", lane) is None
        or not isinstance(mode, str)
        or mode not in {"core", "live"}
        or any(type(value) is not int or not 1 <= value <= 14400 for value in (timeout_seconds, test_timeout_seconds))
    ):
        raise ValueError("Root lane requires exact declared selection, mode and finite integer deadlines")
    root = root.resolve(strict=True)
    directory = evidence_directory(root, directory, fresh=True)
    run_id, nonce = uuid.uuid4().hex, uuid.uuid4().hex
    identity = _root_identity(root)
    census_binding = write(root, directory / "census-bundle.json", census_bundle, identity)
    binding = write(
        root,
        directory / "lane-spec.json",
        {
            "schema_version": LAUNCH_SCHEMA,
            "root": str(root),
            "root_identity": identity,
            "directory": directory.relative_to(root).as_posix(),
            "run_id": run_id,
            "nonce": nonce,
            "lane": lane,
            "mode": mode,
            "timeout_seconds": timeout_seconds,
            "test_timeout_seconds": test_timeout_seconds,
            "census_bundle_artifact": census_binding,
        },
        identity,
    )
    reader = SnapshotReader(root)
    snapshot = _artifact(reader, binding)
    command = coordinator_command(root, snapshot)
    # Source-owned live admission occurs in the guarded coordinator. Preserve
    # only keys named by that policy; ambient credentials never enter core.
    from infrastructure.project.public_root_case_admission import load_policy
    from infrastructure.core.execution_boundary import build_bounded_env
    from infrastructure.core.execution_policy import apply_execution_policy
    import os

    env = build_bounded_env(cell_environment(Path(sys.executable), directory, repo_root=root))
    env = apply_execution_policy(env, root, mode=mode)
    if mode == "live":
        policy, _, _, prerequisites = load_policy(reader)
        from infrastructure.project.public_root_case_units import declared_units

        unit = next((item for item in declared_units(policy, prerequisites) if item.id == lane), None)
        if unit is None:
            raise ValueError("live Root selection is outside its exact source-required applicability units")
        required = set(unit.obligations)
        for prerequisite in prerequisites:
            if prerequisite.id in required:
                for key in prerequisite.environment_keys:
                    if key in os.environ:
                        env[key] = os.environ[key]
    env = prepared_model_environment(env)
    admission_duration = time.monotonic() - started
    remaining = math.floor(timeout_seconds - admission_duration)
    if remaining < 1:
        raise TimeoutError("Root lane deadline exhausted before outer coordinator launch")
    observed = run_with_policy(
        command,
        cwd=root,
        env=env,
        policy=SubprocessPolicy(
            policy_id="root-v2-lane-outer",
            source_path=__name__,
            timeout_seconds=remaining,
            credential_free=mode == "core",
        ),
    )
    result: dict[str, Any] = {}
    result_binding = None
    try:
        held = SnapshotReader(root).read((directory / "lane-coordinator-bundle.json").relative_to(root).as_posix())
        result_binding = {"path": held.relative, "sha256": held.sha256}
        result = _json(held)
    except OSError, ValueError:
        pass
    elapsed = time.monotonic() - started
    native_binding = write(
        root,
        directory / "lane-coordinator-process.json",
        {
            "schema_version": COORDINATOR_SCHEMA,
            "run_id": run_id,
            "nonce": nonce,
            "command": list(command),
            "bundle_artifact": result_binding,
            "returncode": observed.returncode,
            "original_returncode": observed.original_returncode,
            "timed_out": observed.timed_out,
            "custody_refused": observed.custody_refused,
            "command_error": observed.command_error,
            "admission_duration_seconds": admission_duration,
            "launch_budget_seconds": remaining,
            "duration_seconds": elapsed,
        },
        identity,
    )
    code = _code(observed, elapsed >= timeout_seconds)
    if code == 0 and (
        type(result.get("exit_code")) is not int or result["exit_code"] != 0 or result.get("role") != "actual-root-lane"
    ):
        code = 1
    if (
        observed.returncode == observed.original_returncode == 2
        and not observed.timed_out
        and not observed.custody_refused
        and not observed.command_error
        and elapsed < timeout_seconds
    ):
        code = 2  # The source-owned coordinator refused configuration before case launch.
    if time.monotonic() - started >= timeout_seconds and code != 130:
        code = 124
    return {**result, "role": "actual-root-lane", "exit_code": code, "coordinator_artifact": native_binding}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--spec-sha256", required=True)
    args = parser.parse_args(argv)
    if len(args.spec_sha256) != 64 or any(char not in "0123456789abcdef" for char in args.spec_sha256):
        parser.error("original Root lane specification needs its exact SHA-256")
    try:
        root = args.root.resolve(strict=True)
        return _coordinate(root, args.spec.absolute(), args.spec_sha256)
    except MissingRootCasePolicy:
        return 75
    except KeyboardInterrupt:
        return 130
    except TimeoutError:
        return 124
    except _AdmissionError:
        return 2
    except OSError, ValueError, TypeError, KeyError, RuntimeError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
