"""Source-bound 25-project × supported-runtime acceptance using the existing matrix."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from infrastructure.core.testing.project_test_matrix import ProjectTestTask, run_project_test_matrix
from infrastructure.core.testing.pytest_profiles import TEST_RUNNER_BASE_DEPS
from infrastructure.project.public_acceptance_evidence import (
    CELL_SCHEMA,
    RUNTIME_PROBE_SCRIPT,
    aggregate_pytest,
    bootstrap_command,
    cell_environment,
    evidence_directory,
    gate_payload,
    read_json,
    write_json,
)
from infrastructure.project.public_acceptance_dependencies import (
    MissingRuntimeProvider,
    admit_runtime_providers,
    runtime_provider_roots,
)
from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.release_readiness_profile import Requirement, required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance

DEFAULT_ACCEPTANCE_TIMEOUT = 7200


def _probe_runtime(
    root: Path,
    directory: Path,
    runtime: str,
    interpreter: Path | None,
    *,
    expected_root_identity: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Probe the exact installed executable under a finite real child deadline."""
    probe_path = directory / f"runtime-{runtime}.json"
    if expected_root_identity is not None:
        current = root.stat(follow_symlinks=False)
        if root.is_symlink() or (current.st_dev, current.st_ino) != expected_root_identity:
            raise ValueError("runtime probe original physical Root changed before launch")
    if interpreter is None or not interpreter.is_file():
        return {
            "status": "blocked",
            "blockers": [
                {
                    "tool": f"Python {runtime}",
                    "reason": "no selected installed interpreter exists; automatic acquisition is disabled",
                }
            ],
            "command": [],
        }
    executable = interpreter.absolute()  # resolve() would discard a virtual environment's identity.
    command = (str(executable), "-I", "-c", RUNTIME_PROBE_SCRIPT, json.dumps([*TEST_RUNNER_BASE_DEPS, "coverage"]))
    task = ProjectTestTask(
        0, f"runtime-{runtime}", command, root, cell_environment(executable, directory, repo_root=root), 60, True
    )
    observed = run_project_test_matrix([task], workers=1)[0]
    process_outcome = {"execution_exit_code": observed.returncode, "timed_out": observed.timed_out}
    try:
        identity = json.loads(observed.output_tail)
        if not isinstance(identity, dict) or identity.get("python_version") != runtime:
            raise ValueError("selected executable is not the declared Python minor")
        if identity.get("executable") != str(executable):
            raise ValueError("selected executable identity differs from the actual child")
        binding = write_json(
            root,
            probe_path,
            {**identity, "execution_exit_code": observed.returncode, "command": list(command)},
            expected_root_identity=expected_root_identity,
        )
        if observed.returncode == 75 and identity.get("missing"):
            return {
                **process_outcome,
                "status": "blocked",
                "command": list(command),
                "binding": binding,
                "blockers": [
                    {"tool": name, "reason": "test dependency missing in selected installed environment"}
                    for name in identity["missing"]
                ],
            }
        if observed.returncode != 0 or observed.timed_out or identity.get("missing"):
            raise ValueError("selected interpreter preflight failed")
        return {
            **process_outcome,
            "status": "pass",
            "command": list(command),
            "binding": binding,
            "runtime": identity,
            "interpreter": executable,
        }
    except (OSError, ValueError, TypeError):
        binding = write_json(
            root,
            probe_path,
            {
                "status": "fail",
                "execution_exit_code": observed.returncode,
                "command": list(command),
                "timed_out": observed.timed_out,
                "diagnostic": observed.detail,
                "output_tail": observed.output_tail,
            },
            expected_root_identity=expected_root_identity,
        )
        return {
            **process_outcome,
            "status": "fail",
            "command": list(command),
            "binding": binding,
            "diagnostic": "selected runtime probe failed or mismatched",
        }


def _entry(
    root: Path,
    directory: Path,
    requirement: Requirement,
    fingerprint: str,
    status: str,
    command: Sequence[str],
    details: dict[str, Any],
    blockers: list[dict[str, str]] | None = None,
    *,
    expected_root_identity: tuple[int, int] | None = None,
) -> dict[str, Any]:
    payload = gate_payload(requirement, fingerprint, status, details, blockers)
    binding = write_json(
        root, directory / (requirement.kind + "-gate.json"), payload, expected_root_identity=expected_root_identity
    )
    return {
        "status": status,
        "command": list(command) or ["unavailable-selected-interpreter"],
        "artifact": binding["path"],
        "artifact_sha256": binding["sha256"],
    }


def _record_cell(
    root: Path,
    directory: Path,
    runtime_req: Requirement,
    coverage_req: Requirement,
    fingerprint: str,
    command: Sequence[str],
    process_exit: int,
    probe: dict[str, Any],
    run_id: str,
    dependency_providers: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Independently validate raw child evidence against the source-owned profile."""
    try:
        reader = SnapshotReader(root)
        raw = reader.read((directory / "cell.json").relative_to(root).as_posix()).json_object()
        if (
            raw.get("schema_version") != CELL_SCHEMA
            or raw.get("run_id") != run_id
            or raw.get("scope") != runtime_req.scope
            or raw.get("python_version") != runtime_req.python_version
            or raw.get("runtime") != probe["runtime"]
            or raw.get("source_identity_after") != runtime_req.source_identity
            or raw.get("deliverables_identity_after") != runtime_req.deliverables_identity
            or raw.get("dependency_providers", {}) != (dependency_providers or {})
        ):
            raise ValueError("cell raw evidence has stale runtime/source/deliverable bindings")
        if raw.get("status") == "blocked" and process_exit == 75:
            details = {"execution_exit_code": 75, "diagnostic": raw.get("diagnostic", "missing installed provider")}
            blockers = [{"tool": "installed public provider", "reason": details["diagnostic"]}]
            return (
                _entry(root, directory, runtime_req, fingerprint, "blocked", command, details, blockers),
                _entry(root, directory, coverage_req, fingerprint, "blocked", command, details, blockers),
                {
                    "project": runtime_req.scope,
                    "python_version": runtime_req.python_version,
                    "status": "blocked",
                    **details,
                },
            )
        collection_binding = None
        case_bindings = []
        process_bindings = []
        cell_snapshot = reader.read((directory / "cell.json").relative_to(root).as_posix())
        cell_spec = reader.read((directory / "spec.json").relative_to(root).as_posix())
        cell_process = reader.read((directory / "cell-process.json").relative_to(root).as_posix())
        if raw.get("status") == "pass":
            count = raw.get("groups")
            if type(count) is not int or count < 1:
                raise ValueError("passing cell has no explicit executed chunks")
            snapshots = [
                reader.read((directory / name).relative_to(root).as_posix())
                for name in (
                    "collection.json",
                    *(f"chunk-{index:03d}.json" for index in range(1, count + 1)),
                )
            ]
            baseline, *groups = [snapshot.json_object() for snapshot in snapshots]
            collection_binding, *case_bindings = [
                {"path": snapshot.relative, "sha256": snapshot.sha256} for snapshot in snapshots
            ]
            checked = aggregate_pytest(baseline, groups, run_id)
            if any(checked[key] != raw.get(key) for key in checked):
                raise ValueError("cell aggregate differs from exact full collection and case outcomes")
            for index, receipt in enumerate([baseline, *groups]):
                process_name = "collection-process.json" if index == 0 else f"chunk-{index:03d}-process.json"
                process_snapshot = reader.read((directory / process_name).relative_to(root).as_posix())
                process_bindings.append({"path": process_snapshot.relative, "sha256": process_snapshot.sha256})
                observed = process_snapshot.json_object()
                if (
                    receipt.get("runtime") != probe["runtime"]
                    or receipt.get("exit_code") != 0
                    or observed.get("exit_code") != 0
                    or observed.get("timed_out") is not False
                ):
                    raise ValueError("pytest child process/runtime evidence did not pass")
        actual_runtime = probe["runtime"]
        common = {
            "execution_exit_code": raw.get("execution_exit_code", process_exit),
            "python_version": runtime_req.python_version,
            "interpreter": actual_runtime["executable"],
            "implementation": actual_runtime["implementation"],
            "python_full_version": actual_runtime["python_full_version"],
            "runtime_artifact": probe["binding"],
            "run_id": run_id,
            "dependency_providers": dependency_providers or {},
            "collection_artifact": collection_binding,
            "case_artifacts": case_bindings,
            "pytest_process_artifacts": process_bindings,
            "cell_artifact": {"path": cell_snapshot.relative, "sha256": cell_snapshot.sha256},
            "cell_spec_artifact": {"path": cell_spec.relative, "sha256": cell_spec.sha256},
            "cell_process_artifact": {"path": cell_process.relative, "sha256": cell_process.sha256},
        }
        runtime_details = {
            **common,
            **{
                key: raw.get(key)
                for key in ("collected", "passed", "failed", "errors", "skipped", "deselected", "test_files")
            },
        }
        measured = raw.get("coverage", {})
        coverage_details = {
            **common,
            "percent": measured.get("percent"),
            "branch_coverage": measured.get("branch_coverage"),
            "coverage_artifact": {"path": measured.get("path"), "sha256": measured.get("sha256")},
        }
        entries = []
        for req, details in ((runtime_req, runtime_details), (coverage_req, coverage_details)):
            status = "fail"
            try:
                if process_exit or raw.get("status") != "pass":
                    raise ValueError("whole cell did not pass its execution and custody checks")
                validate_acceptance(req, {"details": details}, reader)
                if not reader.unchanged():
                    raise ValueError("consumed cell evidence changed during validation")
                status = "pass"
            except (OSError, ValueError, TypeError, KeyError):
                pass
            entries.append(_entry(root, directory, req, fingerprint, status, command, details))
        summary = {
            "project": runtime_req.scope,
            "python_version": runtime_req.python_version,
            "status": "pass" if all(entry["status"] == "pass" for entry in entries) else "fail",
            "execution_exit_code": process_exit,
            "collected": raw.get("collected", 0),
            "passed": raw.get("passed", 0),
            "skipped": raw.get("skipped", 0),
            "coverage_percent": measured.get("percent"),
            "diagnostic": raw.get("diagnostic", ""),
        }
        return entries[0], entries[1], summary
    except (OSError, ValueError, TypeError, KeyError):
        details = {
            "execution_exit_code": process_exit,
            "diagnostic": "fresh complete cell evidence is unavailable or custody mismatched",
        }
        return (
            _entry(root, directory, runtime_req, fingerprint, "fail", command, details),
            _entry(root, directory, coverage_req, fingerprint, "fail", command, details),
            {"project": runtime_req.scope, "python_version": runtime_req.python_version, "status": "fail", **details},
        )


def run_public_acceptance(
    root: Path,
    interpreters: Mapping[str, Path],
    *,
    timeout_seconds: int = DEFAULT_ACCEPTANCE_TIMEOUT,
    test_timeout_seconds: int = 120,
    project_workers: int = 1,
    projects: Sequence[str] | None = None,
    evidence_dir: Path | None = None,
    provider_wheels: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Run sequential runtime waves of bounded isolated project workers.

    The canonical default is the complete 75-cell product. Explicit project
    selection is diagnostic and never reports matrix_complete. Only actual
    source-owned runtime/coverage gates are emitted; missing release gates
    remain unknown in the release-readiness reader.
    """
    if (
        any(type(value) is not int or value <= 0 for value in (timeout_seconds, test_timeout_seconds, project_workers))
        or project_workers > 3
    ):
        raise ValueError("deadlines must be positive integers and project_workers must be between 1 and 3")
    if set(interpreters) - set(CANONICAL_CI_PYTHON_VERSIONS):
        raise ValueError("interpreter selection contains an unsupported runtime")
    selected = tuple(PUBLIC_PROJECT_NAMES if projects is None else projects)
    if not selected or len(set(selected)) != len(selected) or set(selected) - set(PUBLIC_PROJECT_NAMES):
        raise ValueError("project selection must be a nonempty unique canonical public subset")
    if provider_wheels is not None and set(provider_wheels) - set(PUBLIC_PROJECT_NAMES):
        raise ValueError("provider wheels must name canonical public project scopes")
    root = root.resolve()
    run_id = uuid.uuid4().hex
    directory = evidence_directory(root, evidence_dir or root / "output/readiness" / f"matrix-{run_id}", fresh=True)
    fingerprint = source_fingerprint(root)
    profile_reader = SnapshotReader(root)
    requirements, faults = required_profile(root, profile_reader, fingerprint)
    if faults:
        raise ValueError("source-owned required acceptance profile is incomplete or invalid")
    lookup = {requirement.id: requirement for requirement in requirements}
    gates: dict[str, Any] = {}
    summaries = []
    child_codes = []
    for runtime in CANONICAL_CI_PYTHON_VERSIONS:
        probe = _probe_runtime(root, directory, runtime, interpreters.get(runtime))
        if type(probe.get("execution_exit_code")) is int:
            child_codes.append(probe["execution_exit_code"])
        tasks = []
        cell_specs = {}
        for index, project in enumerate(selected):
            cell_dir = directory / project / runtime
            req = lookup[f"{project}:runtime:{runtime}"]
            coverage = lookup[f"{project}:coverage:{runtime}"]
            cell_probe = probe
            providers = {}
            if probe["status"] == "pass":
                try:
                    providers = admit_runtime_providers(root, project, provider_wheels or {}, lookup, profile_reader)
                except (OSError, ValueError, MissingRuntimeProvider) as error:
                    cell_probe = {
                        "status": "blocked" if isinstance(error, MissingRuntimeProvider) else "fail",
                        "command": probe["command"],
                        "diagnostic": str(error),
                        "blockers": [{"tool": "installed public provider", "reason": str(error)}],
                    }
            if cell_probe["status"] != "pass":
                details = {
                    "python_version": runtime,
                    "diagnostic": cell_probe.get("diagnostic", "selected tool unavailable"),
                    **{key: cell_probe[key] for key in ("execution_exit_code", "timed_out") if key in cell_probe},
                }
                if cell_probe.get("binding") is not None:
                    details["runtime_artifact"] = cell_probe["binding"]
                for requirement in (req, coverage):
                    gates[requirement.id] = _entry(
                        root,
                        cell_dir,
                        requirement,
                        fingerprint,
                        cell_probe["status"],
                        cell_probe["command"],
                        details,
                        cell_probe.get("blockers"),
                    )
                summaries.append({"project": project, "status": cell_probe["status"], **details})
                continue
            spec = {
                "root": str(root),
                "scope": project,
                "directory": cell_dir.relative_to(root).as_posix(),
                "run_id": run_id,
                "runtime": probe["runtime"],
                "source_identity": req.source_identity,
                "deliverables_identity": req.deliverables_identity,
                "test_files": list(req.test_files),
                "timeout_seconds": timeout_seconds,
                "test_timeout_seconds": test_timeout_seconds,
                "dependency_providers": providers,
            }
            spec_path = cell_dir / "spec.json"
            cell_specs[project] = write_json(root, spec_path, spec)
            profile_reader.read(spec_path.relative_to(root).as_posix())
            command = bootstrap_command(
                probe["interpreter"],
                root,
                "infrastructure.project.public_acceptance_worker",
                "--root",
                str(root),
                "--spec",
                str(spec_path),
                "--spec-sha256",
                cell_specs[project]["sha256"],
                audit_roots=runtime_provider_roots(root, providers, probe["interpreter"]),
            )
            tasks.append(
                ProjectTestTask(
                    index,
                    project,
                    command,
                    root,
                    cell_environment(probe["interpreter"], cell_dir, repo_root=root),
                    timeout_seconds + 30,
                    True,
                )
            )
        for result in run_project_test_matrix(tasks, workers=project_workers):
            child_codes.append(result.returncode)
            req = lookup[f"{result.project_name}:runtime:{runtime}"]
            coverage = lookup[f"{result.project_name}:coverage:{runtime}"]
            cell_dir = directory / result.project_name / runtime
            command = next(task.command for task in tasks if task.project_name == result.project_name)
            write_json(
                root,
                cell_dir / "cell-process.json",
                {
                    **asdict(result),
                    "command": list(command),
                    "run_id": run_id,
                    "spec_artifact": cell_specs[result.project_name],
                },
            )
            runtime_entry, coverage_entry, summary = _record_cell(
                root,
                cell_dir,
                req,
                coverage,
                fingerprint,
                command,
                result.returncode,
                probe,
                run_id,
                read_json(root, cell_dir / "spec.json")["dependency_providers"],
            )
            gates[req.id], gates[coverage.id] = runtime_entry, coverage_entry
            summaries.append(summary)
    try:
        current = source_fingerprint(root) == fingerprint
    except (OSError, ValueError):
        current = False
    counts = {
        status: sum(row["status"] == status for row in summaries) for status in ("pass", "fail", "blocked", "unknown")
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "platform_version": requirements[0].platform_version,
        "source_fingerprint": fingerprint,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": gates,
        "matrix": {
            "run_id": run_id,
            "matrix_complete": selected == PUBLIC_PROJECT_NAMES,
            "expected_cells": len(PUBLIC_PROJECT_NAMES) * len(CANONICAL_CI_PYTHON_VERSIONS),
            "selected_cells": len(selected) * len(CANONICAL_CI_PYTHON_VERSIONS),
            "observed_cells": len(summaries),
            "project_workers": project_workers,
            "source_current": current,
            "counts": counts,
            "results": summaries,
        },
    }
    receipt_path = directory / "receipt.json"
    binding = write_json(root, receipt_path, payload)
    exit_code = (
        130
        if 130 in child_codes
        else 124
        if 124 in child_codes
        else 0
        if current and counts["pass"] == len(summaries)
        else 75
        if current and not counts["fail"]
        else 1
    )
    return {
        "receipt": binding,
        "matrix": payload["matrix"],
        "exit_code": exit_code,
    }
