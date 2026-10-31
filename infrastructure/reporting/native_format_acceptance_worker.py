"""Fresh core execution and native observers for one admitted public project."""

from __future__ import annotations

from infrastructure.reporting.native_office_diagram_runtime import PDFiumRuntimeAdmission
from infrastructure.reporting.native_office_full_worker_context import verify_office_font_nominations
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_dependencies import capture_runtime_providers
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidSelection,
    NativeMermaidRuntimeAdmission,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_format_joint_source import (
    NativeSDKSelection,
    admit_native_source_operation,
    admitted_native_providers,
    bound_input,
)
from infrastructure.reporting.native_format_process_custody import native_host_observation
from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.fingerprints import source_content_fingerprint
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.project.public_acceptance_evidence import (
    evidence_directory,
    runtime_identity,
    verify_runtime_execution,
    write_json,
)
from infrastructure.reporting.native_format_acceptance_checks import (
    NativeToolUnavailable,
    native_tool_record,
    parse_native_bytes,
)
from infrastructure.reporting.native_format_acceptance_worker_artifacts import (
    observe_native_deliverables,
)
from infrastructure.reporting.native_format_acceptance_worker_closing import (
    close_native_worker_custody,
)
from infrastructure.reporting.native_format_acceptance_contracts import (
    CONTROL_SCHEMA,
    NATIVE_SCHEMA,
    contract_digest,
    native_artifact_contract,
    public_source_digest,
    validate_native_specification,
    native_environment,
    SOURCE_RENDER_ENV_NAMES,
)
from infrastructure.reporting.native_format_observer_dispatch import (
    observe_format_controls,
)
from infrastructure.project.native_format_library_custody import (
    observe_native_library_custody,
)
from infrastructure.reporting.native_format_portable_custody import (
    executable_observation,
    producer_custody,
)
from infrastructure.reporting.native_format_pdf_oracles import (
    PDF_CONTROL_CODES,
)
from infrastructure.reporting.native_print_artifact_observer import PRINT_SCOPES
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.native_hydration_reconstruction import observe_native_pdf_recomposition
from infrastructure.reporting.native_oracle_phase import NativeOraclePhase
from infrastructure.reporting.native_analysis_boundary_replay import observe_native_analysis_boundary_graph
from infrastructure.reporting.readiness_receipts import deliverable_identity
from infrastructure.rendering.config import RenderingConfig
from infrastructure.validation.publication.audit import (
    build_current_publication_audit,
    build_native_published_audit,
    format_publication_audit_json,
    validate_publication_audit,
)
from infrastructure.validation.publication.rendered_provenance import validate_current_rendered_provenance


from infrastructure.reporting.native_full_worker_pdfium import (
    NativePDFiumSelection,
    NativePDFiumProvider,
)
from infrastructure.reporting.native_full_worker_pdfium import (
    readmit_full_worker_pdfium_provider,
)


from infrastructure.reporting.native_format_worker_controls import (
    _parser_control,
    _pdf_oracle_control,
    run_pdf_oracle_control,
)


def _native_startup_phase(phase: str) -> None:
    try:
        observer = globals().get("_native_startup_observer")
        if observer is not None:
            observer(phase, sys._getframe(1))
    except Exception:
        pass


def require_canonical_native_stages(plan: Any) -> None:
    """A renamed or replaced no-op plan cannot certify existing native artifacts."""
    targets = [stage.script for stage in plan.stages]
    required = [f"scripts/pipeline/stage_{suffix}.py" for suffix in ("02_analysis", "03_render", "04_validate")]
    if any(targets.count(target) != 1 for target in required):
        raise ValueError("native acceptance requires each canonical analysis/render/validation target exactly once")
    if [targets.index(target) for target in required] != sorted(targets.index(target) for target in required):
        raise ValueError("native acceptance targets are not in analysis/render/validation order")


def _run_native_worker(
    root: Path,
    specification: dict[str, Any],
    *,
    source_context: NativeSourceContext,
    mermaid_runtime: NativeMermaidRuntimeAdmission,
    pdfium_runtime: PDFiumRuntimeAdmission,
    office_font_files: tuple[Path, ...],
    decoded_pixel_budget: SourceImageDecodeBudget,
    oracle_phases: list[NativeOraclePhase],
) -> dict[str, Any]:
    """Run the whole current core plan, then inspect exact native deliverables.

    Cleanup is explicitly omitted to preserve archived publication inputs.
    Resume and incremental reuse are disabled; the canonical render target
    removes its current renderer-owned outputs before producing them again.
    Shared infrastructure verification belongs to the separate root gate.
    """
    root = root.resolve()
    validate_native_specification(specification)
    host_before = native_host_observation()
    if host_before["system"] != specification["expected_platform"]:
        raise ValueError("native worker host differs from the supervisor platform obligation")
    if any(key in SOURCE_RENDER_ENV_NAMES or key.startswith("SLIDES_") for key in os.environ):
        raise ValueError("native worker received an ambient rendering override")
    scope, run_id = specification["scope"], specification["run_id"]
    directory = evidence_directory(root, root / specification["directory"])
    deadline = specification["deadline_monotonic"]
    from infrastructure.reporting.native_tool_producer import (
        current_native_producer_operation,
    )

    producer = current_native_producer_operation()
    if producer is None:
        raise ValueError("native worker requires its genuine live Source owner")
    native_reader = SnapshotReader(root, native_producer_operation=producer)
    source_context.verify_correspondence(source_context.reference, root, source_context.current_source_reader, deadline)
    formats = tuple(specification["formats"])
    before = public_source_digest(root)
    if before != specification["source_digest"]:
        raise ValueError("native admission source changed before execution")
    runtime = runtime_identity()
    interpreter_before = executable_observation(Path(sys.executable))
    runtime_binding = write_json(root, directory / "runtime.json", {**runtime, "execution_exit_code": 0})
    raw: dict[str, Any] = {
        "schema_version": NATIVE_SCHEMA,
        "native_oracle_requirements": None,
        "pid": os.getpid(),
        "host_before": host_before,
        "host_after": {},
        "scope": scope,
        "run_id": run_id,
        "status": "fail",
        "execution_exit_code": 1,
        "source_digest_before": before,
        "source_digest_after": "",
        "deliverables_identity_after": "",
        "runtime": runtime,
        "producer_custody": producer_custody(root, runtime, before),
        "interpreter_observation_before": interpreter_before,
        "interpreter_observation_after": {},
        "runtime_artifact": runtime_binding,
        "source_inputs": specification["source_inputs"],
        "runtime_providers": {"before": {}, "after": {}},
        "provider_metadata_artifacts": {},
        "pipeline": {},
        "hydration_reconstruction": None,
        "analysis_data_graph": None,
        "stage_children": [],
        "office_mermaid_census": None,
        "office_diagram_cohorts": {},
        "office_capability_cells": [],
        "native_project_domain": None,
        "loader_persistent_rx_control": None,
        "whole_pdf_cohort": None,
        "whole_pdf_source_controls": None,
        "formats": {},
        "artifacts": [],
        "contract_digest": "",
        "tool_artifacts": [],
        "negative_controls": [],
        "pdf_negative_controls": [],
        "observer_controls": {},
        "pitch_native_pairs": None,
        "library_custody_before": {},
        "library_custody_after": {},
        "publication_audit_artifact": {},
        "published_source_audit_artifact": {},
        "blockers": [],
        "diagnostic": "",
    }
    env = native_environment(root, Path(sys.executable), directory)
    try:
        if runtime["missing"] or runtime["python_version"] not in {
            "3.12",
            "3.13",
            "3.14",
        }:
            raise NativeToolUnavailable("selected supported interpreter/test stack is not prepared")
        providers = specification["source_inputs"]["providers"]
        provider_before, metadata_artifacts = capture_runtime_providers(
            root, providers, directory / "providers", retain_metadata=True
        )
        raw["runtime_providers"]["before"] = provider_before
        raw["provider_metadata_artifacts"] = metadata_artifacts
        raw["library_custody_before"] = observe_native_library_custody(formats, repo_root=root)
        reader = SnapshotReader(root)
        config_raw = reader.read(f"projects/{scope}/manuscript/config.yaml").content
        import yaml

        rendering = RenderingConfig.from_project_config(yaml.safe_load(config_raw), env={})
        for name, arguments in (
            (rendering.pandoc_path, ["--version"]),
            (rendering.latex_compiler, ["--version"]),
            ("pdftoppm", ["-v"]),
            ("pdffonts", ["-v"]),
        ):
            tool = native_tool_record(
                root,
                directory,
                name,
                arguments,
                env=env,
                deadline=deadline,
                run_id=run_id,
                purpose=f"tool-version-{len(raw['tool_artifacts'])}",
            )
            raw["tool_artifacts"].append(tool["artifact"])
            if tool["exit_code"] != 0 or tool["original_exit_code"] != 0:
                raise ValueError("actual native tool version probe failed")
        with project_output_lock(root / "projects" / scope, timeout=max(0.0, deadline - time.monotonic())):
            published = build_native_published_audit(source_context, scope, native_reader, deadline=deadline)
            raw["published_source_audit_artifact"] = write_json(
                root,
                directory / "published-source-audit.json",
                published.to_dict(),
            )
            config = PipelineConfig(
                scope,
                root,
                clean=False,
                skip_infra=True,
                mode="core",
                run_timeout_seconds=specification["timeout_seconds"],
            )
            plan = compile_execution_plan(config)
            require_canonical_native_stages(plan)
            reader.read(plan.provenance)
            executor = PipelineExecutor(config)
            results = executor.execute_plan(plan, deadline_monotonic=deadline)
            outcome = executor.run_result(results)
            raw["pipeline"] = {
                "mode": "core",
                "run_id": executor.run_id,
                "selection": {"skip_clean": True, "skip_infra": True},
                "plan": plan.to_dict(),
                "plan_digest": plan.digest,
                "expected_stage_keys": list(plan.expected_stage_keys),
                "outcomes": [item.to_dict() for item in outcome.outcomes],
                "source_content_identity": source_content_fingerprint(
                    root, config.project_dir, definition_path=root / plan.provenance
                ),
            }
            raw["execution_exit_code"] = outcome.exit_code
            if (
                not outcome.complete
                or outcome.exit_code
                or any(item.status.value != "succeeded" for item in outcome.outcomes)
            ):
                raw["status"] = "blocked" if outcome.exit_code == 75 else "fail"
                if raw["status"] == "blocked":
                    raw["blockers"].append(
                        {
                            "tool": "core execution contract",
                            "reason": "native core execution paused or was blocked",
                        }
                    )
                raise ValueError("fresh source-owned core execution did not complete")
            if not validate_current_rendered_provenance(root, scope).valid:
                raise ValueError("fresh native outputs lack valid current rendered provenance")
            from infrastructure.reporting.native_format_scope_replay import observe_native_scope_evidence

            checked_domain = observe_native_scope_evidence(source_context, raw, specification, native_reader, env)
            raw["stage_children"] = list(producer.stage_children)
            boundary_reader = SnapshotReader(root, native_producer_operation=producer)
            raw["analysis_data_graph"] = observe_native_analysis_boundary_graph(
                source_context,
                scope,
                executor.run_id,
                plan.digest,
                boundary_reader,
                deadline=deadline,
            )
            raw["hydration_reconstruction"], pdf_body = observe_native_pdf_recomposition(
                source_context,
                scope,
                executor.run_id,
                plan.digest,
                boundary_reader,
                deadline=deadline,
            )
            contract = native_artifact_contract(root, scope, formats, native_reader)
            raw["contract_digest"] = contract_digest(contract)
            from infrastructure.reporting.native_office_scope_cohorts import observe_office_scope_cohorts

            office_children = observe_office_scope_cohorts(
                source_context,
                raw,
                specification,
                native_reader,
                mermaid_runtime,
                pdfium_runtime,
                office_font_files,
                env,
            )
            checked_observers, whole_pdf = observe_native_deliverables(
                root,
                directory,
                scope,
                contract,
                formats,
                native_reader,
                source_context,
                raw,
                env=env,
                deadline=deadline,
                run_id=run_id,
                mermaid_runtime=mermaid_runtime,
                office_font_files=office_font_files,
                decoded_pixel_budget=decoded_pixel_budget,
                pdfium_runtime=pdfium_runtime,
                specification=specification,
                pipeline_run_id=executor.run_id,
                plan_digest=plan.digest,
            )
            for kind in sorted({artifact.format for artifact in contract}):
                raw["negative_controls"].append(_parser_control(root, directory, run_id, kind, env, deadline))
            if any(artifact.format == "pdf" for artifact in contract):
                # Dict insertion order puts the positive actual baseline first.
                for name in PDF_CONTROL_CODES:
                    raw["pdf_negative_controls"].append(
                        _pdf_oracle_control(root, directory, run_id, name, env, deadline)
                    )
            selected_tools = specification.get("observer_tools", {})
            from infrastructure.reporting.native_projection_source_dispatch import projection_control_formats

            raw["observer_controls"] = observe_format_controls(
                root,
                directory,
                projection_control_formats(contract, formats),
                scope=scope,
                env=env,
                deadline=deadline,
                run_id=run_id,
                interpreter=Path(sys.executable),
                epubcheck_jar=Path(selected_tools["epubcheck_jar"]) if selected_tools.get("epubcheck_jar") else None,
                java_executable=Path(selected_tools["java_executable"])
                if selected_tools.get("java_executable")
                else None,
                frozen_epub_engine=root / selected_tools["frozen_epub_engine"]
                if selected_tools.get("frozen_epub_engine")
                else None,
            )
            from infrastructure.reporting.native_office_scientific_suite import (
                observe_selected_office_scientific_controls,
            )

            scientific = observe_selected_office_scientific_controls(
                root,
                directory,
                contract,
                scope=scope,
                interpreter=Path(sys.executable),
                env=env,
                deadline=deadline,
                run_id=run_id,
                observer_tools=selected_tools,
            )
            if scientific:
                raw["observer_controls"]["office_scientific"] = scientific
            if scope in PRINT_SCOPES:
                from infrastructure.reporting.native_print_artifact_controls import supervise_print_controls

                raw["observer_controls"]["print"] = supervise_print_controls(
                    root,
                    directory,
                    scope,
                    env=env,
                    deadline=deadline,
                    run_id=run_id,
                    interpreter=Path(sys.executable),
                )
            if scope == "templates/template_pitch_deck":
                from infrastructure.reporting.native_pitch_control_supervisor import supervise_pitch_controls

                raw["observer_controls"]["configured_pitch"] = supervise_pitch_controls(
                    root,
                    directory / "configured-pitch-controls",
                    formats=formats,
                    interpreter=Path(sys.executable),
                    env=env,
                    deadline=deadline,
                    run_id=run_id,
                )
            invalid_pdf = directory / "invented-invalid.pdf"
            invalid_pdf.write_bytes(b"invented public malformed PDF negative control\n")
            tool = native_tool_record(
                root,
                directory,
                "pdftoppm",
                [str(invalid_pdf), str(directory / "invalid-raster")],
                env=env,
                deadline=deadline,
                run_id=run_id,
                purpose="invalid-pdf-tool",
            )
            if tool["exit_code"] != 1 or tool["original_exit_code"] != 1:
                raise ValueError("actual PDF raster tool did not reject malformed native input with its required exit")
            raw["negative_controls"].append(
                {
                    "name": "invalid-pdf-tool",
                    "expected_exit_code": 1,
                    "observed_exit_code": 1,
                    "artifact": tool["artifact"],
                }
            )
            audit = build_current_publication_audit(source_context, scope, native_reader, deadline=deadline)
            audit_payload = json.loads(format_publication_audit_json(audit))
            raw["publication_audit_artifact"] = write_json(root, directory / "publication-audit.json", audit_payload)
            if validate_publication_audit(audit, strict=True) != 0 or not native_reader.unchanged():
                raise ValueError("fresh strict rendered publication audit or artifact custody failed")
            verify_runtime_execution(root / "projects" / scope)
            raw["deliverables_identity_after"] = deliverable_identity(root, scope)
            from infrastructure.reporting.native_oracle_phase_original import collect_original_native_oracle_phase

            oracle_phases.append(
                collect_original_native_oracle_phase(
                    source_context,
                    raw,
                    native_reader,
                    outcome,
                    checked_domain,
                    checked_observers,
                    office_children,
                    pdf_body,
                    formats,
                    deadline=deadline,
                    whole_pdf=whole_pdf,
                    env=env,
                )
            )
            # Final residual projection occurs after the outer runtime/provider
            # and genuine Source owner closing checks, never before them.
            raw["status"], raw["execution_exit_code"] = "pass", 0
    except NativeToolUnavailable as error:
        raw["status"], raw["execution_exit_code"] = "blocked", 75
        raw["blockers"].append({"tool": "native installed tool", "reason": str(error)})
    except TimeoutError as error:
        raw["status"], raw["execution_exit_code"], raw["diagnostic"] = (
            "fail",
            124,
            str(error),
        )
    except Exception as error:  # noqa: BLE001 - every unexpected observer failure remains failed
        raw["diagnostic"] = str(error)
        if raw["status"] != "blocked":
            raw["status"] = "fail"
            raw["execution_exit_code"] = raw["execution_exit_code"] or 1
    close_native_worker_custody(
        raw,
        root=root,
        before=before,
        formats=formats,
        directory=directory,
        specification=specification,
        source_context=source_context,
        native_reader=native_reader,
        runtime=runtime,
        deadline=deadline,
        host_before=host_before,
        interpreter_before=interpreter_before,
    )
    return raw


def run_native_worker(
    root: Path,
    specification: dict[str, Any],
    *,
    source_context: NativeSourceContext,
    mermaid_selection: NativeMermaidSelection,
    pdfium_provider: NativePDFiumProvider,
    office_font_files: tuple[Path, ...],
    decoded_pixel_budget: SourceImageDecodeBudget | None = None,
) -> dict[str, Any]:
    """Keep actual worker outcomes through the existing owners' closing checks."""
    from infrastructure.reporting.native_format_scope_replay import run_native_scope_worker

    return run_native_scope_worker(
        root,
        specification,
        source_context=source_context,
        mermaid_selection=mermaid_selection,
        pdfium_provider=pdfium_provider,
        office_font_files=office_font_files,
        decoded_pixel_budget=decoded_pixel_budget,
    )


def main(argv: list[str] | None = None) -> int:
    """Internal supervised worker; public CLI owns selection and final bindings."""
    _native_startup_phase("worker-main-enter")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--spec-sha256")
    parser.add_argument("--source-descriptor", type=Path)
    parser.add_argument("--source-descriptor-sha256")
    parser.add_argument("--implementation-input", type=Path)
    parser.add_argument("--implementation-sha256")
    parser.add_argument("--audit-closure-directory", type=Path)
    parser.add_argument("--audit-closure-identity", nargs=2, type=int)
    parser.add_argument("--current-root-identity", nargs=2, type=int)
    parser.add_argument("--mermaid-package-root", type=Path)
    parser.add_argument("--mermaid-dependency-root", type=Path)
    parser.add_argument("--mermaid-node-executable", type=Path)
    parser.add_argument("--mermaid-chrome-executable", type=Path)
    parser.add_argument("--mermaid-runtime-digest")
    parser.add_argument("--control", choices=("pdf", "html", "docx", "epub", "pptx", "png"))
    parser.add_argument(
        "--control-suite",
        action="store_true",
        help="Internal actual nested parser-control transport check",
    )
    parser.add_argument("--run-id")
    parser.add_argument("--control-output", type=Path)
    parser.add_argument("--pdf-oracle-control", choices=tuple(PDF_CONTROL_CODES))
    parser.add_argument("--deadline-monotonic", type=float)
    parser.add_argument("--pdfium-site", type=Path)
    parser.add_argument("--pdfium-wheel", type=Path)
    parser.add_argument("--pdfium-wheel-sha256")
    parser.add_argument("--pdfium-input-sha256")
    parser.add_argument("--office-font-file", action="append", type=Path, default=[])
    parser.add_argument("--office-fonts-sha256")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.pdf_oracle_control:
        if (
            args.spec
            or args.control
            or args.control_suite
            or args.control_output is None
            or not args.run_id
            or args.deadline_monotonic is None
        ):
            parser.error("valid-PDF control requires only its exact admitted output/run/deadline")
        output = SnapshotReader(root).public_path(args.control_output.relative_to(root).as_posix())
        return run_pdf_oracle_control(root, output, args.pdf_oracle_control, args.run_id, args.deadline_monotonic)
    if args.deadline_monotonic is not None:
        parser.error("control deadline requires a valid-PDF control")
    if args.control_suite:
        if args.spec or args.control or args.control_output is None or not args.run_id:
            parser.error("control suite requires only its admitted directory and run identity")
        directory = evidence_directory(root, args.control_output)
        env = native_environment(root, Path(sys.executable), directory)
        deadline = time.monotonic() + 120
        controls = [
            _parser_control(root, directory, args.run_id, kind, env, deadline)
            for kind in ("pdf", "html", "docx", "epub", "pptx", "png")
        ]
        write_json(
            root,
            directory / "parser-controls.json",
            {"run_id": args.run_id, "controls": controls},
        )
        return 0
    if args.control:
        code = 0
        try:
            parse_native_bytes(args.control, b"invented public malformed native artifact")
        except Exception:  # noqa: BLE001 - negative control records actual parser refusal
            code = 1
        if args.control_output is None or not args.run_id:
            parser.error("negative control requires its admitted output and run identity")
        write_json(
            root,
            args.control_output,
            {
                "schema_version": CONTROL_SCHEMA,
                "run_id": args.run_id,
                "name": f"invalid-native-{args.control}",
                "format": args.control,
                "exit_code": code,
            },
        )
        return code
    if args.spec is None:
        parser.error("native worker requires an admitted specification")
    pins = (
        args.spec_sha256,
        args.source_descriptor,
        args.source_descriptor_sha256,
        args.implementation_input,
        args.implementation_sha256,
        args.audit_closure_directory,
        args.audit_closure_identity,
        args.current_root_identity,
        args.mermaid_package_root,
        args.mermaid_dependency_root,
        args.mermaid_node_executable,
        args.mermaid_chrome_executable,
        args.mermaid_runtime_digest,
        args.pdfium_site,
        args.pdfium_wheel,
        args.pdfium_wheel_sha256,
        args.pdfium_input_sha256,
        args.office_fonts_sha256,
    )
    if any(value is None for value in pins):
        parser.error("native worker requires all original command-bound source/SDK/spec/closure pins")
    input_reader = SnapshotReader(root)
    spec_snapshot = input_reader.read(args.spec.relative_to(root).as_posix())
    if spec_snapshot.sha256 != args.spec_sha256:
        raise ValueError("native specification changed from original command pin")
    specification = spec_snapshot.json_object()
    validate_native_specification(specification)
    inputs = specification["source_inputs"]
    mermaid_selection = NativeMermaidSelection(
        args.mermaid_package_root,
        args.mermaid_dependency_root,
        args.mermaid_node_executable,
        args.mermaid_chrome_executable,
    )
    expected_runtime = {
        **mermaid_selection.spec_data(),
        "runtime_content_digest": args.mermaid_runtime_digest,
    }
    if inputs["mermaid_runtime"] != expected_runtime:
        raise ValueError("native Source11 spec differs from all original command-pinned runtime nominations")
    descriptor = bound_input(input_reader, inputs["descriptor"])
    implementation = bound_input(input_reader, inputs["implementation"])
    if (
        descriptor.path != args.source_descriptor
        or descriptor.sha256 != args.source_descriptor_sha256
        or implementation.path != args.implementation_input
        or implementation.sha256 != args.implementation_sha256
    ):
        raise ValueError("native source/SDK input differs from original command pins")
    closure = root / inputs["closure"]["directory"]
    metadata = closure.lstat()
    current_metadata = root.lstat()
    if (
        closure != args.audit_closure_directory
        or list((metadata.st_dev, metadata.st_ino)) != args.audit_closure_identity
        or inputs["closure"]["identity"] != args.audit_closure_identity
        or list((current_metadata.st_dev, current_metadata.st_ino)) != args.current_root_identity
    ):
        raise ValueError("native current root/closure differs from original actual physical bindings")
    import infrastructure

    if infrastructure.__file__ is None:
        raise ValueError("native selected SDK origin is unavailable")
    _native_startup_phase("source-admission-begin")
    source_context = admit_native_source_operation(
        root,
        NativeSDKSelection(Path(infrastructure.__file__).absolute().parent, implementation.content),
        run_id=specification["run_id"],
        deadline=specification["deadline_monotonic"],
        environment=os.environ,
    )
    _native_startup_phase("source-admission-returned")
    from infrastructure.reporting.native_source_external_admission import (
        validate_original_source_descriptor,
    )

    observation = validate_original_source_descriptor(
        descriptor.content,
        externally_bound_sha256=args.source_descriptor_sha256,
        run_id=specification["run_id"],
        scope=specification["scope"],
        deadline=specification["deadline_monotonic"],
    )
    reference = source_context.reference
    if (
        observation["original_source"]["root"] != str(reference.root)
        or observation["original_source"]["commit"] != reference.commit
        or observation["original_source"]["source_identity"] != reference.source_identity
        or observation["current_mirror"]["root"] != str(root)
        or observation["current_mirror"]["root_identity"] != args.current_root_identity
        or observation["selected_sdk"]["package_root"] != str(source_context.bindings.selected_sdk_package_root)
        or observation["selected_sdk"]["implementation_sha256"] != implementation.sha256
    ):
        raise ValueError("native worker source/SDK re-admission differs from original observations")
    wheels = {
        scope: input_reader.public_path(provider["wheel_artifact"]["path"])
        for scope, provider in inputs["providers"].items()
    }
    providers, roots = admitted_native_providers(
        source_context,
        specification["scope"],
        wheels,
        Path(sys.executable),
        deadline=specification["deadline_monotonic"],
    )
    pdfium_provider = readmit_full_worker_pdfium_provider(
        NativePDFiumSelection(args.pdfium_site, args.pdfium_wheel),
        source_context,
        inputs["pdfium"],
        scope=specification["scope"],
        wheel_sha256=args.pdfium_wheel_sha256,
        input_sha256=args.pdfium_input_sha256,
        deadline=specification["deadline_monotonic"],
    )
    roots = (*roots, *pdfium_provider.audit_roots)
    if providers != inputs["providers"] or list(map(str, roots)) != inputs["provider_roots"]:
        raise ValueError("native installed provider admission differs from original launch selection")
    source_context.verify_correspondence(reference, root, input_reader, specification["deadline_monotonic"])
    office_font_files = tuple(args.office_font_file)
    verify_office_font_nominations(
        inputs["office_fonts"],
        office_font_files,
        deadline=specification["deadline_monotonic"],
        digest=args.office_fonts_sha256,
    )
    _native_startup_phase("worker-execution-begin")
    raw = run_native_worker(
        root,
        specification,
        source_context=source_context,
        mermaid_selection=mermaid_selection,
        pdfium_provider=pdfium_provider,
        office_font_files=office_font_files,
    )
    write_json(root, root / specification["directory"] / "native-execution.json", raw)
    code = raw["execution_exit_code"]
    if type(code) is not int:
        raise ValueError("native worker outcome is not a typed exit code")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
