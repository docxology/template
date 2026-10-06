"""Bounded canonical Root collection and independent readback; never runtime acceptance."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.implementation_custody import capture_implementation_custody, verify_implementation_custody
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.project.public_acceptance_case_observer import RootCaseObserver
from infrastructure.project.public_acceptance_evidence import (
    cell_environment,
    evidence_directory,
    runtime_identity,
    verify_runtime_execution,
    write_json,
)
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_root_case_contract import (
    COORDINATOR_SCHEMA,
    SPEC_SCHEMA,
    RECEIPT_SCHEMA,
    PROCESS_SCHEMA,
    _spec,
    _fresh_prefix,
    _root_identity,
    _runtime_locations,
    _pytest_arguments,
    _json,
    census_command,
    coordinator_command,
    root_python_hashes,
)
from infrastructure.project.public_root_case_readback import _read_collection
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _worker(root: Path, spec_path: Path, expected_hash: str) -> int:
    reader = SnapshotReader(root)
    snapshot = reader.read(spec_path.absolute().relative_to(root).as_posix())
    if snapshot.sha256 != expected_hash:
        raise ValueError("census specification bytes changed after actual child admission")
    spec = _spec(reader, snapshot)
    directory = root / spec["directory"]
    receipt = directory / "census.json"
    if receipt.exists() or receipt.is_symlink():
        raise ValueError("Root census receipt must be fresh")

    class CensusObserver(RootCaseObserver):
        interrupted = False

        def pytest_keyboard_interrupt(self, excinfo: pytest.ExceptionInfo[BaseException]) -> None:
            self.interrupted = True

    observer = CensusObserver(reader, spec["source_hashes"])
    arguments = _pytest_arguments(root, directory, spec["test_files"])
    original: int | None = None
    diagnostic = ""
    census: dict[str, Any] | None = None
    try:
        os.chdir(root)
        original = int(pytest.main(arguments, plugins=[observer]))
        if original != 0:
            raise ValueError("original pytest collection did not succeed")
        census = observer.census(
            source_identity=spec["source_identity"],
            runtime=spec["runtime"]["python_version"],
            platform=sys.platform,
        )
        if any(not row["public_closure"] for row in census["families"]):
            raise ValueError("Root collection imported a nonpublic or unresolved case/fixture provider")
        verify_runtime_execution(root, root=root, scope="root")
        verify_implementation_custody(spec["implementation"], fresh_pycache_prefix=_fresh_prefix())
        if (
            RuntimeScope(root, "root").source_identity() != spec["source_identity"]
            or runtime_identity() != spec["runtime"]
        ):
            raise ValueError("source or selected runtime changed during canonical collection")
        if not reader.unchanged() or _root_identity(root) != spec["root_identity"]:
            raise ValueError("consumed collection source or Root identity changed during canonical collection")
    except (OSError, ValueError) as error:
        # Keep raw private details local in pytest output; public summaries stay generic.
        diagnostic = type(error).__name__ + ": canonical Root collection refused"
        census = None
    code = 130 if observer.interrupted else 0 if census is not None else 1
    write_json(
        root,
        receipt,
        {
            "schema_version": RECEIPT_SCHEMA,
            "role": "canonical-collection-only",
            "run_id": spec["run_id"],
            "nonce": spec["nonce"],
            "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
            "original_pytest_exit_code": original,
            "exit_code": code,
            "arguments": arguments,
            "source_identity": spec["source_identity"],
            "runtime": spec["runtime"],
            "runtime_locations": spec["runtime_locations"],
            "census": census,
            "cases": observer.cases,
            "nodeids": observer.nodeids,
            "collection_errors": observer.collection_errors,
            "collection_skips": observer.collection_skips,
            "deselected": observer.deselected,
            "executed_reports": observer.executed_reports,
            "interrupted": observer.interrupted,
            "bytecode_verified": census is not None,
            "diagnostic": diagnostic,
        },
    )
    return code


def _coordinate(root: Path, directory: Path, timeout_seconds: int, run_id: str, nonce: str) -> dict[str, Any]:
    """Admission and readback run inside the outer native-process guardian."""
    started = time.monotonic()
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600:
        raise ValueError("canonical collection needs a finite positive timeout at most 3600 seconds")
    root = root.resolve(strict=True)
    directory = evidence_directory(root, directory, fresh=True)
    reader = SnapshotReader(root)
    resolved = RuntimeScope(root, "root")
    source = resolved.source_identity()
    spec = {
        "schema_version": SPEC_SCHEMA,
        "root": str(root),
        "directory": directory.relative_to(root).as_posix(),
        "run_id": run_id,
        "nonce": nonce,
        "test_files": list(resolved.test_files()),
        "source_identity": source,
        "source_hashes": root_python_hashes(root, reader),
        "runtime": runtime_identity(),
        "runtime_locations": _runtime_locations(),
        "timeout_seconds": timeout_seconds,
        "implementation": capture_implementation_custody(fresh_pycache_prefix=_fresh_prefix()),
        "root_identity": _root_identity(root),
    }
    if not reader.unchanged() or resolved.source_identity() != source or _root_identity(root) != spec["root_identity"]:
        raise ValueError("Root source changed before canonical census launch")
    binding = write_json(root, directory / "census-spec.json", spec)
    remaining = math.floor(timeout_seconds - (time.monotonic() - started))
    if remaining < 1:
        raise TimeoutError("Root census deadline exhausted before child launch")
    command = census_command(root, directory, binding)
    observed = run_with_policy(
        command,
        cwd=root,
        env=cell_environment(Path(sys.executable), directory, repo_root=root),
        policy=SubprocessPolicy(
            policy_id="root-canonical-census-v2", source_path=__name__, timeout_seconds=remaining, credential_free=True
        ),
    )
    receipt_reader = SnapshotReader(root)
    receipt_path = directory / "census.json"
    receipt_binding = None
    if receipt_path.is_file() and not receipt_path.is_symlink():
        held = receipt_reader.read(receipt_path.relative_to(root).as_posix())
        receipt_binding = {"path": held.relative, "sha256": held.sha256}
    process_binding = write_json(
        root,
        directory / "census-process.json",
        {
            "schema_version": PROCESS_SCHEMA,
            "run_id": spec["run_id"],
            "nonce": spec["nonce"],
            "spec_artifact": binding,
            "receipt_artifact": receipt_binding,
            "command": list(command),
            "returncode": observed.returncode,
            "original_returncode": observed.original_returncode,
            "timed_out": observed.timed_out,
            "custody_refused": observed.custody_refused,
            "command_error": observed.command_error,
            "duration_seconds": time.monotonic() - started,
        },
    )
    if observed.returncode in (-2, 130):
        code = 130
    elif observed.timed_out or time.monotonic() - started >= timeout_seconds:
        code = 124
    else:
        code = 0 if observed.returncode == 0 and receipt_binding is not None else 1
    if code == 0:
        _read_collection(reader, binding, process_binding, receipt_binding)
    return {
        "role": "canonical-collection-only",
        "exit_code": code,
        "spec_artifact": binding,
        "process_artifact": process_binding,
        "receipt_artifact": receipt_binding,
    }


def produce_root_census(root: Path, directory: Path, *, timeout_seconds: int = 660) -> dict[str, Any]:
    """Guard the actual coordinator, including admission, child and readback.

    Matrix callers run this API in each locked selected environment. It never
    installs or switches runtimes. Independent later reading remains separately
    supervised by its enclosing readiness or program worker.
    """
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600:
        raise ValueError("canonical collection needs a finite positive timeout at most 3600 seconds")
    root = root.resolve(strict=True)
    directory = evidence_directory(root, directory, fresh=True)
    run_id, nonce = uuid.uuid4().hex, uuid.uuid4().hex
    started = time.monotonic()
    command = coordinator_command(root, directory, timeout_seconds, run_id, nonce)
    environment = cell_environment(Path(sys.executable), directory, repo_root=root)
    admission_duration = time.monotonic() - started
    remaining = math.floor(timeout_seconds - admission_duration)
    if remaining < 1:
        raise TimeoutError("Root census deadline exhausted before coordinator launch")
    observed = run_with_policy(
        command,
        cwd=root,
        env=environment,
        policy=SubprocessPolicy(
            policy_id="root-census-coordinator-v2",
            source_path=__name__,
            timeout_seconds=remaining,
            credential_free=True,
        ),
    )
    reader = SnapshotReader(root)
    bundle_binding = None
    bundle: dict[str, Any] = {}
    try:
        held = reader.read((directory / "coordinator-bundle.json").relative_to(root).as_posix())
        bundle_binding = {"path": held.relative, "sha256": held.sha256}
        bundle = _json(held)
    except (OSError, ValueError):
        pass
    outer_binding = write_json(
        root,
        directory / "coordinator-process.json",
        {
            "schema_version": COORDINATOR_SCHEMA,
            "run_id": run_id,
            "nonce": nonce,
            "command": list(command),
            "bundle_artifact": bundle_binding,
            "returncode": observed.returncode,
            "original_returncode": observed.original_returncode,
            "timed_out": observed.timed_out,
            "custody_refused": observed.custody_refused,
            "command_error": observed.command_error,
            "admission_duration_seconds": admission_duration,
            "launch_budget_seconds": remaining,
            "duration_seconds": time.monotonic() - started,
        },
    )
    exhausted = time.monotonic() - started >= timeout_seconds
    code = (
        130
        if observed.returncode in (-2, 130)
        else 124
        if observed.timed_out or observed.returncode == 124 or exhausted
        else 1
    )
    if (
        observed.returncode == 0
        and type(bundle.get("exit_code")) is int
        and bundle["exit_code"] == 0
        and bundle.get("role") == "canonical-collection-only"
        and not exhausted
        and not observed.timed_out
        and not observed.custody_refused
        and not observed.command_error
    ):
        code = 0
    return {**bundle, "role": "canonical-collection-only", "exit_code": code, "coordinator_artifact": outer_binding}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--worker-spec", type=Path)
    parser.add_argument("--spec-sha256")
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=660)
    parser.add_argument("--coordinator-run")
    parser.add_argument("--coordinator-nonce")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
    except OSError:
        parser.error("Root path must exist")
    if not root.is_dir():
        parser.error("Root path must be a directory")
    if args.worker_spec is not None:
        if (
            args.directory is not None
            or args.coordinator_run is not None
            or args.coordinator_nonce is not None
            or args.spec_sha256 is None
            or re.fullmatch(r"[0-9a-f]{64}", args.spec_sha256) is None
        ):
            parser.error("worker mode requires only its original spec/hash")
        return _worker(root, args.worker_spec, args.spec_sha256)
    if args.directory is None or args.spec_sha256 is not None:
        parser.error("producer mode requires a fresh ignored directory")
    if not 1 <= args.timeout_seconds <= 3600 or not RuntimeScope(root, "root").test_files():
        parser.error("producer needs a finite timeout and nonempty canonical Root test files")
    try:
        evidence_directory(root, args.directory, fresh=True)
    except ValueError as error:
        parser.error(str(error))
    try:
        if args.coordinator_run is not None or args.coordinator_nonce is not None:
            if any(
                not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{32}", value) is None
                for value in (args.coordinator_run, args.coordinator_nonce)
            ):
                parser.error("coordinator mode requires original run and nonce identities")
            result = _coordinate(
                root, args.directory, args.timeout_seconds, args.coordinator_run, args.coordinator_nonce
            )
            write_json(root, args.directory / "coordinator-bundle.json", result)
        else:
            result = produce_root_census(root, args.directory, timeout_seconds=args.timeout_seconds)
    except KeyboardInterrupt:
        return 130
    except TimeoutError:
        return 124
    except (OSError, ValueError):
        return 1
    print(json.dumps(result, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
