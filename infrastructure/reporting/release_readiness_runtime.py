"""Independently validate complete source/spec/process-bound public pytest cells."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.project.public_acceptance_cases import PYTEST_SPEC_SCHEMA, project_python_hashes, pytest_command
from infrastructure.project.public_acceptance_dependencies import runtime_provider_roots
from infrastructure.project.public_acceptance_evidence import CELL_SCHEMA, aggregate_pytest, bootstrap_command
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.release_readiness_profile import Requirement


def _artifact(binding: object, reader: SnapshotReader) -> ArtifactSnapshot:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise ValueError("pytest execution requires exact artifact bindings")
    snapshot = reader.read(binding["path"])
    if not snapshot.content or snapshot.sha256 != binding["sha256"]:
        raise ValueError("pytest execution artifact differs from its admitted bytes")
    return snapshot


def _zero_process(process: dict[str, Any], command: tuple[str, ...], *, cell: bool = False) -> None:
    code = process.get("returncode" if cell else "exit_code")
    duration = process.get("duration_seconds")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool):
        raise ValueError("actual pytest/cell process has no finite observed duration")
    if (
        type(code) is not int
        or code != 0
        or process.get("timed_out") is not False
        or process.get("command") != list(command)
        or not math.isfinite(duration)
        or duration < 0
        or process.get("detail" if cell else "diagnostic") != ""
    ):
        raise ValueError("actual pytest/cell process did not complete its exact admitted invocation")


def validate_runtime_cases(
    requirement: Requirement,
    details: dict[str, Any],
    reader: SnapshotReader,
) -> list[dict[str, Any]]:
    """Require genuine complete cases regardless of whether a provider is declared."""
    root, scope = reader.root, requirement.scope
    if scope == "root":
        raise ValueError("Root evidence requires its complete case-policy reader")
    resolved = RuntimeScope(root, scope)
    if not requirement.test_files:
        raise ValueError("a source-owned public runtime cell and full test selection are required")
    run_id, cases, processes = (
        details.get("run_id"),
        details.get("case_artifacts"),
        details.get("pytest_process_artifacts"),
    )
    if (
        not isinstance(run_id, str)
        or not run_id
        or not isinstance(cases, list)
        or not cases
        or not isinstance(processes, list)
        or len(processes) != len(cases) + 1
    ):
        raise ValueError("runtime acceptance requires complete collection, case and original process receipts")
    runtime = _artifact(details.get("runtime_artifact"), reader).json_object()
    runtime.pop("execution_exit_code", None)
    runtime.pop("command", None)
    minor, executable = requirement.python_version, runtime.get("executable")
    if (
        minor not in ("3.14", "3.15")
        or runtime.get("python_version") != minor
        or runtime.get("implementation") != "CPython"
        or not isinstance(runtime.get("python_full_version"), str)
        or re.fullmatch(re.escape(minor) + r"\.\d+(?:(?:a|b|rc)\d+)?", runtime["python_full_version"]) is None
        or not isinstance(executable, str)
        or not Path(executable).is_absolute()
    ):
        raise ValueError("actual pytest runtime has an incoherent selected implementation/minor")
    source = resolved.source_identity()
    deliverables = resolved.deliverables_identity()
    if source != requirement.source_identity or deliverables != requirement.deliverables_identity:
        raise ValueError("runtime source/deliverables differ from the current required profile")
    hashes = project_python_hashes(root, scope, reader)
    providers = details.get("dependency_providers", {})
    if not isinstance(providers, dict):
        raise ValueError("runtime provider declaration is invalid")
    audit_roots = runtime_provider_roots(root, providers, Path(executable))
    cell_snap = _artifact(details.get("cell_artifact"), reader)
    cell_spec_snap = _artifact(details.get("cell_spec_artifact"), reader)
    cell_process = _artifact(details.get("cell_process_artifact"), reader).json_object()
    cell, cell_spec = cell_snap.json_object(), cell_spec_snap.json_object()
    directory = root / cell_snap.relative
    directory = directory.parent
    test_files = list(requirement.test_files)
    relative_tests = resolved.relative_tests(test_files)
    for value in (cell, cell_spec):
        if (
            value.get("run_id") != run_id
            or value.get("scope") != scope
            or value.get("runtime") != runtime
            or value.get("source_identity") != source
            or value.get("deliverables_identity") != deliverables
            or value.get("test_files") != test_files
            or value.get("dependency_providers", {}) != providers
        ):
            raise ValueError("runtime cell/spec differs from its exact source, runtime or selection")
    if (
        cell.get("schema_version") != CELL_SCHEMA
        or cell.get("status") != "pass"
        or cell.get("source_identity_after") != source
        or cell.get("deliverables_identity_after") != deliverables
        or cell.get("spec_artifact") != details["cell_spec_artifact"]
        or cell_spec.get("root") != str(root)
        or cell_spec.get("directory") != directory.relative_to(root).as_posix()
        or cell_process.get("run_id") != run_id
        or cell_process.get("spec_artifact") != details["cell_spec_artifact"]
        or type(cell_spec.get("timeout_seconds")) is not int
        or cell_spec["timeout_seconds"] <= 0
        or type(cell_spec.get("test_timeout_seconds")) is not int
        or cell_spec["test_timeout_seconds"] <= 0
    ):
        raise ValueError("runtime cell admission or completion evidence is incompatible")
    _zero_process(
        cell_process,
        bootstrap_command(
            Path(executable),
            root,
            "infrastructure.project.public_acceptance_worker",
            "--root",
            str(root),
            "--spec",
            str(cell_spec_snap.path),
            "--spec-sha256",
            cell_spec_snap.sha256,
            audit_roots=audit_roots,
        ),
        cell=True,
    )
    snapshots = [_artifact(details.get("collection_artifact"), reader), *[_artifact(item, reader) for item in cases]]
    if len({item.relative for item in snapshots}) != len(snapshots):
        raise ValueError("runtime acceptance repeats actual pytest evidence")
    receipts = [item.json_object() for item in snapshots]
    counts = aggregate_pytest(receipts[0], receipts[1:], run_id)
    if any(counts[key] for key in ("failed", "errors", "skipped", "deselected")) or any(
        counts[key] != cell.get(key) for key in counts
    ):
        raise ValueError("actual runtime case selection was incomplete or differs from the cell")
    if requirement.kind == "runtime" and any(
        details.get(key) != counts[key] for key in ("collected", "passed", "failed", "errors", "skipped", "deselected")
    ):
        raise ValueError("runtime assertion counts differ from actual complete pytest cases")
    if any(node.split("::", 1)[0] not in relative_tests for node in counts["nodeids"]):
        raise ValueError("actual collected pytest cases are outside the source-owned test selection")
    nonces: set[str] = set()
    for index, (snapshot, receipt, process_binding) in enumerate(zip(snapshots, receipts, processes, strict=True)):
        stem = "collection" if index == 0 else f"chunk-{index:03d}"
        if snapshot.path != directory / (stem + ".json"):
            raise ValueError("actual pytest artifact is outside its admitted cell/attempt")
        spec_snap = _artifact(receipt.get("spec_artifact"), reader)
        spec = spec_snap.json_object()
        process = _artifact(process_binding, reader).json_object()
        selectors, nonce = spec.get("selectors"), spec.get("nonce")
        if (
            spec_snap.path != directory / (stem + "-spec.json")
            or spec.get("schema_version") != PYTEST_SPEC_SCHEMA
            or spec.get("root") != str(root)
            or spec.get("scope") != scope
            or spec.get("run_id") != run_id
            or spec.get("directory") != directory.relative_to(root).as_posix()
            or spec.get("receipt") != snapshot.relative
            or receipt.get("receipt") != snapshot.relative
            or spec.get("collect") is not (index == 0)
            or spec.get("runtime") != runtime
            or spec.get("dependency_providers") != providers
            or spec.get("source_identity") != source
            or spec.get("deliverables_identity") != deliverables
            or spec.get("source_hashes") != hashes
            or spec.get("audit_roots") != [str(item) for item in audit_roots]
            or spec.get("test_timeout_seconds") != cell_spec["test_timeout_seconds"]
            or not isinstance(nonce, str)
            or re.fullmatch("[0-9a-f]{32}", nonce) is None
            or nonce in nonces
            or not isinstance(selectors, list)
            or not selectors
            or any(not isinstance(item, str) or item.split("::", 1)[0] not in relative_tests for item in selectors)
            or index == 0
            and selectors != relative_tests
        ):
            raise ValueError("actual pytest spec is stale, foreign or outside the complete selection")
        nonces.add(nonce)
        if (
            receipt.get("nonce") != nonce
            or receipt.get("scope") != scope
            or receipt.get("runtime") != runtime
            or type(receipt.get("exit_code")) is not int
            or receipt["exit_code"] != 0
            or type(receipt.get("pytest_exit_code")) is not int
            or receipt["pytest_exit_code"] != 0
            or any(receipt.get("source_identity_" + phase) != source for phase in ("before", "after"))
            or any(receipt.get("deliverables_identity_" + phase) != deliverables for phase in ("before", "after"))
            or any(receipt.get("source_hashes_" + phase) != hashes for phase in ("before", "after"))
            or process.get("spec_artifact") != receipt.get("spec_artifact")
            or process.get("nonce") != nonce
            or process.get("run_id") != run_id
            or process.get("receipt") != snapshot.relative
            or process.get("receipt_sha256") != snapshot.sha256
        ):
            raise ValueError("pytest child completion/source/spec differs from its original observed process")
        _zero_process(
            process,
            pytest_command(
                Path(executable),
                root,
                directory,
                run_id,
                scope,
                snapshot.path,
                spec_snap.path,
                selectors,
                spec_sha256=spec_snap.sha256,
                collect=index == 0,
                test_timeout=cell_spec["test_timeout_seconds"],
                audit_roots=audit_roots,
            ),
        )
    return receipts
