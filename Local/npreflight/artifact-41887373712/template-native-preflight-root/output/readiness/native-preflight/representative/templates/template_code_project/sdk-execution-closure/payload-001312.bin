"""Actual declared project suites inside the genuine native Source owner.

Reuse the existing complete collection/chunk/branch-coverage controller. The
packet is DATA; original authority comes from the enclosing independently held
NativeOriginalLaunch and the actual ToolAPI children. A fresh current cell is
required. Complete suite success does not admit every scientific/native axis.
"""

from __future__ import annotations

import math
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_acceptance_cases import PYTEST_SPEC_SCHEMA, project_python_hashes, pytest_command
from infrastructure.project.public_acceptance_dependencies import admit_runtime_providers, runtime_provider_roots
from infrastructure.project.public_acceptance_evidence import (
    CELL_SCHEMA,
    aggregate_pytest,
    evidence_directory,
    runtime_identity,
    write_json,
)
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_acceptance_worker import run_cell, test_groups
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation, native_producer_operation
from infrastructure.reporting.native_tool_replay import (
    authenticate_original_native_artifact,
    validate_original_native_tool,
)
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCHEMA = "template-native-declared-project-suite-v1"
MODULES = (
    "reporting/native_project_domain.py",
    "project/public_acceptance_worker.py",
    "project/public_acceptance_cases.py",
    "reporting/native_tool_process.py",
    "reporting/native_format_acceptance_checks.py",
)
REMAINING = (
    "all-generated-value-scientific-domains-not-covered-by-declared-project-suite",
    "actual-analysis-leaf-read-write-and-registry-causal-consumption",
    "every-native-semantic-and-visual-generated-value-occurrence",
)


class NativeProjectDomainFailure(RuntimeError):
    """Attempt facts only; never an accepted ToolAPI or suite capability."""

    def __init__(self, code: int, attempt: dict[str, Any]) -> None:
        super().__init__(f"actual native project suite did not qualify (exit {code})")
        self.code = code
        self.native_project_domain_attempt = attempt


def _bound(value: object, reader: SnapshotReader) -> ArtifactSnapshot:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError("native declared suite requires exact retained artifact bindings")
    item = reader.read(value["path"])
    if item.sha256 != value["sha256"]:
        raise ValueError("native declared suite retained bytes changed")
    return item


def _plan(source: NativeSourceContext, scope: str, reader: SnapshotReader, deadline: float) -> dict[str, Any]:
    remaining(deadline)
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    resolved = RuntimeScope(reader.root, scope)
    if scope == "root":
        raise ValueError(
            "native project domain uses the canonical exemplar suite; Root retains its own case controller"
        )
    tests = resolved.test_files()
    if not tests or len(tests) > 10000:
        raise ValueError("native project domain needs the full bounded existing Source test roster")
    hashes = project_python_hashes(reader.root, scope, reader)
    metadata = reader.read(f"projects/{scope}/pyproject.toml")
    if metadata.content != source.reference.read(metadata.relative):
        raise ValueError("native declared suite metadata differs from genuine held Source")
    for name in tests:
        remaining(deadline)
        if reader.read(name).content != source.reference.read(name):
            raise ValueError("native declared suite test body differs from genuine held Source")
    body = {
        "scope": scope,
        "test_files": list(tests),
        "source_hashes": hashes,
        "metadata_artifact": {"path": metadata.relative, "sha256": metadata.sha256},
        "source_identity": resolved.source_identity(),
        "deliverables_identity": resolved.deliverables_identity(),
        "coverage_floor": resolved.coverage_floor,
    }
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    if not reader.unchanged():
        raise ValueError("native full-suite Source selection changed during admission")
    return {**body, "content_digest": canonical_digest(body)}


def observe_native_project_domain(
    source: NativeSourceContext,
    scope: str,
    directory: Path,
    reader: SnapshotReader,
    *,
    deadline: float,
    provider_wheels: Mapping[str, Path],
) -> dict[str, str]:
    """Execute the existing full suite under this actual current native owner.

    Wheel paths are independently nominated inputs, then admitted by existing
    Source dependency contracts. They do not authorize an installed provider.
    No test selector, planner callback, expected result or original is accepted.
    """
    owner = current_native_producer_operation()
    if owner is None or owner.source is not source:
        raise ValueError("native project suite needs its genuine already-active Source owner")
    owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    root = reader.root
    directory = evidence_directory(root, directory, fresh=True)
    plan = _plan(source, scope, reader, deadline)
    timeout = math.floor(remaining(deadline))
    if timeout < 1:
        raise TimeoutError("native declared suite lacks one second on the existing operation clock")
    requirements, faults = required_profile(root, reader, source.bindings.expected_source_identity)
    if faults:
        raise ValueError("native declared suite has no valid existing Source acceptance profile")
    providers = admit_runtime_providers(root, scope, provider_wheels, {row.id: row for row in requirements}, reader)
    runtime = runtime_identity()
    if runtime["missing"]:
        raise ValueError("native declared suite selected interpreter lacks the actual test stack")
    spec = {
        "root": str(root),
        "scope": scope,
        "directory": directory.relative_to(root).as_posix(),
        "run_id": owner.run_id,
        "runtime": runtime,
        "source_identity": plan["source_identity"],
        "deliverables_identity": plan["deliverables_identity"],
        "test_files": plan["test_files"],
        "timeout_seconds": timeout,
        "test_timeout_seconds": 120,
        "dependency_providers": providers,
    }
    runtime_binding = write_json(root, directory / "runtime.json", runtime)
    spec_binding = write_json(root, directory / "spec.json", spec)
    tools: list[dict[str, Any]] = []
    previous_cwd, previous_path, previous_env = Path.cwd(), list(sys.path), dict(os.environ)
    code = None
    cell_error: BaseException | None = None
    try:
        code = run_cell(spec, spec_binding, original_deadline=deadline, native_tools=tools)
    except (KeyboardInterrupt, Exception) as error:  # noqa: BLE001 - retain controller failure facts
        cell_error = error
    finally:
        # Existing run_cell is a standalone-worker controller. Its in-process
        # native use restores the actual owner environment even on interruption.
        os.chdir(previous_cwd)
        sys.path[:] = previous_path
        os.environ.clear()
        os.environ.update(previous_env)
    # Capture the actual returned controller result and ToolAPI sink first.
    # The live owner may already be expired; these DATA grant no capability.
    artifacts = {"spec.json": spec_binding, "runtime.json": runtime_binding}
    body = {
        "schema": SCHEMA,
        "run_id": owner.run_id,
        "scope": scope,
        "plan": plan,
        "runtime": runtime,
        "artifacts": artifacts,
        "native_tools": [{"artifact": item["artifact"]} for item in tools],
        "cell_exit_code": code,
        "remaining_obligations": list(REMAINING),
    }
    attempt = {
        "controller_exception": None
        if cell_error is None
        else {"type": type(cell_error).__name__, "message": str(cell_error)[-5000:]},
        "observation": body,
        "native_tools": list(tools),
        "artifact": None,
        "persistence_diagnostic": "",
        "verification_diagnostic": "",
    }
    interrupted = (
        code == 130
        or isinstance(cell_error, KeyboardInterrupt)
        or any(item["observation"]["original_exit_code"] in (130, -2) for item in tools)
    )
    timed_out = (
        code == 124 or isinstance(cell_error, TimeoutError) or any(item["observation"]["timed_out"] for item in tools)
    )
    failure_code = 130 if interrupted else 124 if timed_out else code or 1
    retained: dict[str, str] | None = None
    held = SnapshotReader(root)
    names = ["spec.json", "runtime.json", "cell.json", "dependency-spec.json", "coverage.json"]
    for index in range(len(tools)):
        stem = "collection" if index == 0 else f"chunk-{index:03d}"
        names.extend([stem + ".json", stem + "-spec.json", stem + "-process.json"])
    try:
        for name in names:
            remaining(deadline)
            path = directory / name
            if path.is_file():
                item = held.read(path.relative_to(root).as_posix())
                artifacts[name] = {"path": item.relative, "sha256": item.sha256}
        if not held.unchanged():
            raise ValueError("native declared suite evidence changed after actual child observations")
        remaining(deadline)
        retained = write_json(root, directory / "native-project-domain.json", body)
        attempt["artifact"] = retained
    except (OSError, ValueError, TimeoutError) as error:
        attempt["persistence_diagnostic"] = str(error)[-5000:]
        # A real 130/124 returned by run_cell dominates retention expiry/failure.
        if failure_code not in (130, 124) and isinstance(error, TimeoutError):
            failure_code = 124
        raise NativeProjectDomainFailure(failure_code, attempt) from error
    if cell_error is not None or type(code) is not int or code != 0 or interrupted or timed_out:
        raise NativeProjectDomainFailure(failure_code, attempt) from cell_error
    try:
        owner.verify(reader, run_id=owner.run_id, deadline=deadline)
        remaining(deadline)
    except (OSError, ValueError, TimeoutError) as error:
        attempt["verification_diagnostic"] = str(error)[-5000:]
        raise NativeProjectDomainFailure(124 if isinstance(error, TimeoutError) else 1, attempt) from error
    if retained is None:
        raise NativeProjectDomainFailure(1, attempt)
    return retained


def _validate(
    packet: dict[str, Any],
    reader: SnapshotReader,
    source: NativeSourceContext,
    *,
    original: bool,
    deadline: float,
    source_labels: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if set(packet) != {
        "schema",
        "run_id",
        "scope",
        "plan",
        "runtime",
        "artifacts",
        "native_tools",
        "cell_exit_code",
        "remaining_obligations",
    }:
        raise ValueError("native project suite fields differ from the fixed Source contract")
    if packet["schema"] != SCHEMA or packet["remaining_obligations"] != list(REMAINING):
        raise ValueError("native project suite changed its qualified claim boundary")
    if packet["plan"] != _plan(source, packet["scope"], reader, deadline) or packet["cell_exit_code"] != 0:
        raise ValueError("native declared suite did not complete its exact full Source plan")
    artifacts, tools = packet["artifacts"], packet["native_tools"]
    if not isinstance(artifacts, dict) or not isinstance(tools, list) or not 2 <= len(tools) <= 10000:
        raise ValueError("native full suite needs actual whole collection and every declared chunk")
    cell = _bound(artifacts.get("cell.json"), reader).json_object()
    spec_item = _bound(artifacts.get("spec.json"), reader)
    spec = spec_item.json_object()
    if _bound(artifacts.get("runtime.json"), reader).json_object() != packet["runtime"]:
        raise ValueError("native suite actual retained interpreter/test stack differs from its child observations")
    scope, run_id, plan = packet["scope"], packet["run_id"], packet["plan"]
    command_root = Path(source_labels["current_mirror"]["root"]) if source_labels is not None else reader.root
    implementation_root = Path(source_labels["selected_sdk"]["package_root"]) if source_labels is not None else None
    directory = spec_item.path.parent
    if (
        cell.get("schema_version") != CELL_SCHEMA
        or cell.get("status") != "pass"
        or cell.get("spec_artifact") != artifacts["spec.json"]
        or spec.get("runtime") != packet["runtime"]
        or cell.get("runtime") != packet["runtime"]
        or cell.get("groups") != len(tools) - 1
        or spec.get("scope") != scope
        or spec.get("run_id") != run_id
        or cell.get("run_id") != run_id
        or spec.get("root") != str(command_root)
        or spec.get("directory") != directory.relative_to(reader.root).as_posix()
        or type(spec.get("timeout_seconds")) is not int
        or spec["timeout_seconds"] < 1
        or spec.get("test_timeout_seconds") != 120
        or cell.get("scope") != scope
        or cell.get("source_identity") != plan["source_identity"]
        or cell.get("deliverables_identity") != plan["deliverables_identity"]
        or cell.get("dependency_providers") != spec.get("dependency_providers")
        or spec.get("test_files") != plan["test_files"]
        or cell.get("test_files") != plan["test_files"]
        or spec.get("source_identity") != plan["source_identity"]
        or spec.get("deliverables_identity") != plan["deliverables_identity"]
        or cell.get("source_identity_after") != plan["source_identity"]
        or cell.get("deliverables_identity_after") != plan["deliverables_identity"]
    ):
        raise ValueError("native actual cell/spec/Source identity or complete chunk accounting differs")
    resolved = RuntimeScope(reader.root, scope)
    files = resolved.relative_tests(plan["test_files"])
    previous_path = list(sys.path)
    try:
        sys.path[:0] = [str(resolved.base / "src"), str(resolved.base)]
        groups = [files, *test_groups(resolved.base, files)]
    finally:
        sys.path[:] = previous_path
    if len(groups) != len(tools):
        raise ValueError("native actual suite omitted or invented a Source-declared chunk")
    receipts, nonces = [], set()
    for index, (tool_binding, selectors) in enumerate(zip(tools, groups, strict=True)):
        remaining(deadline)
        stem = "collection" if index == 0 else f"chunk-{index:03d}"
        test_spec = _bound(artifacts.get(stem + "-spec.json"), reader)
        test = test_spec.json_object()
        receipt = _bound(artifacts.get(stem + ".json"), reader)
        process = _bound(artifacts.get(stem + "-process.json"), reader).json_object()
        tool_item = _bound(tool_binding.get("artifact"), reader)
        tool = tool_item.json_object()
        if original:
            validate_original_native_tool(
                tool_binding["artifact"], tool, reader, run_id=run_id, required_sdk_modules=MODULES
            )
        else:
            owner = current_native_producer_operation()
            if owner is None:
                raise ValueError("current project suite replay lost its real ToolAPI owner")
            owner.validate_tool(tool_binding["artifact"], tool, reader, run_id=run_id)
        nonce = test.get("nonce")
        if not isinstance(nonce, str) or re.fullmatch(r"[0-9a-f]{32}", nonce) is None or nonce in nonces:
            raise ValueError("native actual suite repeated or omitted a child Source request nonce")
        nonces.add(nonce)
        command = pytest_command(
            Path(packet["runtime"]["executable"]),
            reader.root,
            directory,
            run_id,
            scope,
            receipt.path,
            test_spec.path,
            selectors,
            spec_sha256=test_spec.sha256,
            collect=index == 0,
            test_timeout=spec["test_timeout_seconds"],
            command_root=command_root if original else None,
            implementation_root=implementation_root if original else None,
            command_audit_roots=tuple(Path(name) for name in test["audit_roots"]) if original else None,
            # Original provider paths are authenticated labels from the real
            # Source-built spec/ToolAPI invocation. Never glob/open the removed
            # original runtime. Fresh current production uses its own roots.
            audit_roots=tuple(Path(name) for name in test["audit_roots"])
            if original
            else runtime_provider_roots(reader.root, spec["dependency_providers"], Path(sys.executable)),
        )
        if (
            test.get("schema_version") != PYTEST_SPEC_SCHEMA
            or test.get("root") != str(command_root)
            or test.get("directory") != directory.relative_to(reader.root).as_posix()
            or test.get("receipt") != receipt.relative
            or test.get("runtime") != packet["runtime"]
            or test.get("dependency_providers") != spec["dependency_providers"]
            or test.get("test_timeout_seconds") != spec["test_timeout_seconds"]
            or test.get("selectors") != selectors
            or test.get("source_hashes") != plan["source_hashes"]
            or test.get("source_identity") != plan["source_identity"]
            or test.get("deliverables_identity") != plan["deliverables_identity"]
            or test.get("run_id") != run_id
            or test.get("scope") != scope
            or test.get("collect") is not (index == 0)
            or process.get("command") != list(command)
            or tool.get("command") != list(command)
            or process.get("spec_artifact") != {"path": test_spec.relative, "sha256": test_spec.sha256}
            or process.get("receipt_sha256") != receipt.sha256
            or process.get("nonce") != nonce
            or process.get("exit_code") != 0
            or process.get("timed_out") is not False
            or tool.get("original_exit_code") != 0
            or tool.get("exit_code") != 0
            or tool.get("timed_out") is not False
            or tool.get("custody_refused") is not False
            or receipt.json_object().get("spec_artifact") != {"path": test_spec.relative, "sha256": test_spec.sha256}
            or receipt.json_object().get("exit_code") != 0
        ):
            raise ValueError("native full-suite child differs from its fixed actual Source request/OS outcome")
        observed = receipt.json_object()
        if (
            observed.get("nonce") != nonce
            or observed.get("scope") != scope
            or observed.get("runtime") != packet["runtime"]
            or observed.get("pytest_exit_code") != 0
            or observed.get("source_identity_before") != plan["source_identity"]
            or observed.get("source_identity_after") != plan["source_identity"]
            or observed.get("deliverables_identity_before") != plan["deliverables_identity"]
            or observed.get("deliverables_identity_after") != plan["deliverables_identity"]
            or observed.get("source_hashes_before") != plan["source_hashes"]
            or observed.get("source_hashes_after") != plan["source_hashes"]
            or observed.get("diagnostic") != ""
        ):
            raise ValueError("actual full-suite consumed Source/runtime observation differs from its genuine request")
        receipts.append(observed)
    counts = aggregate_pytest(receipts[0], receipts[1:], run_id)
    if any(counts[name] for name in ("failed", "errors", "skipped", "deselected")) or any(
        cell.get(name) != value for name, value in counts.items()
    ):
        raise ValueError("native actual whole collection/case union differs or has incomplete outcomes")
    requirements, faults = required_profile(reader.root, reader, source.bindings.expected_source_identity)
    if faults:
        raise ValueError("native suite cannot replay without its current Source acceptance profile")
    requirement = next(
        (row for row in requirements if row.id == f"{scope}:runtime:{packet['runtime']['python_version']}"), None
    )
    if requirement is None:
        raise ValueError("native suite selected an undeclared project runtime")
    from infrastructure.reporting.release_readiness_dependencies import _validate_provider_receipts

    _validate_provider_receipts(
        requirement,
        {
            **counts,
            "run_id": run_id,
            "dependency_providers": spec["dependency_providers"],
            "runtime_artifact": artifacts["runtime.json"],
        },
        reader,
        receipts,
    )
    coverage = _bound(artifacts.get("coverage.json"), reader)
    totals = coverage.json_object()
    if (
        totals.get("meta", {}).get("branch_coverage") is not True
        or totals.get("totals", {}).get("num_branches", 0) <= 0
        or totals["totals"]["percent_covered"] < plan["coverage_floor"]
        or cell.get("coverage", {}).get("sha256") != coverage.sha256
    ):
        raise ValueError("native actual own-source branch coverage did not meet its existing Source floor")
    if not reader.unchanged():
        raise ValueError("native full suite Source/evidence changed during original/current verification")
    return {
        "plan_digest": plan["content_digest"],
        "nodeids": counts["nodeids"],
        "counts": {key: counts[key] for key in ("collected", "passed", "failed", "errors", "skipped", "deselected")},
    }


def replay_native_project_domain(
    binding: object,
    reader: SnapshotReader,
    *,
    run_id: str,
    directory: Path,
    provider_wheels: Mapping[str, Path],
) -> dict[str, Any]:
    """Authenticate the actual original, then rerun the existing full current suite."""
    authority = authenticate_original_native_artifact(binding, reader, run_id=run_id, required_sdk_modules=MODULES)
    operation = authority["operation"]
    packet = authority["event"].json_object()
    if packet.get("run_id") != run_id or packet.get("scope") != authority["original"].scope:
        raise ValueError("native project suite differs from its independently held original scope/run")
    original = _validate(
        packet, reader, operation.source, original=True, deadline=operation.deadline, source_labels=authority["source"]
    )
    current_reader = SnapshotReader(reader.root)
    with native_producer_operation(
        operation.source, run_id=operation.source.bindings.run_id, deadline=operation.deadline
    ):
        current = observe_native_project_domain(
            operation.source,
            packet["scope"],
            directory,
            current_reader,
            deadline=operation.deadline,
            provider_wheels=provider_wheels,
        )
        result = _validate(
            _bound(current, current_reader).json_object(),
            current_reader,
            operation.source,
            original=False,
            deadline=operation.deadline,
        )
    if result != original or not reader.unchanged() or not current_reader.unchanged():
        raise ValueError("native original/current full Source suite plan/cases differ")
    operation.verify(reader)
    return {
        "original_artifact": binding,
        "current_artifact": current,
        **result,
        "remaining_obligations": list(REMAINING),
    }
