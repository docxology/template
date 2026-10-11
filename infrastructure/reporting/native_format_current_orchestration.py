"""Serial Current-root custody through existing Source/Git/SDK owner factories.

Destination and wheel paths nominate DATA. Only the independently selected
Source, SDK and existing live owner APIs admit execution; no packet mints one.
"""

from __future__ import annotations

import os
import stat
import sys
import time
import uuid
from contextlib import contextmanager
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import gate_payload, write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_format_acceptance_contracts import (
    NATIVE_SCHEMA,
    create_private_native_directory,
    native_environment,
    validate_native_specification,
)
from infrastructure.reporting.native_format_acceptance_results import _executed_failure_exit, _finalize_profile
from infrastructure.reporting.native_format_acceptance_validation import (
    validate_native_acceptance,
    validate_native_conformance,
)
from infrastructure.reporting.native_format_joint_source import (
    NativeReaderOperation,
    NativeSDKSelection,
    admit_native_source_operation,
    source_environment,
)
from infrastructure.reporting.native_hosted_original_producer import NativeHostedTransportRequest
from infrastructure.reporting.native_installed_invocation import NativeInstalledInvocationFailure
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidSelection,
    admit_source_mermaid_selection,
    source_mermaid_runtime_operation,
)
from infrastructure.reporting.native_preparation_resources import TRANSPORT_PEAK_BYTES, require_native_capacity
from infrastructure.reporting.native_readiness_input_copy import copy_source_mirror_data
from infrastructure.reporting.native_source_external_admission import NativeSourceContext, _physical_directory
from infrastructure.reporting.native_tool_process import run_native_tool_process
from infrastructure.reporting.native_tool_producer import current_native_producer_operation, native_producer_operation
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


if TYPE_CHECKING:
    from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
    from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission


def validate_current_destination(source: NativeSourceContext, destination: Path | None) -> tuple[int, int]:
    """Check the explicitly owned fresh scratch nomination without allocating."""
    if (
        not isinstance(source, NativeSourceContext)
        or not isinstance(destination, Path)
        or not destination.is_absolute()
        or ".." in destination.parts
        or "\\" in str(destination)
        or "\0" in str(destination)
        or destination.exists()
        or destination.is_symlink()
    ):
        raise ValueError("fresh Current analysis needs an explicit canonical unused destination")
    parent_identity = _physical_directory(destination.parent)
    parent = destination.parent.lstat()
    if parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) != 0o700:
        raise ValueError("fresh Current analysis destination must use the owned private launcher scratch parent")
    for protected in (
        source.bindings.current_root,
        source.reference.root,
        source.bindings.selected_sdk_package_root,
    ):
        if destination.is_relative_to(protected) or protected.is_relative_to(destination):
            raise ValueError("fresh Current root overlaps Original, selected Source or installed SDK")
    return parent_identity


def _prepare_current_root(
    original: NativeSourceContext,
    sdk: NativeSDKSelection,
    destination: Path,
    state: dict[str, Any],
    provider_wheels: Mapping[str, Path],
) -> tuple[NativeSourceContext, dict[str, Path]]:
    """Clone the held reference once; reuse the actual SDK and original clock."""
    if current_native_producer_operation() is not None:
        raise ValueError("Current root preparation cannot replace an active Original producer")
    deadline = state["deadline"]
    remaining(deadline)
    original.verify_correspondence(
        original.reference, original.bindings.current_root, SnapshotReader(original.bindings.current_root), deadline
    )
    if (
        sdk.package_root != original.bindings.selected_sdk_package_root
        or sdk.implementation_bytes != original.bindings.expected_implementation_bytes
    ):
        raise ValueError("Current root needs the same independently selected actual installed SDK")
    parent_identity = validate_current_destination(original, destination)
    require_native_capacity(destination.parent, peak_bytes=TRANSPORT_PEAK_BYTES, deadline=deadline)
    diagnostics = destination.parent / f"native-current-clone-{uuid.uuid4().hex}"
    diagnostics.mkdir(mode=0o700)
    source = original.reference.root
    env = native_environment(original.bindings.current_root, Path(sys.executable), state["directory"])
    env.update(source_environment(original))
    clone = run_native_tool_process(
        diagnostics,
        "git",
        ["clone", "--no-hardlinks", "--no-local", "--recurse-submodules", str(source), str(destination)],
        cwd=source,
        env=env,
        deadline=deadline,
        purpose="actual-native-independent-current-full-git-mirror",
        observed_processes=state["current_processes"],
    )
    state["current_clone_result"] = clone
    if clone["accepted"] is not True or clone["original_exit_code"] != 0:
        raise NativeInstalledInvocationFailure(clone)
    if _physical_directory(destination.parent) != parent_identity:
        raise ValueError("Current root owned scratch parent changed during its actual clone")
    copy_source_mirror_data(
        source, destination, expected_identity=original.reference.source_identity, deadline=deadline
    )
    current = admit_native_source_operation(
        destination, sdk, run_id=uuid.uuid4().hex, deadline=deadline, environment=env
    )
    if current.bindings.current_root_identity == original.bindings.current_root_identity:
        raise ValueError("fresh Current Source admission reused Original's physical root")
    # Wheel copies are DATA with genuine Original admission-derived bindings.
    # Current full configured suites independently inspect/import the same
    # installed distributions again. No environment or package is installed.
    original_reader = SnapshotReader(original.bindings.current_root)
    wheels: dict[str, Path] = {}
    for providers in state["original_provider_bindings"].values():
        for provider, declaration in providers.items():
            remaining(deadline)
            binding = declaration["wheel_artifact"]
            held = original_reader.read(binding["path"])
            if provider_wheels.get(provider) != held.path or held.sha256 != binding["sha256"]:
                raise ValueError("Original admitted provider wheel changed before Current DATA copy")
            target = destination / held.relative
            if provider in wheels and wheels[provider] != target:
                raise ValueError("Original admitted provider has conflicting wheel paths")
            if provider not in wheels:
                atomic_write_bytes_confined(destination, target, held.content, mode=0o600)
                if SnapshotReader(destination).read(held.relative).content != held.content:
                    raise ValueError("Current retained provider wheel DATA differs")
                wheels[provider] = target
    if not original_reader.unchanged() or _physical_directory(destination.parent) != parent_identity:
        raise ValueError("Original wheels or Current scratch parent changed during preparation")
    current.verify_correspondence(current.reference, destination, SnapshotReader(destination), deadline)
    remaining(deadline)
    return current, wheels


@contextmanager
def current_native_analysis_scope(
    source: NativeSourceContext,
    scope: str,
    directory: Path,
    mermaid: NativeMermaidSelection,
    *,
    deadline: float,
) -> Iterator[Path]:
    """Use genuine per-scope owners and re-admit the same nominated runtime."""
    root = source.bindings.current_root
    expected = root / "output/readiness" / f"native-current-{source.bindings.run_id}" / scope
    if directory != expected or scope not in PUBLIC_PROJECT_NAMES:
        raise ValueError("Current analysis scope differs from its exact caller-nominated held directory")
    _physical_directory(directory)
    with native_producer_operation(
        source, run_id=source.bindings.run_id, deadline=deadline, scope=scope, directory=directory
    ):
        runtime_directory = directory / "mermaid-controller-runtime"
        create_private_native_directory(root, runtime_directory)
        env = native_environment(root, Path(sys.executable), directory)
        env.update(source_environment(source))
        runtime = admit_source_mermaid_selection(
            mermaid, source, deadline=deadline, directory=runtime_directory, env=env
        )
        failure_packets: dict[str, Any] = {}
        try:
            with source_mermaid_runtime_operation(runtime, source=source, deadline=deadline):
                try:
                    yield directory
                except BaseException as error:
                    for name in ("native_current_pipeline", "native_project_domain_attempt"):
                        packet = getattr(error, name, None)
                        if isinstance(packet, dict):
                            failure_packets[name] = packet
                    code = getattr(error, "native_project_domain_exit_code", getattr(error, "code", None))
                    if type(code) is int and "native_project_domain_attempt" in failure_packets:
                        failure_packets["native_project_domain_exit_code"] = code
                    raise
        except BaseException as error:
            # A closing Source/runtime check can refuse after an already
            # observed failed core. Preserve those direct facts separately;
            # they cannot authorize successful completion or any Original.
            for name, packet in failure_packets.items():
                setattr(error, name, packet)
            raise


def preserve_current_attempts(result: dict[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve direct failure DATA without promoting it to successful custody."""
    processes = state.get("current_processes", [])
    failures = state.get("current_failures", [])
    domains = state.get("current_domain_failures", [])
    result["current_analysis_attempts"] = {"processes": processes, "failures": failures, "domain_failures": domains}
    codes = [result["exit_code"]]
    for actual in processes:
        if actual.get("original_exit_code") in (130, -2):
            codes.append(130)
        if actual.get("timed_out") is True:
            codes.append(124)
    for packet in failures:
        code = packet.get("observation", {}).get("execution_exit_code")
        if code in (124, 130):
            codes.append(code)
    for failure in domains:
        packet = failure["attempt"]
        code = packet.get("observation", {}).get("cell_exit_code")
        if code in (124, 130):
            codes.append(code)
        if failure.get("controller_exit_code") in (124, 130):
            codes.append(failure["controller_exit_code"])
        for tool in packet.get("native_tools", []):
            observed = tool.get("observation", {})
            if observed.get("original_exit_code") in (130, -2):
                codes.append(130)
            if observed.get("timed_out") is True:
                codes.append(124)
    if 130 in codes:
        result["exit_code"] = 130
    elif 124 in codes or time.monotonic() >= state["deadline"]:
        result["exit_code"] = 124
    return result


def finish_native_format_acceptance(
    source_context: NativeSourceContext,
    sdk_selection: NativeSDKSelection,
    current_destination: Path | None,
    mermaid_selection: NativeMermaidSelection | None,
    provider_wheels: Mapping[str, Path],
    state: dict[str, Any],
    *,
    epubcheck_jar: Path | None,
    java_executable: Path | None,
) -> dict[str, Any]:
    """Finish Original readback after its owner closes; run Current once per scope."""
    root = source_context.bindings.current_root
    selected, run_id, deadline = state["selected"], state["run_id"], state["deadline"]
    before, initial_fingerprint = state["before"], state["fingerprint"]
    requirements, admitted, directory = state["original_requirements"], state["admitted"], state["directory"]
    office_reader_selection = state["office_reader_selection"]
    prepared_reader_runtimes = state["prepared_reader_runtimes"]
    _state = state
    current_source: NativeSourceContext | None = None
    current_wheels: dict[str, Path] = {}
    current_pdfium: dict[str, NativePDFiumProvider] = {}
    current_pdfium_runtimes: dict[str, PDFiumRuntimeAdmission] = {}
    current_observer_tools: Mapping[str, Path | None] | None = None
    preparation_refusal: Exception | None = None
    try:
        current, fingerprint, final_requirements = _finalize_profile(root, before)
    except (OSError, ValueError, TypeError, KeyError) as error:
        # After launch, failed source custody/finalization is executed failure.
        # Preserve original interruption/timeout precedence and private attempts;
        # parser.error(2) is exclusively a pre-execution configuration result.
        codes = [item["observation"]["exit_code"] for item in admitted]
        code = _executed_failure_exit(codes)
        summary = {
            "run_id": run_id,
            "source_digest": before,
            "source_current": False,
            "complete_selection": selected == PUBLIC_PROJECT_NAMES,
            "selected_projects": list(selected),
            "observed_projects": len(admitted),
            "diagnostic": str(error),
            "results": [
                {
                    "project": item["scope"],
                    "status": "fail",
                    "execution_exit_code": item["observation"]["exit_code"],
                    "process_artifact": item["process"],
                    "native_execution_artifact": item["raw_binding"],
                }
                for item in admitted
            ],
        }
        payload = {
            "schema_version": SCHEMA_VERSION,
            "platform_version": requirements[0].platform_version,
            "source_fingerprint": initial_fingerprint,
            "roster": list(PUBLIC_PROJECT_NAMES),
            "gates": {},
            "native_formats": summary,
        }
        binding = write_json(root, directory / "receipt.json", payload)
        return preserve_current_attempts({"receipt": binding, "native_formats": summary, "exit_code": code}, state)
    final_lookup = {item.scope: item for item in final_requirements if item.kind == "formats"}
    gates: dict[str, Any] = {}
    summaries = []
    for item in admitted:
        scope, raw, observed = item["scope"], item["raw"], item["observation"]
        requirement = final_lookup[scope]
        details = {
            "schema_version": NATIVE_SCHEMA,
            "run_id": run_id,
            "execution_exit_code": observed["exit_code"],
            "specification_artifact": item["specification"],
            "process_artifact": item["process"],
            "native_execution_artifact": item["raw_binding"],
            "sdk_closure_artifact": observed["sdk_closure_artifact"],
            "formats": raw.get("formats", {}),
            "conformance_validated": False,
            "diagnostic": raw.get("diagnostic") or observed.get("diagnostic", ""),
        }
        status, blockers = "fail", []
        matching = (
            current
            and raw.get("schema_version") == NATIVE_SCHEMA
            and raw.get("scope") == scope
            and raw.get("run_id") == run_id
            and raw.get("source_digest_before") == before
            and raw.get("source_digest_after") == before
            and raw.get("execution_exit_code") == observed["exit_code"]
            and (
                not raw.get("pipeline")
                or raw.get("deliverables_identity_after") in {"", requirement.deliverables_identity}
            )
            and observed["original_exit_code"] == observed["exit_code"]
            and not observed["timed_out"]
            and not observed["custody_refused"]
            and item["original_launch"] is not None
        )
        if matching and raw.get("status") == "blocked" and observed["exit_code"] == 75:
            declared = raw.get("blockers")
            from infrastructure.reporting.native_oracle_phase import native_residual_rows

            if raw.get("native_oracle_requirements") is not None and native_residual_rows(declared):
                status, blockers = "blocked", declared
        if current and observed["custody_refused"] and observed["exit_code"] == 75:
            status, blockers = (
                "blocked",
                [{"tool": "native process guardian", "reason": observed["diagnostic"]}],
            )
        if matching and raw.get("status") in {"pass", "blocked"}:
            try:
                operation = NativeReaderOperation(
                    source_context,
                    deadline,
                    {row["scope"]: row["original_launch"] for row in admitted if row["original_launch"] is not None},
                    {row["scope"]: row["pdfium_provider"] for row in admitted if row["original_launch"] is not None},
                    office_reader_selection=office_reader_selection,
                    pdfium_runtime_admissions={
                        row["scope"]: prepared_reader_runtimes[row["scope"]]
                        for row in admitted
                        if row["original_launch"] is not None
                    },
                )
                reader = SnapshotReader(root, native_operation=operation)
                if not isinstance(current_destination, Path) or not isinstance(
                    mermaid_selection, NativeMermaidSelection
                ):
                    raise ValueError("Current conformance requires its independently nominated root and shared runtime")
                if preparation_refusal is not None:
                    raise preparation_refusal
                if current_source is None:
                    try:
                        current_source, current_wheels = _prepare_current_root(
                            source_context, sdk_selection, current_destination, state, provider_wheels
                        )
                        from infrastructure.reporting.native_full_worker_pdfium import (
                            NativePDFiumProvider,
                            admit_full_worker_pdfium_provider,
                        )
                        from infrastructure.reporting.native_office_diagram_runtime import admit_pdfium_runtime

                        # Admit ALL Current scopes before the first Current Core
                        # or retained-reader PDFium namespace import. These are
                        # fresh factory results for the actual separate Source;
                        # Original provider objects nominate physical paths only.
                        for original_item in admitted:
                            current_scope = original_item["scope"]
                            nominee = original_item["pdfium_provider"]
                            if not isinstance(nominee, NativePDFiumProvider) or current_scope in current_pdfium:
                                raise ValueError("Current PDFium needs one genuine Original nominee per admitted scope")
                            current_pdfium[current_scope] = admit_full_worker_pdfium_provider(
                                nominee.selection, current_source, scope=current_scope, deadline=deadline
                            )
                        for current_scope, current_provider in current_pdfium.items():
                            current_pdfium_runtimes[current_scope] = admit_pdfium_runtime(
                                current_source,
                                scope=current_scope,
                                site=current_provider.selection.site,
                                wheel=current_provider.selection.wheel,
                                deadline=deadline,
                            )
                        from infrastructure.reporting.native_current_epub_engine_data import (
                            prepare_current_epub_observer_tools,
                        )

                        # Choose a real completed EPUB-enabled Original from the
                        # full Source profile, rather than the first loop scope.
                        epub_scopes = [scope for scope in selected if "epub" in final_lookup[scope].formats]
                        if epub_scopes:
                            completed_epub = [scope for scope in epub_scopes if scope in operation.originals]
                            if not completed_epub:
                                raise ValueError(
                                    "Current shared EPUB input preparation lacks a genuinely "
                                    "completed selected Original"
                                )
                            current_observer_tools = prepare_current_epub_observer_tools(
                                completed_epub[0],
                                reader,
                                current_source,
                                epubcheck_jar=epubcheck_jar,
                                java_executable=java_executable,
                            )
                        else:
                            # Exact full-profile absence: unused path nominees
                            # confer no engine execution or completion authority.
                            original = operation.originals[scope]
                            specification_file = reader.read(original.specification_relative)
                            if specification_file.sha256 != original.specification_sha256:
                                raise ValueError(
                                    "unused Current observer selection changed its held Original specification"
                                )
                            specification = specification_file.json_object()
                            validate_native_specification(specification)
                            tools = specification.get(
                                "observer_tools",
                                dict.fromkeys(("epubcheck_jar", "java_executable", "frozen_epub_engine")),
                            )
                            if (
                                specification["scope"] != scope
                                or specification["run_id"] != original.run_id
                                or tools["epubcheck_jar"] != (None if epubcheck_jar is None else str(epubcheck_jar))
                                or tools["java_executable"]
                                != (None if java_executable is None else str(java_executable))
                            ):
                                raise ValueError(
                                    "unused Current observer nominees differ from the caller's actual Source selection"
                                )
                            label = tools["frozen_epub_engine"]
                            current_observer_tools = {
                                "epubcheck_jar": epubcheck_jar,
                                "java_executable": java_executable,
                                "frozen_epub_engine": None
                                if label is None
                                else current_source.bindings.current_root / label,
                            }
                    except BaseException as error:
                        current_observer_tools = None
                        current_pdfium.clear()
                        current_pdfium_runtimes.clear()
                        if isinstance(error, Exception):
                            preparation_refusal = error
                        raise
                current_directory = (
                    current_source.bindings.current_root
                    / "output/readiness"
                    / f"native-current-{current_source.bindings.run_id}"
                    / scope
                )
                create_private_native_directory(current_source.bindings.current_root, current_directory)
                try:
                    validator = validate_native_acceptance if raw["status"] == "pass" else validate_native_conformance
                    validator(
                        requirement,
                        details,
                        reader,
                        current_source=current_source,
                        current_directory=current_directory,
                        provider_wheels=current_wheels,
                        pdfium_provider=current_pdfium[scope],
                        pdfium_runtime=current_pdfium_runtimes[scope],
                        office_font_files=office_reader_selection.font_files,
                        current_observer_tools=current_observer_tools,
                    )
                except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
                    packet = getattr(error, "native_current_pipeline", None)
                    if isinstance(packet, dict):
                        state["current_failures"].append(packet)
                    domain_attempt = getattr(error, "native_project_domain_attempt", None)
                    if isinstance(domain_attempt, dict):
                        state.setdefault("current_domain_failures", []).append(
                            {
                                "attempt": domain_attempt,
                                "controller_exit_code": getattr(
                                    error, "native_project_domain_exit_code", getattr(error, "code", None)
                                ),
                            }
                        )
                    raise
                details["conformance_validated"] = True
                if raw["status"] == "pass":
                    status = "pass"
            except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
                details["diagnostic"] = str(error)
                status = "fail"
        binding = write_json(
            root,
            item["directory"] / "formats-gate.json",
            gate_payload(requirement, fingerprint, status, details, blockers),
        )
        gates[requirement.id] = {
            "status": status,
            "command": item["command"],
            "artifact": binding["path"],
            "artifact_sha256": binding["sha256"],
        }
        summaries.append(
            {
                "project": scope,
                "status": status,
                "execution_exit_code": observed["exit_code"],
                "conformance_validated": details["conformance_validated"],
                "diagnostic": details["diagnostic"],
                "blockers": blockers,
            }
        )
        # An actual Current interruption/timeout is terminal for this attempt.
        # Keep the partial gate census; later scopes must remain unqualified.
        if preserve_current_attempts({"exit_code": 1}, state)["exit_code"] in (124, 130):
            break
    codes = [item["observation"]["exit_code"] for item in admitted]
    states = [item["status"] for item in summaries]
    exit_code = (
        130
        if 130 in codes
        else 124
        if 124 in codes or time.monotonic() >= deadline
        else 1
        if not current or "fail" in states or len(admitted) != len(selected)
        else 75
        if "blocked" in states
        else 0
    )
    completion = preserve_current_attempts({"exit_code": exit_code}, state)
    exit_code = completion["exit_code"]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "platform_version": final_requirements[0].platform_version,
        "source_fingerprint": fingerprint,
        "roster": list(PUBLIC_PROJECT_NAMES),
        "gates": gates,
        "current_analysis_attempts": completion["current_analysis_attempts"],
        "native_formats": {
            "run_id": run_id,
            "source_digest": before,
            "source_current": current,
            "complete_selection": selected == PUBLIC_PROJECT_NAMES,
            "selected_projects": list(selected),
            "observed_projects": len(admitted),
            "results": summaries,
        },
    }
    binding = write_json(root, directory / "receipt.json", payload)
    result = {
        "receipt": binding,
        "native_formats": payload["native_formats"],
        "exit_code": exit_code,
        "current_analysis_attempts": completion["current_analysis_attempts"],
    }
    request = _state.get("hosted_transport")
    if request is not None:
        if not isinstance(request, NativeHostedTransportRequest):
            raise ValueError("native hosted transport requires its explicit Source-owned request")
        if exit_code == 0:
            from infrastructure.reporting.native_hosted_original_producer import pack_native_hosted_originals

            result["transport"] = pack_native_hosted_originals(
                source_context,
                {item["scope"]: item["original_launch"] for item in admitted},
                request.directory,
                repository=request.repository,
                run_id=request.run_id,
                deadline=deadline,
                native_receipt=SnapshotReader(root).read(binding["path"]),
            )
    return result
