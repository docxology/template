"""One Original and one Current Office roster, followed by genuine paired replay."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import native_artifact_contract
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_mermaid_source_census import collect_current_source_mermaid_fences
from infrastructure.reporting.native_office_control_custody import (
    NativeOfficeControlOriginal,
    OfficeControlReaderOperation,
)
from infrastructure.reporting.native_office_control_supervisor import (
    OfficeNativeDependencies,
    _supervise_office_cases,
    SCOPES,
    KINDS,
    supervise_office_diagram_cohort,
)
from infrastructure.reporting.native_office_diagram_cohort import (
    execute_current_office_diagram_cohort,
    replay_office_diagram_cohort,
)
from infrastructure.reporting.native_office_diagram_positive import build_office_diagram_native_positive
from infrastructure.reporting.native_office_diagram_source import prepare_office_diagram_source
from infrastructure.reporting.native_office_full_worker_context import (
    NativeOfficeReaderSelection,
    OfficeCurrentReaderContext,
)
from infrastructure.reporting.native_office_nested_custody import OfficeNestedReaderOperation, retain_office_child
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidRuntimeAdmission,
    NativeMermaidSelection,
)
from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@dataclass(frozen=True)
class CurrentOfficeCohorts:
    source: NativeSourceContext
    children: dict[str, tuple[NativeOfficeControlOriginal, ...]]
    capabilities: tuple[NativeOfficeControlOriginal, ...]
    custody: dict[str, str]
    versions: dict[str, dict[str, Any]]


def _dependencies(
    selection: NativeMermaidSelection, fonts: tuple[Path, ...], site: Path, wheel: Path
) -> OfficeNativeDependencies:
    return OfficeNativeDependencies(
        selection.package_root,
        selection.dependency_root,
        selection.node_executable,
        selection.chrome_executable,
        fonts,
        site,
        wheel,
        None,
        None,
        None,
    )


def observe_office_scope_cohorts(
    source: NativeSourceContext,
    raw: dict[str, Any],
    specification: dict[str, Any],
    reader: SnapshotReader,
    runtime: NativeMermaidRuntimeAdmission,
    pdfium: PDFiumRuntimeAdmission,
    fonts: tuple[Path, ...],
    env: dict[str, str],
) -> dict[str, tuple[NativeOfficeControlOriginal, ...]]:
    """Run every Source-selected Office artifact after the existing full Core."""
    deadline, scope = specification["deadline_monotonic"], specification["scope"]
    dependencies = _dependencies(runtime.selection, fonts, pdfium.site, pdfium.wheel)
    raw["office_mermaid_census"] = collect_current_source_mermaid_fences(source, deadline=deadline).data()
    formats = tuple(specification["formats"])
    kinds = tuple(kind for kind in ("docx", "epub") if kind in formats)
    held_children: dict[str, tuple[NativeOfficeControlOriginal, ...]] = {}
    for kind in kinds:
        children = supervise_office_diagram_cohort(
            reader.root,
            reader.root / specification["directory"] / f"office-{kind}-cohort",
            source,
            pdfium,
            dependencies,
            scope=scope,
            kind=kind,
            interpreter=Path(sys.executable),
            env=env,
            deadline=deadline,
        )
        held_children[kind] = children
        raw["office_diagram_cohorts"][kind] = [retain_office_child(child, reader) for child in children]
    # Preserve the four existing Code/Textbook native capability cells once in
    # the Textbook scope. Its diagram rosters above are reused, never rerun.
    if scope == SCOPES[1]:
        cells = _supervise_office_cases(
            reader.root,
            reader.root / specification["directory"] / "office-capability-cells",
            source,
            pdfium,
            dependencies,
            cases=tuple((cell_scope, kind, "office-cell", None) for cell_scope in SCOPES for kind in KINDS),
            interpreter=Path(sys.executable),
            env=env,
            deadline=deadline,
        )
        raw["office_capability_cells"] = [retain_office_child(child, reader) for child in cells]
    return held_children


def execute_current_office_scope(
    source: NativeSourceContext,
    directory: Path,
    original_reader: SnapshotReader,
    scope: str,
    formats: tuple[str, ...],
    env: dict[str, str],
    *,
    pdfium_provider: NativePDFiumProvider,
    office_font_files: tuple[Path, ...],
) -> CurrentOfficeCohorts:
    """Child execution only: parent preimport provider is a genuine nomination."""
    operation = require_native_operation(original_reader)
    selection = operation.office_reader_selection
    provider = pdfium_provider
    if (
        not isinstance(selection, NativeOfficeReaderSelection)
        or not isinstance(provider, NativePDFiumProvider)
        or provider.source is not source
        or provider.scope != scope
        or provider.deadline != operation.deadline
        or office_font_files != selection.font_files
    ):
        raise ValueError("Current Office fixed children require fresh independently admitted Current Source nominees")
    provider.verify_current(deadline=operation.deadline)
    dependencies = _dependencies(
        selection.mermaid, office_font_files, provider.selection.site, provider.selection.wheel
    )
    census = collect_current_source_mermaid_fences(source, deadline=operation.deadline).data()
    original = operation.originals[scope]
    held = original_reader.read(original.native_execution_relative).json_object()
    if census != held["office_mermaid_census"]:
        raise ValueError("Current complete all25 source Mermaid fence census differs from held Original")
    children: dict[str, tuple[NativeOfficeControlOriginal, ...]] = {
        kind: execute_current_office_diagram_cohort(
            source.bindings.current_root,
            directory / f"office-{kind}-cohort",
            source,
            provider,
            dependencies,
            original_reader_root=original_reader.root,
            scope=scope,
            kind=kind,
            interpreter=Path(sys.executable),
            env=env,
            deadline=operation.deadline,
        )
        for kind in ("docx", "epub")
        if kind in formats
    }
    capabilities = (
        _supervise_office_cases(
            source.bindings.current_root,
            directory / "office-capability-cells",
            source,
            provider,
            dependencies,
            cases=tuple((cell_scope, kind, "office-cell", None) for cell_scope in SCOPES for kind in KINDS),
            interpreter=Path(sys.executable),
            env=env,
            deadline=operation.deadline,
        )
        if scope == SCOPES[1]
        else ()
    )
    from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation

    owner = current_native_producer_operation()
    if owner is None or owner.source is not source or owner.deadline != operation.deadline:
        raise ValueError("Current Office probes lost actual Source/live owner/clock")
    versions = {}
    for index, name in enumerate(("pdftoppm", "pdffonts")):
        record = native_tool_record(
            source.bindings.current_root,
            directory,
            name,
            ["-v"],
            env=env,
            deadline=operation.deadline,
            run_id=owner.run_id,
            purpose=f"office-cohort-version-{index}",
        )
        if record["exit_code"] != 0 or record["original_exit_code"] != 0:
            raise ValueError("Current Office actual version probe failed")
        versions[name] = record
    return CurrentOfficeCohorts(
        source,
        children,
        capabilities,
        {
            "root": str(source.bindings.current_root),
            "implementation_root": str(source.bindings.selected_sdk_package_root),
        },
        versions,
    )


def replay_office_scope_cohorts(
    original_reader: SnapshotReader,
    current_source: NativeSourceContext,
    current: CurrentOfficeCohorts,
    raw: dict[str, Any],
    context: OfficeCurrentReaderContext,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    env: dict[str, str],
    formats: tuple[str, ...],
    scope: str,
) -> dict[str, Any]:
    """Both completed tuples are retained outside JSON; one live reader positive."""
    operation = require_native_operation(original_reader)
    if type(current) is not CurrentOfficeCohorts or current.source is not current_source:
        raise ValueError("Office replay lost the actual returned Current tuple holder")
    current_children = current.children
    selection = operation.office_reader_selection
    if not isinstance(selection, NativeOfficeReaderSelection):
        raise ValueError("Office cohort replay requires exact externally selected Mermaid/fonts")
    original_rosters = raw["office_diagram_cohorts"]
    kinds = tuple(kind for kind in ("docx", "epub") if kind in formats)
    if (
        not isinstance(original_rosters, dict)
        or set(original_rosters) != set(kinds)
        or set(current_children) != set(kinds)
    ):
        raise ValueError("Office Source-declared artifact roster differs between actual Original and Current")
    if (
        collect_current_source_mermaid_fences(operation.source, deadline=operation.deadline).data()
        != raw["office_mermaid_census"]
    ):
        raise ValueError("Office reader complete all25 source fence census differs")
    checked = {}
    for kind in kinds:
        original_role = OfficeNestedReaderOperation(
            original_reader, original_rosters[kind], scope=scope, deadline=operation.deadline
        )
        nested_reader = SnapshotReader(
            original_reader.root, native_operation=operation, native_control_operation=original_role
        )
        current_role = OfficeControlReaderOperation(current_source, current_children[kind], deadline=operation.deadline)
        current_reader = SnapshotReader(current_source.bindings.current_root, native_control_operation=current_role)
        artifacts = [
            artifact
            for artifact in native_artifact_contract(original_reader.root, scope, (kind,), original_reader)
            if artifact.id == f"manuscript:{kind}"
        ]
        if len(artifacts) != 1:
            raise ValueError("Office reader requires exact declared combined artifact")
        directory = context.directory / f"cohort-{kind}"
        admission = prepare_office_diagram_source(
            original_reader.root,
            directory / "source",
            scope,
            artifacts[0],
            operation.source,
            package_root=selection.mermaid.package_root,
            node_executable=selection.mermaid.node_executable,
            chrome_executable=selection.mermaid.chrome_executable,
            font_files=selection.font_files,
            decoded_pixel_budget=context.decoded_pixel_budget,
            pdfium_runtime=context.pdfium_runtime,
            env=env,
            deadline=operation.deadline,
            run_id=operation.source.bindings.run_id,
        )
        positive = (
            None
            if admission is None
            else build_office_diagram_native_positive(
                original_reader.root,
                directory / "positive",
                scope,
                artifacts[0],
                operation.source,
                admission,
                env=env,
                deadline=operation.deadline,
                run_id=operation.source.bindings.run_id,
            )
        )
        checked[kind] = replay_office_diagram_cohort(
            original_reader.root,
            original_role.originals,
            original_role,
            nested_reader,
            current_children[kind],
            current_role,
            current_reader,
            scope=scope,
            kind=kind,
            reader_positive=positive,
            pdfium_runtime=context.pdfium_runtime,
            env=env,
            deadline=operation.deadline,
            custody=custody,
            versions=versions,
            current_custody=current.custody,
            current_versions=current.versions,
            reader_directory=directory / "paired-replay",
        )
    capabilities = raw["office_capability_cells"]
    wanted = tuple((cell_scope, kind) for cell_scope in SCOPES for kind in KINDS) if scope == SCOPES[1] else ()
    if (
        not isinstance(capabilities, list)
        or len(capabilities) != len(wanted)
        or len(current.capabilities) != len(wanted)
    ):
        raise ValueError("Office Original/Current Code/Textbook capability cells were omitted or duplicated")
    checked_capabilities = []
    if capabilities:
        role = OfficeNestedReaderOperation(original_reader, capabilities, scope=scope, deadline=operation.deadline)
        current_role = OfficeControlReaderOperation(current_source, current.capabilities, deadline=operation.deadline)
        current_reader = SnapshotReader(current_source.bindings.current_root, native_control_operation=current_role)
        nested_reader = SnapshotReader(original_reader.root, native_operation=operation, native_control_operation=role)
        for label, roster, selected_role, selected_reader in (
            ("original", role.originals, role, nested_reader),
            ("current", current.capabilities, current_role, current_reader),
        ):
            if tuple((item.scope, item.kind) for item in roster) != wanted or any(
                item.control != "office-cell" or item.expected_exit != 0 for item in roster
            ):
                raise ValueError("Office Original/Current four capability outcomes differ from fixed Source suite")
            for item in roster:
                admitted = selected_role.authenticate_artifact(
                    {"path": item.observation_relative, "sha256": item.artifact_hashes[item.observation_relative]},
                    selected_reader,
                    run_id=item.run_id,
                    required_sdk_modules=(
                        "reporting/native_office_diagram_control_worker.py",
                        "reporting/native_office_full_observer.py",
                    ),
                )
                observed = admitted["event"].json_object()
                if (
                    observed.get("scope") != item.scope
                    or observed.get("kind") != item.kind
                    or observed.get("control") != "office-cell"
                    or observed.get("oracle_exit_code") != 0
                ):
                    raise ValueError("Office capability observation differs from its actual fixed child oracle")
                checked_capabilities.append(
                    {"phase": label, "scope": item.scope, "kind": item.kind, "original_exit_code": item.expected_exit}
                )
            selected_role.verify(selected_reader)
    return {
        "scope": scope,
        "source_census": raw["office_mermaid_census"],
        "cohorts": checked,
        "capability_cells": checked_capabilities,
        "claim_boundary": "Root dispatcher consumes complete checked DATA; all native unsupported declarations remain",
    }
