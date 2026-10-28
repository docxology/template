"""Supervised fresh native rendering; incomplete visual acceptance stays blocked."""

from __future__ import annotations

import argparse
import hashlib
import os
import json
import math
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Sequence

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.core.implementation_custody import source_file_bytes
from infrastructure.reporting.native_format_acceptance_results import (
    _executed_failure_exit as _executed_failure_exit,
    _executed_failure_result as _original_executed_failure_result,
    _finalize_profile as _finalize_profile,
)
from infrastructure.reporting.native_projection_contracts import (
    ProjectionSourceUnsupported,
)
from infrastructure.reporting.native_source_provider_bootstrap import (
    selected_sdk_native_command,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_office_full_worker_context import (
    NativeOfficeReaderSelection,
    observe_office_font_nominations,
    verify_office_font_nominations,
)
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidSelection,
    NativeMermaidRuntimeAdmission,
)
from infrastructure.reporting.native_format_joint_source import (
    JOINT_SCHEMA,
    NativeSDKSelection,
    admit_native_source_operation,
    source_environment,
    worker_arguments,
)
from infrastructure.reporting.native_format_process_custody import (
    native_host_observation,
    require_native_platform,
)
from infrastructure.project.public_acceptance_cli import positive_int
from infrastructure.project.public_acceptance_evidence import (
    evidence_directory,
    read_json,
    write_json,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_format_acceptance_contracts import (
    PROCESS_SCHEMA,
    native_environment,
    public_source_digest,
    create_private_native_directory,
    native_deadline_guard,
    NativeDeadlineExpired,
    NativeDeadlineUnavailable,
)
from infrastructure.reporting.readiness_receipts import (
    source_fingerprint,
)
from infrastructure.reporting.release_readiness_profile import required_profile
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumSelection, admit_full_worker_pdfium_providers
from infrastructure.reporting.native_project_provider_batch import admitted_native_provider_batch
from infrastructure.reporting.native_original_progress import original_cell_progress
from infrastructure.reporting.native_hosted_original_producer import NativeHostedTransportRequest


def _executed_failure_result(state: dict[str, Any], error: BaseException) -> dict[str, Any]:
    """Preserve Original and directly returned Current failures independently."""
    from infrastructure.reporting.native_format_current_orchestration import preserve_current_attempts

    packet = getattr(error, "native_current_pipeline", None)
    if isinstance(packet, dict):
        state.setdefault("current_failures", []).append(packet)
    domain_attempt = getattr(error, "native_project_domain_attempt", None)
    if isinstance(domain_attempt, dict):
        state.setdefault("current_domain_failures", []).append(
            {
                "attempt": domain_attempt,
                "controller_exit_code": getattr(error, "native_project_domain_exit_code", getattr(error, "code", None)),
            }
        )
    return preserve_current_attempts(_original_executed_failure_result(state, error), state)


def _run_native_format_acceptance(
    root: Path,
    *,
    projects: Sequence[str] | None = None,
    timeout_seconds: int = 14400,
    evidence_dir: Path | None = None,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    expected_platform: str | None = None,
    sdk_selection: NativeSDKSelection | None = None,
    provider_wheels: dict[str, Path] | None = None,
    mermaid_selection: NativeMermaidSelection | None = None,
    pdfium_selection: NativePDFiumSelection | None = None,
    office_font_files: tuple[Path, ...] = (),
    current_analysis_root: Path | None = None,
    _state: dict[str, Any],
) -> dict[str, Any]:
    """Run fresh whole-core project plans serially under one admission deadline.

    The generated partial receipt owns only format gates. It neither merges
    old evidence nor grants runtime, domain, installed-package or publication
    acceptance. Pure source is frozen before execution; mutable deliverables
    enter the final readiness fingerprint only after regeneration settles.
    """
    started = _state["started"]
    try:
        valid_timeout = type(timeout_seconds) is int and timeout_seconds > 0 and math.isfinite(timeout_seconds)
    except OverflowError:
        valid_timeout = False
    if not valid_timeout:
        raise ValueError("native acceptance requires a positive finite whole-run timeout")
    expected_platform = require_native_platform(expected_platform)
    host_before = native_host_observation()
    if host_before["system"] != expected_platform:
        raise ValueError("native supervisor host differs from its prelaunch platform obligation")
    root = root.resolve()
    selected = tuple(projects) if projects is not None else PUBLIC_PROJECT_NAMES
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(scope not in PUBLIC_PROJECT_NAMES for scope in selected)
    ):
        raise ValueError("native acceptance requires unique canonical public project names")
    if (epubcheck_jar is None) != (java_executable is None):
        raise ValueError("native EPUB tools require both the reviewed JAR and actual Java executable")
    for tool in (epubcheck_jar, java_executable):
        if tool is not None and (not isinstance(tool, Path) or not tool.is_absolute() or ".." in tool.parts):
            raise ValueError("native EPUB tools require explicit absolute paths without traversal")
    run_id = uuid.uuid4().hex
    deadline = _state["deadline"]
    if sdk_selection is None:
        raise ProjectionSourceUnsupported("native producer requires an externally admitted selected SDK input")
    source_context = admit_native_source_operation(
        root, sdk_selection, run_id=run_id, deadline=deadline, environment=os.environ
    )
    from infrastructure.reporting.native_tool_producer import native_producer_operation
    from infrastructure.reporting.native_format_current_orchestration import (
        finish_native_format_acceptance,
        validate_current_destination,
    )

    validate_current_destination(source_context, current_analysis_root)
    with native_producer_operation(source_context, run_id=run_id, deadline=deadline):
        _run_admitted_native_format_acceptance(
            root,
            selected=selected,
            started=started,
            run_id=run_id,
            source_context=source_context,
            timeout_seconds=timeout_seconds,
            evidence_dir=evidence_dir,
            epubcheck_jar=epubcheck_jar,
            java_executable=java_executable,
            expected_platform=expected_platform,
            sdk_selection=sdk_selection,
            provider_wheels=provider_wheels,
            mermaid_selection=mermaid_selection,
            pdfium_selection=pdfium_selection,
            office_font_files=office_font_files,
            _state=_state,
        )
    # Both Original producer and Mermaid owners have now closed. Only the
    # externally held Original launch/provider capabilities survive this split.
    return finish_native_format_acceptance(
        source_context,
        sdk_selection,
        current_analysis_root,
        mermaid_selection,
        provider_wheels or {},
        _state,
        epubcheck_jar=epubcheck_jar,
        java_executable=java_executable,
    )


def _run_admitted_native_format_acceptance(
    root: Path,
    *,
    selected: tuple[str, ...],
    started: float,
    run_id: str,
    source_context: NativeSourceContext,
    timeout_seconds: int,
    evidence_dir: Path | None,
    epubcheck_jar: Path | None,
    java_executable: Path | None,
    expected_platform: str,
    sdk_selection: NativeSDKSelection,
    provider_wheels: dict[str, Path] | None,
    mermaid_selection: NativeMermaidSelection | None,
    pdfium_selection: NativePDFiumSelection | None,
    office_font_files: tuple[Path, ...],
    _state: dict[str, Any],
) -> None:
    """Hold the actual live Source producer across preparation and every worker."""
    deadline = _state["deadline"]
    host_before = native_host_observation()
    directory = evidence_directory(root, evidence_dir or root / "output/readiness" / f"native-{run_id}", fresh=True)
    observer_tools: dict[str, str | None] = {
        "epubcheck_jar": str(epubcheck_jar) if epubcheck_jar else None,
        "java_executable": str(java_executable) if java_executable else None,
        "frozen_epub_engine": None,
    }
    if epubcheck_jar is not None and java_executable is not None:
        from infrastructure.reporting.native_epub_observer import (
            bind_epubcheck_engine,
            freeze_epubcheck_bundle,
        )

        engine = bind_epubcheck_engine(epubcheck_jar, java_executable, deadline=started + timeout_seconds)
        frozen = freeze_epubcheck_bundle(root, directory, engine, deadline=started + timeout_seconds)
        observer_tools["frozen_epub_engine"] = frozen.parent.relative_to(root).as_posix()
    before = public_source_digest(root)
    deadline = started + timeout_seconds
    initial_fingerprint = source_fingerprint(root)
    requirements, faults = required_profile(root, SnapshotReader(root), initial_fingerprint)
    if faults:
        raise ValueError("source-owned readiness metadata is invalid or incomplete")
    lookup = {item.scope: item for item in requirements if item.kind == "formats"}
    if set(selected) - set(lookup):
        raise ValueError("selected projects lack declared native format requirements")
    admitted: list[dict[str, Any]] = _state["admitted"]
    _state.update(
        root=root,
        directory=directory,
        before=before,
        fingerprint=initial_fingerprint,
        deadline=deadline,
        run_id=run_id,
        selected=selected,
        platform_version=requirements[0].platform_version,
        original_requirements=requirements,
        current_processes=[],
        current_failures=[],
    )
    if not isinstance(mermaid_selection, NativeMermaidSelection):
        raise ProjectionSourceUnsupported(
            "native Source11 producer requires all four independently nominated runtime paths"
        )
    from infrastructure.reporting.native_mermaid_runtime_selection import (
        admit_source_mermaid_selection,
        source_mermaid_runtime_operation,
    )

    runtime_directory = directory / "mermaid-controller-runtime"
    create_private_native_directory(root, runtime_directory)
    _state["executed"] = True
    runtime = admit_source_mermaid_selection(
        mermaid_selection,
        source_context,
        deadline=deadline,
        directory=runtime_directory,
        env=native_environment(root, Path(sys.executable), directory),
    )
    with source_mermaid_runtime_operation(runtime, source=source_context, deadline=deadline):
        _run_original_native_cells(
            root,
            source_context=source_context,
            selected=selected,
            run_id=run_id,
            sdk_selection=sdk_selection,
            provider_wheels=provider_wheels,
            runtime=runtime,
            pdfium_selection=pdfium_selection,
            office_font_files=office_font_files,
            directory=directory,
            observer_tools=observer_tools,
            lookup=lookup,
            requirements=requirements,
            before=before,
            initial_fingerprint=initial_fingerprint,
            deadline=deadline,
            timeout_seconds=timeout_seconds,
            expected_platform=expected_platform,
            host_before=host_before,
            admitted=admitted,
            _state=_state,
        )


def _run_original_native_cells(
    root: Path,
    *,
    source_context: NativeSourceContext,
    selected: tuple[str, ...],
    run_id: str,
    sdk_selection: NativeSDKSelection,
    provider_wheels: dict[str, Path] | None,
    runtime: NativeMermaidRuntimeAdmission,
    pdfium_selection: NativePDFiumSelection | None,
    office_font_files: tuple[Path, ...],
    directory: Path,
    observer_tools: dict[str, str | None],
    lookup: dict[str, Requirement],
    requirements: tuple[Requirement, ...],
    before: str,
    initial_fingerprint: str,
    deadline: float,
    timeout_seconds: int,
    expected_platform: str,
    host_before: dict[str, Any],
    admitted: list[dict[str, Any]],
    _state: dict[str, Any],
) -> None:
    """Actual fully pinned originals under the live Source11 factory capability."""
    if not isinstance(pdfium_selection, NativePDFiumSelection):
        raise ProjectionSourceUnsupported(
            "native original requires independent PDFium site and Source wheel nomination"
        )
    office_fonts = observe_office_font_nominations(office_font_files, deadline=deadline)
    office_reader_selection = NativeOfficeReaderSelection(runtime.selection, office_font_files)
    # Admit every provider before the first reader imports a PDFium namespace.
    # Scope factories intentionally refuse post-import admission. Reusing a held
    # pre-import capability keeps subsequent cells inside that original boundary.
    prepared_providers = admitted_native_provider_batch(
        source_context, selected, provider_wheels or {}, Path(sys.executable), deadline=deadline
    )
    selections = tuple((scope, pdfium_selection) for scope in selected)
    prepared_pdfium = admit_full_worker_pdfium_providers(source_context, selections, deadline=deadline)
    from infrastructure.reporting.native_office_diagram_runtime import admit_pdfium_runtimes

    # Every scope holds its own genuine preimport admission. The complete fixed
    # selection closes Source custody before any provider capability escapes.
    prepared_reader_runtimes = admit_pdfium_runtimes(source_context, selections, deadline=deadline)
    _state.update(
        original_provider_bindings={scope: prepared_providers[scope][0] for scope in selected},
        office_reader_selection=office_reader_selection,
        prepared_reader_runtimes=prepared_reader_runtimes,
    )
    for scope in selected:
        original_cell_progress("selection-start", scope, deadline)
        cell = directory / scope
        create_private_native_directory(root, cell)
        providers, provider_roots = prepared_providers[scope]
        pdfium_provider = prepared_pdfium[scope]
        verify_office_font_nominations(office_fonts, office_font_files, deadline=deadline)
        provider_roots = (*provider_roots, *pdfium_provider.audit_roots)
        atomic_write_bytes_confined(
            root,
            cell / "implementation-input.json",
            sdk_selection.implementation_bytes,
            mode=0o600,
        )
        atomic_write_bytes_confined(
            root,
            cell / "source-descriptor.json",
            source_context.descriptor(scope, deadline=deadline),
            mode=0o600,
        )
        input_reader = source_context.current_source_reader
        implementation_input = input_reader.read((cell / "implementation-input.json").relative_to(root).as_posix())
        source_descriptor = input_reader.read((cell / "source-descriptor.json").relative_to(root).as_posix())
        closure_directory = cell / "sdk-execution-closure"
        create_private_native_directory(root, closure_directory)
        metadata = closure_directory.lstat()
        closure_identity = metadata.st_dev, metadata.st_ino
        source_inputs = {
            "schema_version": JOINT_SCHEMA,
            "descriptor": {
                "path": source_descriptor.relative,
                "sha256": source_descriptor.sha256,
            },
            "implementation": {
                "path": implementation_input.relative,
                "sha256": implementation_input.sha256,
            },
            "providers": providers,
            "mermaid_runtime": runtime.spec_data(),
            "pdfium": pdfium_provider.held_inputs(),
            "office_fonts": office_fonts,
            "provider_roots": list(map(str, provider_roots)),
            "closure": {
                "directory": closure_directory.relative_to(root).as_posix(),
                "identity": list(closure_identity),
            },
        }
        spec = {
            "scope": scope,
            "run_id": run_id,
            "directory": cell.relative_to(root).as_posix(),
            "formats": list(lookup[scope].formats),
            "source_digest": before,
            "timeout_seconds": timeout_seconds,
            "deadline_monotonic": deadline,
            "observer_tools": observer_tools,
            "expected_platform": expected_platform,
            "source_inputs": source_inputs,
        }
        specification = write_json(root, cell / "spec.json", spec)
        command = list(
            selected_sdk_native_command(
                Path(sys.executable),
                source_context,
                worker_arguments(
                    root,
                    cell / "spec.json",
                    specification["sha256"],
                    source_descriptor,
                    implementation_input,
                    closure_directory,
                    closure_identity,
                    source_context.bindings.current_root_identity,
                    runtime.spec_data(),
                    pdfium_provider,
                    office_fonts,
                ),
                provider_audit_roots=provider_roots,
                implementation_binding_path=implementation_input.path,
                audit_closure_directory=closure_directory,
                deadline=deadline,
            )
        )
        from infrastructure.reporting.native_original_supervisor import NativeOriginalSupervisor

        specification_snapshot = SnapshotReader(root).read(specification["path"])
        supervisor = NativeOriginalSupervisor(
            source_context,
            specification_snapshot,
            source_descriptor,
            implementation_input,
            tuple(command),
            closure_directory,
            closure_identity,
            deadline=deadline,
            pdfium_provider=pdfium_provider,
        )
        remaining = deadline - time.monotonic()
        observation: dict[str, Any] = {
            "schema_version": PROCESS_SCHEMA,
            "run_id": run_id,
            "command": command,
            "selected_interpreter": str(Path(sys.executable).absolute()),
            "source_environment": source_environment(source_context),
            "sdk_closure_artifact": None,
            "completed_monotonic": None,
            "exit_code": 124,
            "original_exit_code": None,
            "pid": None,
            "host_before": host_before,
            "host_after": {},
            "timed_out": True,
            "custody_refused": False,
            "diagnostic": "whole native deadline expired before worker launch",
        }
        item: dict[str, Any] = {
            "scope": scope,
            "directory": cell,
            "command": command,
            "process": None,
            "observation": observation,
            "specification": specification,
            "pdfium_provider": pdfium_provider,
            "raw_binding": None,
            "raw": {},
        }
        admitted.append(item)
        _state["executed"] = True
        if remaining > 0:
            observation.update(
                exit_code=1,
                timed_out=False,
                diagnostic="native attempt did not return an observed outcome",
            )
            try:
                worker_env = native_environment(root, Path(sys.executable), cell)
                worker_env.update(source_environment(source_context))
                original_cell_progress("worker-start", scope, deadline)
                observation.update(supervisor.launch(cell, worker_env))
            except KeyboardInterrupt:
                observation.update(
                    exit_code=130,
                    original_exit_code=None,
                    timed_out=False,
                    diagnostic="native supervisor interrupted",
                )
        if observation["pid"] is not None:
            original_cell_progress("worker-completed", scope, deadline)
        observation["host_after"] = native_host_observation()
        if observation["completed_monotonic"] is None:
            observation["completed_monotonic"] = time.monotonic()
        if observation["completed_monotonic"] >= deadline:
            observation.update(
                exit_code=130 if observation["exit_code"] == 130 else 124,
                timed_out=observation["exit_code"] != 130,
                diagnostic="original native operation expired before guardian completion",
            )
        try:
            closure_snapshot = SnapshotReader(root).read(
                (closure_directory / "receipt.json").relative_to(root).as_posix()
            )
            observation["sdk_closure_artifact"] = {
                "path": closure_snapshot.relative,
                "sha256": closure_snapshot.sha256,
            }
        except OSError, ValueError:
            pass
        process = write_json(root, cell / "process.json", observation)
        item["process"] = process
        raw_binding: dict[str, str] | None = None
        raw: dict[str, Any] = {}
        try:
            raw = read_json(root, cell / "native-execution.json")
            snapshot = SnapshotReader(root).read((cell / "native-execution.json").relative_to(root).as_posix())
            raw_binding = {"path": snapshot.relative, "sha256": snapshot.sha256}
        except OSError, ValueError:
            pass
        item.update(raw_binding=raw_binding, raw=raw, original_launch=None)
        closure_binding = observation["sdk_closure_artifact"]
        if isinstance(closure_binding, dict) and raw_binding is not None:
            try:
                terminal_reader = SnapshotReader(root)
                item["original_launch"] = supervisor.finish(
                    terminal_reader.read(process["path"]),
                    terminal_reader.read(closure_binding["path"]),
                    terminal_reader.read(raw_binding["path"]),
                )
            except (OSError, ValueError, TypeError, KeyError) as error:
                # Preserve the actual signed OS outcome and all raw original
                # bytes. Failed terminal Source/Code custody cannot mint a GO.
                observation["custody_refused"] = True
                observation["diagnostic"] = str(error)
                process = write_json(root, cell / "process.json", observation)
                item["process"] = process
        original_cell_progress("terminal-observed", scope, deadline)
        if observation["exit_code"] != 0 or observation["custody_refused"]:
            break


def run_native_format_acceptance(
    root: Path,
    *,
    projects: Sequence[str] | None = None,
    timeout_seconds: int = 14400,
    evidence_dir: Path | None = None,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    expected_platform: str | None = None,
    sdk_selection: NativeSDKSelection | None = None,
    provider_wheels: dict[str, Path] | None = None,
    mermaid_selection: NativeMermaidSelection | None = None,
    pdfium_selection: NativePDFiumSelection | None = None,
    office_font_files: tuple[Path, ...] = (),
    operation_started: float | None = None,
    hosted_transport: NativeHostedTransportRequest | None = None,
    current_analysis_root: Path | None = None,
) -> dict[str, Any]:
    """Keep invocation faults separate from the entire actual executed phase."""
    try:
        valid_timeout = type(timeout_seconds) is int and timeout_seconds > 0 and math.isfinite(timeout_seconds)
    except OverflowError:
        valid_timeout = False
    if not valid_timeout:
        raise ValueError("native acceptance requires a positive finite whole-run timeout")
    started = time.monotonic() if operation_started is None else operation_started
    if type(started) is not float or not math.isfinite(started) or started <= 0 or started > time.monotonic():
        raise ValueError("native caller must supply its actual already-started original operation clock")
    state: dict[str, Any] = {
        "executed": False,
        "admitted": [],
        "started": started,
        "deadline": started + timeout_seconds,
        "hosted_transport": hosted_transport,
    }
    try:
        with native_deadline_guard(state["deadline"]):
            result = _run_native_format_acceptance(
                root,
                projects=projects,
                timeout_seconds=timeout_seconds,
                evidence_dir=evidence_dir,
                epubcheck_jar=epubcheck_jar,
                java_executable=java_executable,
                expected_platform=expected_platform,
                sdk_selection=sdk_selection,
                provider_wheels=provider_wheels,
                mermaid_selection=mermaid_selection,
                pdfium_selection=pdfium_selection,
                office_font_files=office_font_files,
                current_analysis_root=current_analysis_root,
                _state=state,
            )
        if result["exit_code"] != 130 and time.monotonic() >= state["deadline"]:
            return _executed_failure_result(
                state,
                NativeDeadlineExpired("original native deadline expired during finalization"),
            )
        return result
    except ProjectionSourceUnsupported as error:
        if state["executed"]:
            return _executed_failure_result(state, error)
        return {
            "receipt": None,
            "native_formats": {
                "observed_projects": 0,
                "results": [],
                "diagnostic": str(error),
                "blockers": [
                    {
                        "tool": "authenticated native source/installed SDK",
                        "reason": str(error),
                    }
                ],
            },
            "exit_code": 75,
        }
    except NativeDeadlineUnavailable as error:
        return {
            "receipt": None,
            "native_formats": {
                "diagnostic": str(error),
                "blockers": [
                    {
                        "tool": "POSIX main-thread real-time deadline",
                        "reason": str(error),
                    }
                ],
            },
            "exit_code": 75,
        }
    except NativeDeadlineExpired as error:
        if not state["executed"]:
            return {
                "receipt": None,
                "native_formats": {
                    "diagnostic": str(error),
                    "observed_projects": 0,
                    "results": [],
                },
                "exit_code": 124,
            }
        return _executed_failure_result(state, error)
    except KeyboardInterrupt as error:
        if not state["executed"]:
            raise
        return _executed_failure_result(state, error)
    except Exception as error:  # noqa: BLE001 - every unexpected post-launch failure is an executed outcome
        if not state["executed"]:
            raise
        return _executed_failure_result(state, error)


def main(argv: list[str] | None = None) -> int:
    """Run the public native producer without dependency acquisition or publication."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).absolute().parents[2])
    parser.add_argument("--project", action="append", choices=PUBLIC_PROJECT_NAMES)
    parser.add_argument(
        "--timeout",
        type=positive_int,
        default=14400,
        help="Whole admission/execution/observer budget in seconds",
    )
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--current-analysis-root", required=True, type=Path)
    parser.add_argument("--epubcheck-jar", type=Path)
    parser.add_argument("--java-executable", type=Path)
    parser.add_argument("--expected-platform", required=True, choices=("Linux", "Darwin"))
    parser.add_argument("--sdk-package-root", required=True, type=Path)
    parser.add_argument("--implementation-input", required=True, type=Path)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--provider-wheel", action="append", default=[], metavar="SCOPE=PATH")
    parser.add_argument("--mermaid-package-root", required=True, type=Path)
    parser.add_argument("--mermaid-dependency-root", required=True, type=Path)
    parser.add_argument("--mermaid-node-executable", required=True, type=Path)
    parser.add_argument("--mermaid-chrome-executable", required=True, type=Path)
    parser.add_argument("--pdfium-site", required=True, type=Path)
    parser.add_argument("--pdfium-wheel", required=True, type=Path)
    parser.add_argument("--office-font-file", action="append", default=[], type=Path)
    parser.add_argument("--operation-started-monotonic", type=float)
    parser.add_argument("--hosted-transport-dir", type=Path)
    parser.add_argument("--hosted-repository")
    parser.add_argument("--hosted-run-id", type=int)
    args = parser.parse_args(argv)
    started = time.monotonic() if args.operation_started_monotonic is None else args.operation_started_monotonic
    try:
        transport_values = (args.hosted_transport_dir, args.hosted_repository, args.hosted_run_id)
        if any(value is not None for value in transport_values) and any(value is None for value in transport_values):
            raise ValueError("hosted native transport requires directory, actual repository and actual run ID together")
        transport = (
            NativeHostedTransportRequest(args.hosted_transport_dir, args.hosted_repository, args.hosted_run_id)
            if all(value is not None for value in transport_values)
            else None
        )
        implementation_bytes = source_file_bytes(args.implementation_input)
        if hashlib.sha256(implementation_bytes).hexdigest() != args.implementation_sha256:
            raise ValueError("selected SDK input differs from its explicit external hash")
        wheels: dict[str, Path] = {}
        for value in args.provider_wheel:
            scope, separator, path = value.partition("=")
            if not separator or scope not in PUBLIC_PROJECT_NAMES or scope in wheels or not path:
                raise ValueError("provider wheels require unique canonical SCOPE=PATH declarations")
            wheels[scope] = Path(path).absolute()
        result = run_native_format_acceptance(
            args.repo_root,
            projects=args.project,
            timeout_seconds=args.timeout,
            evidence_dir=args.evidence_dir,
            epubcheck_jar=args.epubcheck_jar,
            java_executable=args.java_executable,
            expected_platform=args.expected_platform,
            sdk_selection=NativeSDKSelection(args.sdk_package_root, implementation_bytes),
            provider_wheels=wheels,
            mermaid_selection=NativeMermaidSelection(
                args.mermaid_package_root,
                args.mermaid_dependency_root,
                args.mermaid_node_executable,
                args.mermaid_chrome_executable,
            ),
            pdfium_selection=NativePDFiumSelection(args.pdfium_site, args.pdfium_wheel),
            office_font_files=tuple(args.office_font_file),
            operation_started=started,
            hosted_transport=transport,
            current_analysis_root=args.current_analysis_root,
        )
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
