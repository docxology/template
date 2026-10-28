"""Observe the actual artifacts of the already executed fresh Current Core.

The caller retains the genuine Current owner and previously admitted runtime
capabilities. This module does not execute Core/Common, construct authority
from receipts, project declared axes to passes, or reinterpret Original bytes
as a freshly executed Current writer.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes
from infrastructure.reporting.native_current_epub_engine_data import validate_current_epub_conversion_equivalence
from infrastructure.reporting.native_format_acceptance_contracts import (
    contract_digest,
    create_private_native_directory,
    native_artifact_contract,
    validate_native_specification,
)
from infrastructure.reporting.native_format_acceptance_validation import native_environment_for_replay
from infrastructure.reporting.native_format_acceptance_evidence import _file
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_format_observer_dispatch import observe_native_artifact
from infrastructure.reporting.native_format_observer_outcome import native_observer_outcome
from infrastructure.reporting.native_full_worker_pdfium import (
    NativePDFiumProvider,
    full_worker_pdfium_execution,
)
from infrastructure.reporting.native_mermaid_runtime_selection import current_source_mermaid_runtime_admission
from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
from infrastructure.reporting.native_office_diagram_source import prepare_office_diagram_source
from infrastructure.reporting.native_office_full_worker_context import (
    NativeOfficeReaderSelection,
    verify_office_font_nominations,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader
from infrastructure.validation.publication.audit import build_current_publication_audit, validate_publication_audit
from infrastructure.validation.publication.rendered_provenance import validate_current_rendered_provenance

SCHEMA = "template-native-current-artifact-join-v1"


def _observer_nominations(
    specification: dict[str, Any],
    root: Path,
    nominees: Mapping[str, Path | None],
) -> dict[str, Path | None]:
    """Compare explicit nominees with the externally pinned Source selection.

    These paths are DATA. The actual Source observer and live ToolAPI validate
    the selected native engines; neither these paths nor the spec grant access
    or process ownership. A shared frozen engine must be retained in Current.
    """
    names = {"epubcheck_jar", "java_executable", "frozen_epub_engine"}
    if not isinstance(nominees, Mapping) or set(nominees) != names:
        raise ValueError("Current observers require the complete explicit native tool nomination")
    source_tools = specification.get("observer_tools", dict.fromkeys(names))
    result: dict[str, Path | None] = {}
    for name in names:
        selected = nominees[name]
        label = source_tools[name]
        if name == "frozen_epub_engine":
            expected = None if label is None else root / label
            valid = selected == expected and (selected is None or isinstance(selected, Path))
        else:
            valid = (selected is None) == (label is None) and (
                selected is None or isinstance(selected, Path) and selected.is_absolute() and ".." not in selected.parts
            )
        if not valid:
            raise ValueError("Current observers require actual paired caller nominees and exact confined frozen DATA")
        result[name] = selected
    return result


def observe_current_native_artifact_join(
    scope: str,
    original_execution: ArtifactSnapshot,
    original_reader: SnapshotReader,
    current_pipeline: ArtifactSnapshot,
    current_reader: SnapshotReader,
    *,
    current_source: NativeSourceContext,
    current_stage: NativeStageChildReaderOperation,
    directory: Path,
    pdfium_provider: NativePDFiumProvider,
    pdfium_runtime: PDFiumRuntimeAdmission,
    office_font_files: tuple[Path, ...],
    decoded_pixel_budget: SourceImageDecodeBudget,
    observer_tools: Mapping[str, Path | None],
) -> dict[str, str]:
    """Join the complete Source roster to real separately executed Current bytes.

    Every retained native observer result is computed on the Current snapshot
    under its actual live owner. Source/compiler controls, consuming native
    roles, complete reference parity and scientific truth remain separate
    predicates. This returns only a binding to checked DATA, not a capability.
    """
    operation = require_native_operation(original_reader)
    original = operation.originals.get(scope)
    owner = current_native_producer_operation()
    if (
        original is None
        or not isinstance(current_source, NativeSourceContext)
        or type(current_stage) is not NativeStageChildReaderOperation
        or owner is None
        or owner.source is not current_source
        or current_reader.native_producer_operation is not owner
        or current_reader.native_operation is not None
        or current_reader.root != current_source.bindings.current_root
        or current_stage.source is not current_source
        or current_stage.scope != scope
        or current_stage.run_id != owner.run_id
        or current_stage.deadline != operation.deadline
        or owner.deadline != operation.deadline
        or owner.run_id == original.run_id
        or directory != owner.stage_scope_directory(scope) / "current-native-artifacts"
        or current_reader.root == original_reader.root
        or current_reader.root.is_relative_to(original_reader.root)
        or original_reader.root.is_relative_to(current_reader.root)
        or current_source.bindings.current_root_identity == operation.source.bindings.current_root_identity
        or current_source.reference.commit != operation.source.reference.commit
        or current_source.reference.source_identity != operation.source.reference.source_identity
        or current_source.bindings.expected_implementation_bytes
        != operation.source.bindings.expected_implementation_bytes
        or original_execution.relative != original.native_execution_relative
        or original_execution.sha256 != original.native_execution_sha256
        or original_reader.read(original_execution.relative) != original_execution
        or current_reader.read(current_pipeline.relative) != current_pipeline
        or current_pipeline.path != owner.stage_scope_directory(scope) / "current-analysis/pipeline.json"
    ):
        raise ValueError("Current artifact join lacks its actual separate Source/Core/stage owner and Original")
    root, deadline = current_reader.root, operation.deadline
    remaining(deadline)
    owner.verify(current_reader, run_id=owner.run_id, deadline=deadline)
    current_stage.verify(current_reader)
    if current_stage.records != tuple(owner.stage_children):
        raise ValueError("Current artifact join changed the genuine closed stage graph")
    pipeline = current_pipeline.json_object()
    if (
        pipeline["mode"] != "core"
        or pipeline["execution_exit_code"] != 0
        or pipeline["deadline_monotonic"] != deadline
        or pipeline["plan"]["project"] != scope
        or pipeline["stage_children"] != list(current_stage.records)
        or [item["stage_key"] for item in pipeline["outcomes"]] != pipeline["expected_stage_keys"]
        or any(
            item["status"] != "succeeded"
            or not (
                item["child_exit_code"] == 0
                or item["child_exit_code"] is None
                and item["in_process_completed"] is True
                and not item["attempt_exit_codes"]
            )
            for item in pipeline["outcomes"]
        )
    ):
        raise ValueError("Current native outputs require the actual complete successful Core and fixed stage roster")
    spec_file = original_reader.read(original.specification_relative)
    if spec_file.sha256 != original.specification_sha256:
        raise ValueError("Current artifact join changed the externally held Original specification")
    specification = spec_file.json_object()
    validate_native_specification(specification)
    if specification["scope"] != scope or specification["run_id"] != original.run_id:
        raise ValueError("Current artifact join specification belongs to a different actual Original")
    tools = _observer_nominations(specification, root, observer_tools)
    verify_office_font_nominations(specification["source_inputs"]["office_fonts"], office_font_files, deadline=deadline)
    original_provider = operation.pdfium_providers.get(scope)
    selection = operation.office_reader_selection
    if (
        not isinstance(original_provider, NativePDFiumProvider)
        or not isinstance(selection, NativeOfficeReaderSelection)
        or not isinstance(pdfium_provider, NativePDFiumProvider)
        or not isinstance(pdfium_runtime, PDFiumRuntimeAdmission)
        or pdfium_provider is original_provider
        or pdfium_provider.source is not current_source
        or pdfium_provider.scope != scope
        or pdfium_provider.deadline != deadline
        or pdfium_provider.selection != original_provider.selection
        or pdfium_runtime.source is not current_source
        or pdfium_runtime.scope != scope
        or pdfium_runtime.site != pdfium_provider.selection.site
        or pdfium_runtime.wheel != pdfium_provider.selection.wheel
        or pdfium_runtime.deadline != deadline
        or office_font_files != selection.font_files
        or not isinstance(decoded_pixel_budget, SourceImageDecodeBudget)
        or operation.office_decoded_pixel_budget is not None
        and decoded_pixel_budget is not operation.office_decoded_pixel_budget
    ):
        raise ValueError("Current native observers need actual preimport Current PDFium and shared decoder nominees")
    mermaid = current_source_mermaid_runtime_admission()
    if mermaid is None or mermaid.source is not current_source or mermaid.producer is not owner:
        raise ValueError("Current artifact join lost its genuinely re-admitted Source Mermaid runtime")
    formats = tuple(specification["formats"])
    raw = original_execution.json_object()
    create_private_native_directory(root, directory)
    env = native_environment_for_replay(root)
    attempt: dict[str, Any] = {
        "scope": scope,
        "original_run_id": original.run_id,
        "current_run_id": owner.run_id,
        "current_pipeline": {"path": current_pipeline.relative, "sha256": current_pipeline.sha256},
        "artifacts": [],
        "pdfium_runtime": None,
        "artifact": None,
        "claim_boundary": "partial Current observer DATA; no completed admission",
    }
    try:
        with (
            project_output_lock(root / "projects" / scope, timeout=remaining(deadline)),
            full_worker_pdfium_execution(
                pdfium_provider,
                directory=directory / "pdfium-runtime",
                deadline=deadline,
                runtime_admission=pdfium_runtime,
            ) as pdfium,
        ):
            if not validate_current_rendered_provenance(root, scope).valid:
                raise ValueError("fresh Current native artifacts lack current consumed rendered provenance")
            contract = native_artifact_contract(root, scope, formats, current_reader)
            old_rows = raw["artifacts"]
            if (
                raw["scope"] != scope
                or raw["run_id"] != original.run_id
                or raw["contract_digest"] != contract_digest(contract)
                or not isinstance(old_rows, list)
                or [{name: row[name] for name in ("id", "format", "path")} for row in old_rows]
                != [asdict(artifact) for artifact in contract]
            ):
                raise ValueError("Current complete Source artifact roster differs from the held Original")
            for ordinal, (artifact, old) in enumerate(zip(contract, old_rows, strict=True)):
                remaining(deadline)
                old_snapshot = original_reader.read(artifact.path)
                if old_snapshot.sha256 != old["sha256"]:
                    raise ValueError("Original native artifact changed before the actual Current join")
                snapshot = current_reader.read(artifact.path)
                row = {
                    **asdict(artifact),
                    "sha256": snapshot.sha256,
                    "original_input": {"path": old_snapshot.relative, "sha256": old_snapshot.sha256},
                    "current_input": {"path": snapshot.relative, "sha256": snapshot.sha256},
                    "current_parse": parse_native_bytes(artifact.format, snapshot.content),
                }
                attempt["artifacts"].append(row)
                admission = None
                if artifact.format in {"docx", "epub"}:
                    admission = prepare_office_diagram_source(
                        root,
                        directory / f"office-source-admission-{ordinal:04d}",
                        scope,
                        artifact,
                        current_source,
                        package_root=mermaid.selection.package_root,
                        runtime_admission=mermaid,
                        node_executable=mermaid.selection.node_executable,
                        chrome_executable=mermaid.selection.chrome_executable,
                        font_files=office_font_files,
                        decoded_pixel_budget=decoded_pixel_budget,
                        pdfium_runtime=pdfium.runtime,
                        env=env,
                        deadline=deadline,
                        run_id=owner.run_id,
                    )
                observed = observe_native_artifact(
                    root,
                    directory,
                    scope,
                    artifact,
                    snapshot,
                    current_reader,
                    env=env,
                    deadline=deadline,
                    run_id=owner.run_id,
                    ordinal=ordinal,
                    source_reference=current_source.reference,
                    verify_source_correspondence=current_source.verify_correspondence,
                    office_mermaid_admission=admission,
                    epubcheck_jar=tools["epubcheck_jar"],
                    java_executable=tools["java_executable"],
                    frozen_epub_engine=tools["frozen_epub_engine"],
                )
                if artifact.id == "manuscript:pdf":
                    from infrastructure.reporting.native_pdf_whole_source_witness import (
                        observe_current_whole_pdf_predicates,
                    )

                    observed["current_whole_pdf"] = observe_current_whole_pdf_predicates(
                        scope,
                        artifact,
                        snapshot,
                        observed["raster"],
                        observed["scientific_pdf_source"],
                        current_reader,
                        source=current_source,
                        pipeline_run_id=pipeline["run_id"],
                        plan_digest=pipeline["plan_digest"],
                        env=env,
                        deadline=deadline,
                    )
                    predicates = observed["current_whole_pdf"]["source_predicates"]
                    if predicates is not None and predicates["findings"]:
                        raise ValueError(
                            f"fresh Current Source reference disagrees with {artifact.id}: {predicates['findings']}"
                        )
                if observed["input"] != row["current_input"]:
                    raise ValueError("fresh Current native observer consumed a different exact artifact")
                # Evaluate the actual in-memory Current return, never producer
                # status or the later interpreter of transported Original bytes.
                result = native_observer_outcome(observed)
                row.update(native_observer=observed, findings=result["findings"], residuals=result["blockers"])
                if artifact.format == "epub" and tools["epubcheck_jar"] is not None:
                    old_native = old["native_observer"]["office_complete_source"]["native"]
                    current_native = observed["office_complete_source"]["native"]
                    for name in ("reference", "candidate"):
                        validate_current_epub_conversion_equivalence(
                            scope,
                            old_native[name]["conversion"],
                            current_native[name]["conversion"],
                            original_reader,
                            current_reader,
                        )
                if result["findings"] or result["status"] == "fail":
                    raise ValueError(f"fresh Current native observer failed for {artifact.id}: {result['findings']}")
            if not current_reader.unchanged() or not original_reader.unchanged():
                raise ValueError("Original/Current native artifact bytes changed during the complete observer loop")
        if pdfium.completed_binding is None:
            raise ValueError("Current PDFium actual Code/image closing did not complete")
        attempt["pdfium_runtime"] = pdfium.completed_binding
        tool_bindings = list(owner.retained_tool_bindings)
        for tool_binding in tool_bindings:
            event = _file(tool_binding, current_reader).json_object()
            owner.validate_tool(tool_binding, event, current_reader, run_id=owner.run_id)
        audit = build_current_publication_audit(current_source, scope, current_reader, deadline=deadline)
        if validate_publication_audit(audit, strict=True):
            raise ValueError("fresh Current complete rendered publication audit failed")
        audit_binding = write_json(root, directory / "publication-audit.json", audit.to_dict())
        current_source.verify_correspondence(current_source.reference, root, current_reader, deadline)
        current_stage.verify(current_reader)
        owner.verify(current_reader, run_id=owner.run_id, deadline=deadline)
        operation.verify(original_reader)
        if not current_reader.unchanged() or not original_reader.unchanged():
            raise ValueError("Original/Current Source and native observer closing custody changed")
        remaining(deadline)
        return write_json(
            root,
            directory / "native-artifact-join.json",
            {
                "schema_version": SCHEMA,
                "scope": scope,
                "source_binding": [current_source.reference.commit, current_source.reference.source_identity],
                "original_run_id": original.run_id,
                "current_run_id": owner.run_id,
                "current_pipeline": attempt["current_pipeline"],
                "current_pipeline_run_id": pipeline["run_id"],
                "current_plan_digest": pipeline["plan_digest"],
                "artifact_contract_digest": contract_digest(contract),
                "artifact_ids": [artifact.id for artifact in contract],
                "artifacts": attempt["artifacts"],
                "pdfium_runtime": pdfium.completed_binding,
                "publication_audit_artifact": audit_binding,
                "tool_artifacts": tool_bindings,
                "deadline_monotonic": deadline,
                "claim_boundary": (
                    "actual separately executed Current Core artifacts and fresh native positive observations; "
                    "writer causality, complete scientific/reference/control/consuming-role and release "
                    "admission remain separate predicates"
                ),
            },
        )
    except BaseException as error:
        # Retain only already observed DATA. Do not call an expired getter,
        # reread a process, infer OS outcomes, replace Core0, or mint success.
        if not isinstance(getattr(error, "native_current_artifact_attempt", None), dict):
            setattr(error, "native_current_artifact_attempt", attempt)
        raise
