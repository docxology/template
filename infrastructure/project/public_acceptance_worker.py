"""One locked, bounded full-selection public project/runtime acceptance cell."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import math
import os
import re
import sys
import time
import tomllib
import uuid
from pathlib import Path
from typing import Any

from coverage import Coverage

from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.testing.project_test_matrix import ProjectTestResult, ProjectTestTask, run_project_test_matrix
from infrastructure.project.public_acceptance_evidence import (
    CELL_SCHEMA,
    aggregate_pytest,
    cell_environment,
    evidence_directory,
    read_json,
    runtime_identity,
    verify_runtime_execution,
    write_json,
)
from infrastructure.project.public_acceptance_cases import PYTEST_SPEC_SCHEMA, project_python_hashes, pytest_command
from infrastructure.project.public_acceptance_dependencies import runtime_provider_roots
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy, RuntimeScope


class _RuntimeChildFailure(RuntimeError):
    """Retain a supervised child's original interruption/deadline outcome."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def test_groups(project: Path, files: list[str]) -> list[list[str]]:
    """Reuse an explicitly declared pure chunk planner; otherwise execute the whole suite."""
    metadata = tomllib.loads((project / "pyproject.toml").read_text())
    contract = metadata.get("tool", {}).get("template", {})
    planner = contract.get("acceptance_test_groups")
    if planner is None:
        if contract.get("project_test_command"):
            raise ValueError("custom verifier needs an explicit full-selection acceptance_test_groups planner")
        return [files]
    if not isinstance(planner, str) or re.fullmatch(r"[a-zA-Z_][\w.]*:[a-zA-Z_]\w*", planner) is None:
        raise ValueError("acceptance_test_groups must be a source-owned module:callable")
    module_name, function_name = planner.split(":")
    module = importlib.import_module(module_name)
    source = Path(module.__file__ or "").resolve()
    if not source.is_relative_to((project / "src").resolve()):
        raise ValueError("acceptance chunk planner must belong to this project's src")
    groups = getattr(module, function_name)(project)
    if not isinstance(groups, list) or not groups:
        raise ValueError("acceptance chunk planner returned no groups")
    selections = []
    for row in groups:
        if (
            not isinstance(row, tuple)
            or len(row) != 2
            or not isinstance(row[0], str)
            or not isinstance(row[1], list)
            or not row[1]
        ):
            raise ValueError("acceptance chunk planner must return labeled nonempty selector lists")
        for selector in row[1]:
            if not isinstance(selector, str) or selector.split("::", 1)[0] not in files:
                raise ValueError("acceptance chunk selector is outside the whole source-owned selection")
        selections.append(row[1])
    return selections


def _run_pytest(
    root: Path,
    project: Path,
    directory: Path,
    run_id: str,
    index: int,
    selectors: list[str],
    *,
    collect: bool,
    deadline: float,
    test_timeout: int,
    admitted_source_identity: str,
    admitted_deliverables_identity: str,
    observed_child_codes: list[int],
    native_tools: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], int]:
    receipt = directory / ("collection.json" if collect else f"chunk-{index:03d}.json")
    remaining = math.floor(deadline - time.monotonic())
    if remaining < 1:
        raise TimeoutError("runtime cell deadline exhausted before pytest launch")
    scope = "root" if project == root else project.relative_to(root / "projects").as_posix()
    resolved = RuntimeScope(root, scope)
    if (
        resolved.source_identity() != admitted_source_identity
        or resolved.deliverables_identity() != admitted_deliverables_identity
    ):
        raise ValueError("runtime source/deliverables changed before pytest child admission")
    providers = read_json(root, directory / "dependency-spec.json")
    audit_roots = runtime_provider_roots(root, providers, Path(sys.executable))
    spec_path = directory / (receipt.stem + "-spec.json")
    spec = {
        "schema_version": PYTEST_SPEC_SCHEMA,
        "root": str(root),
        "scope": scope,
        "directory": directory.relative_to(root).as_posix(),
        "run_id": run_id,
        "nonce": uuid.uuid4().hex,
        "receipt": receipt.relative_to(root).as_posix(),
        "collect": collect,
        "selectors": selectors,
        "test_timeout_seconds": test_timeout,
        "source_identity": admitted_source_identity,
        "deliverables_identity": admitted_deliverables_identity,
        "source_hashes": project_python_hashes(root, scope),
        "runtime": runtime_identity(),
        "dependency_providers": providers,
        "audit_roots": [str(path) for path in audit_roots],
    }
    spec_binding = write_json(root, spec_path, spec)
    command = pytest_command(
        Path(sys.executable),
        root,
        directory,
        run_id,
        scope,
        receipt,
        spec_path,
        selectors,
        spec_sha256=spec_binding["sha256"],
        collect=collect,
        test_timeout=test_timeout,
        audit_roots=audit_roots,
    )
    task = ProjectTestTask(
        index,
        project.relative_to(root).as_posix(),
        command,
        project,
        dict(os.environ),
        min(remaining, 600) if collect else remaining,
        capture_output=True,
    )
    if native_tools is None:
        result = run_project_test_matrix([task], workers=1)[0]
    else:
        from infrastructure.reporting.native_format_acceptance_checks import NativeToolUnavailable, native_tool_record
        from infrastructure.reporting.native_tool_producer import current_native_producer_operation

        owner = current_native_producer_operation()
        if owner is None:
            raise ValueError("native full-suite execution lost its genuine current Source owner")
        owner.verify(SnapshotReader(root), run_id=run_id, deadline=deadline)
        child_tools: list[dict[str, Any]] = []
        started = time.monotonic()
        launch_error: Exception | None = None
        try:
            native_tool_record(
                root,
                directory,
                command[0],
                list(command[1:]),
                env=dict(os.environ),
                deadline=deadline,
                phase_deadline=min(deadline, started + task.timeout_seconds),
                run_id=run_id,
                purpose=receipt.stem + "-native-tool",
                preserve_nominated_launcher=True,
                observed_tools=child_tools,
            )
        except (TimeoutError, NativeToolUnavailable) as error:
            launch_error = error
            if not child_tools:
                raise
        finally:
            # Keep actual child OS facts even if final retention/source custody
            # refuses after reap. These DATA facts cannot grant completion.
            native_tools.extend(child_tools)
            for packet in child_tools:
                actual = packet["observation"]
                actual_code = 130 if actual["original_exit_code"] in (130, -2) else actual["exit_code"]
                if type(actual_code) is int:
                    observed_child_codes.append(actual_code)
        if len(child_tools) != 1:
            raise ValueError("actual full-suite child lacks one exact Native ToolAPI observation")
        packet = child_tools[0]
        child = packet["observation"]
        # These fields came directly from the actual ToolAPI invocation above.
        # Incomplete custody cannot pass or mint a tool original capability.
        code = 130 if child["original_exit_code"] in (130, -2) else child["exit_code"]
        if type(code) is not int:
            code = 75
        result = ProjectTestResult(
            index,
            project.relative_to(root).as_posix(),
            code,
            timed_out=child["timed_out"],
            detail=child["diagnostic"],
            output_tail=(child["stdout"] + "\n" + child["stderr"])[-4000:],
            duration_seconds=time.monotonic() - started,
        )
        if child["custody_refused"] or packet.get("completion_authorized") is not True:
            failure_code = (
                130
                if child["original_exit_code"] in (130, -2)
                else 124
                if isinstance(launch_error, TimeoutError) or child["timed_out"]
                else 75
                if result.returncode == 0
                else result.returncode
            )
            observed_child_codes.append(failure_code)
            raise _RuntimeChildFailure(failure_code, "native pytest original custody/promotion refused")
    # Keep native supervised outcomes before any receipt/source read can fail.
    # Interruption and timeout remain dominant even with incomplete evidence.
    if native_tools is None:
        observed_child_codes.append(result.returncode)
    receipt_reader = SnapshotReader(root)
    observed_snapshot = receipt_reader.read(receipt.relative_to(root).as_posix()) if receipt.is_file() else None
    write_json(
        root,
        directory / ("collection-process.json" if collect else f"chunk-{index:03d}-process.json"),
        {
            "command": list(command),
            "spec_artifact": spec_binding,
            "nonce": spec["nonce"],
            "run_id": run_id,
            "receipt": receipt.relative_to(root).as_posix(),
            "receipt_sha256": observed_snapshot.sha256 if observed_snapshot is not None else None,
            "exit_code": result.returncode,
            "timed_out": result.timed_out,
            "duration_seconds": result.duration_seconds,
            "diagnostic": result.detail,
            "output_tail": result.output_tail,
        },
    )
    if result.returncode in (130, 124) or result.timed_out or not receipt.is_file():
        raise _RuntimeChildFailure(
            130 if result.returncode == 130 else 124 if result.timed_out else result.returncode,
            f"pytest subprocess failed without complete evidence: exit={result.returncode}; {result.output_tail}",
        )
    if observed_snapshot is None:
        raise ValueError("actual pytest child has no held receipt snapshot")
    observed = observed_snapshot.json_object()
    if not receipt_reader.unchanged():
        raise ValueError("pytest receipt changed after its actual child process observation")
    if observed.get("exit_code") != result.returncode:
        raise ValueError("pytest receipt differs from its actual supervised child exit")
    if result.returncode == 75 and observed.get("diagnostic"):
        from infrastructure.project.public_acceptance_dependencies import MissingRuntimeProvider

        raise MissingRuntimeProvider(str(observed["diagnostic"]))
    return observed, result.returncode


def run_cell(
    spec: dict[str, Any],
    spec_binding: dict[str, str],
    *,
    original_deadline: float | None = None,
    native_tools: list[dict[str, Any]] | None = None,
) -> int:
    """Produce raw collection/outcome/branch coverage evidence under the project lock."""
    root = Path(spec["root"]).resolve()
    scope = spec["scope"]
    resolved = RuntimeScope(root, scope)
    project = resolved.base
    directory = evidence_directory(root, root / spec["directory"])
    if any(path.is_symlink() for path in (project, project.parent, project.parent.parent)):
        raise ValueError("public project path is symlinked")
    run_id = spec["run_id"]
    timeout, test_timeout = spec["timeout_seconds"], spec["test_timeout_seconds"]
    if any(type(value) is not int or value < 1 for value in (timeout, test_timeout)):
        raise ValueError("cell and test deadlines must be finite positive integers")
    initial_runtime = runtime_identity()
    observed_child_codes: list[int] = []
    result: dict[str, Any] = {
        "schema_version": CELL_SCHEMA,
        "spec_artifact": spec_binding,
        "run_id": run_id,
        "scope": scope,
        "python_version": initial_runtime["python_version"],
        "runtime": initial_runtime,
        "status": "fail",
        "source_identity": spec["source_identity"],
        "deliverables_identity": spec["deliverables_identity"],
        "dependency_providers": spec.get("dependency_providers", {}),
        "observed_child_exit_codes": observed_child_codes,
    }
    deadline = time.monotonic() + timeout
    if original_deadline is not None:
        from infrastructure.reporting.native_tool_producer import current_native_producer_operation

        owner = current_native_producer_operation()
        if (
            type(original_deadline) not in (float, int)
            or not math.isfinite(original_deadline)
            or native_tools is None
            or owner is None
        ):
            raise ValueError("native cell needs its actual owner, observation sink and existing finite clock")
        deadline = min(deadline, original_deadline)
        owner.verify(SnapshotReader(root), run_id=run_id, deadline=deadline)
    elif native_tools is not None:
        raise ValueError("native cell cannot launch with a fresh replacement clock")
    try:
        if initial_runtime != spec["runtime"]:
            raise ValueError("selected interpreter or test stack changed after the bounded runtime probe")
        resolved.require_case_policy()
        if scope == "root" and list(resolved.test_files()) != spec["test_files"]:
            raise ValueError("root cell omitted or invented source-owned test files")
        with project_output_lock(project, timeout=min(timeout, max(0.0, deadline - time.monotonic()))):
            if resolved.source_identity() != spec["source_identity"]:
                raise ValueError("project source changed before full-selection execution")
            if resolved.deliverables_identity() != spec["deliverables_identity"]:
                raise ValueError("project deliverables changed before full-selection execution")
            sys.path[:0] = [str(project / "src"), str(project)]
            os.chdir(project)
            files = resolved.relative_tests(spec["test_files"])
            if not files or len(set(files)) != len(files):
                raise ValueError("source-owned full test-file selection is empty or duplicate")
            env = cell_environment(Path(sys.executable), directory, repo_root=root)
            result["build_policy"] = {
                name: env[name]
                for name in ("SOURCE_DATE_EPOCH", "TEMPLATE_BUILD_EPOCH_SOURCE", "TEMPLATE_EXECUTION_MODE")
            }
            # Retain the lock this cell actually acquired for its pytest descendants.
            env.update({key: value for key, value in os.environ.items() if key.startswith("TEMPLATE_PROJECT_LOCK_")})
            os.environ.update(env)
            write_json(root, directory / "dependency-spec.json", result["dependency_providers"])
            baseline, collection_exit = _run_pytest(
                root,
                project,
                directory,
                run_id,
                0,
                files,
                collect=True,
                deadline=deadline,
                test_timeout=test_timeout,
                admitted_source_identity=spec["source_identity"],
                admitted_deliverables_identity=spec["deliverables_identity"],
                observed_child_codes=observed_child_codes,
                native_tools=native_tools,
            )
            if collection_exit != 0 or not baseline.get("nodeids"):
                raise ValueError("full collection failed or was empty")
            groups = test_groups(project, files)
            observed = []
            exits = []
            for index, selectors in enumerate(groups, 1):
                receipt, exit_code = _run_pytest(
                    root,
                    project,
                    directory,
                    run_id,
                    index,
                    selectors,
                    collect=False,
                    deadline=deadline,
                    test_timeout=test_timeout,
                    admitted_source_identity=spec["source_identity"],
                    admitted_deliverables_identity=spec["deliverables_identity"],
                    observed_child_codes=observed_child_codes,
                    native_tools=native_tools,
                )
                if receipt.get("runtime") != initial_runtime:
                    raise ValueError("pytest child ran a different interpreter or test stack")
                observed.append(receipt)
                exits.append(exit_code)
            counts = aggregate_pytest(baseline, observed, run_id)
            result.update(
                counts,
                execution_exit_code=next((code for code in exits if code != 0), 0),
                test_files=spec["test_files"],
                groups=len(groups),
            )
            coverage = Coverage(data_file=str(directory / ".coverage"), config_file=str(project / "pyproject.toml"))
            coverage.load()
            coverage_path = directory / "coverage.json"
            coverage.json_report(outfile=str(coverage_path), pretty_print=True)
            coverage_data = read_json(root, coverage_path)
            result["coverage"] = {
                "path": coverage_path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(coverage_path.read_bytes()).hexdigest(),
                "percent": coverage_data["totals"]["percent_covered"],
                "branch_coverage": coverage_data.get("meta", {}).get("branch_coverage") is True,
            }
            if (
                any(counts[key] for key in ("failed", "errors", "skipped", "deselected"))
                or result["execution_exit_code"]
            ):
                raise ValueError("runtime tests failed, skipped or deselected; whole acceptance cannot pass")
            if (
                coverage_data["totals"].get("num_branches", 0) <= 0
                or coverage_data["totals"]["percent_covered"] < resolved.coverage_floor
            ):
                raise ValueError(f"own branch coverage did not meet the {resolved.coverage_floor} percent floor")
            result["status"] = "pass"
    except (OSError, ValueError, RuntimeError, TimeoutError) as error:
        result["diagnostic"] = str(error)[-5000:]
        from infrastructure.project.public_acceptance_dependencies import MissingRuntimeProvider

        if isinstance(error, (MissingRuntimeProvider, MissingRootCasePolicy)):
            result.update(status="blocked", execution_exit_code=75)
        elif isinstance(error, _RuntimeChildFailure):
            result["execution_exit_code"] = error.code
        elif isinstance(error, TimeoutError):
            result.update(status="fail", cell_exit_code=124)
    finally:
        try:
            result["source_identity_after"] = resolved.source_identity()
            result["deliverables_identity_after"] = resolved.deliverables_identity()
            if (
                result["source_identity_after"] != spec["source_identity"]
                or result["deliverables_identity_after"] != spec["deliverables_identity"]
                or runtime_identity() != initial_runtime
            ):
                result.update(
                    status="fail",
                    diagnostic="source, deliverables, interpreter or test stack changed during runtime cell",
                )
        except (OSError, ValueError):
            result.update(status="fail", diagnostic="runtime cell custody recheck failed")
        if result["status"] == "pass":
            try:
                verify_runtime_execution(project, root=root, scope=scope)
            except (OSError, ValueError, TimeoutError) as error:
                result.update(status="fail", diagnostic=str(error))
                if isinstance(error, TimeoutError):
                    result["cell_exit_code"] = 124
        if time.monotonic() >= deadline:
            result.update(
                status="fail", cell_exit_code=124, diagnostic="runtime cell deadline exhausted after final custody"
            )
        if 130 in observed_child_codes or 124 in observed_child_codes:
            result.update(status="fail", execution_exit_code=130 if 130 in observed_child_codes else 124)
        write_json(root, directory / "cell.json", result)
    original = result.get("execution_exit_code")
    return (
        130
        if original == 130
        else 124
        if original == 124 or result.get("cell_exit_code") == 124
        else 0
        if result["status"] == "pass"
        else 75
        if result["status"] == "blocked"
        else 1
    )


def main(argv: list[str] | None = None) -> int:
    """Handle an actual interpreter probe or one fresh matrix cell."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--spec-sha256")
    args = parser.parse_args(argv)
    if args.probe is not None:
        identity = runtime_identity()
        write_json(args.root.resolve(), args.probe, identity)
        return 75 if identity["missing"] else 0
    if args.spec is None:
        parser.error("--spec or --probe is required")
    if args.spec_sha256 is None or re.fullmatch(r"[0-9a-f]{64}", args.spec_sha256) is None:
        parser.error("--spec requires its original --spec-sha256")
    root = args.root.resolve()
    reader = SnapshotReader(root)
    snapshot = reader.read(args.spec.absolute().relative_to(root).as_posix())
    if snapshot.sha256 != args.spec_sha256:
        raise ValueError("runtime cell specification hash differs from its original admission")
    code = run_cell(snapshot.json_object(), {"path": snapshot.relative, "sha256": snapshot.sha256})
    if not reader.unchanged():
        return code if code in (130, 124) else 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
