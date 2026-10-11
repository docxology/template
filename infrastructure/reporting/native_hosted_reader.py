"""Cold installed Source reader with actual authenticated original custody."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
import uuid
from typing import Any, cast
from pathlib import Path

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.public_hosted_origin import HostedReadbackContext, collect_hosted_origin
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_authenticated_original_launch import admit_authenticated_native_originals
from infrastructure.reporting.native_format_current_orchestration import (
    _prepare_current_root,
    preserve_current_attempts,
    validate_current_destination,
)
from infrastructure.reporting.native_current_reader_inputs import NativeCurrentAnalysisInputs
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
    validate_native_specification,
)
from infrastructure.reporting.native_format_joint_source import (
    NativeReaderOperation,
    NativeSDKSelection,
    admitted_native_providers,
    admit_native_source_operation,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    MAX_SOURCE_IMAGE_OCCURRENCES,
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumSelection, admit_full_worker_pdfium_provider
from infrastructure.reporting.native_hosted_original_custody import collect_native_hosted_originals
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidSelection,
)
from infrastructure.reporting.native_office_diagram_runtime import admit_pdfium_runtime
from infrastructure.reporting.native_office_full_worker_context import NativeOfficeReaderSelection
from infrastructure.reporting.required_acceptance_aggregate import produce_aggregate
from infrastructure.reporting.required_candidate_transport import RequiredCandidatePackingInputs
from infrastructure.reporting.required_candidate_collection import collect_required_candidate
from infrastructure.publishing.release_acceptance import RECEIPT_PATH, validate_candidate_handoff
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _assignments(values: list[str], *, pair: bool) -> dict[object, str]:
    rows: dict[object, str] = {}
    for value in values:
        owner, separator, path = value.partition("=")
        key: object = tuple(owner.split("/")) if pair else owner
        if not separator or not path or key in rows or (pair and len(owner.split("/")) != 2):
            raise ValueError("reader input must name one unique externally selected owner=path")
        rows[key] = path
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--current-analysis-root", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--sdk-package-root", type=Path, required=True)
    parser.add_argument("--implementation-input", type=Path, required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--provider-wheel", action="append", default=[])
    parser.add_argument("--pdfium-site", type=Path, required=True)
    parser.add_argument("--pdfium-wheel", type=Path, required=True)
    parser.add_argument("--office-font-file", action="append", default=[], type=Path)
    parser.add_argument("--epubcheck-jar", type=Path)
    parser.add_argument("--java-executable", type=Path)
    parser.add_argument("--mermaid-package-root", type=Path, required=True)
    parser.add_argument("--mermaid-dependency-root", type=Path, required=True)
    parser.add_argument("--mermaid-node-executable", type=Path, required=True)
    parser.add_argument("--mermaid-chrome-executable", type=Path, required=True)
    parser.add_argument("--operation-started-monotonic", type=float, required=True)
    parser.add_argument("--timeout", type=int, required=True)
    parser.add_argument("--receipt", action="append", default=[])
    parser.add_argument("--root-receipt", action="append", default=[])
    parser.add_argument("--auxiliary-receipt", action="append", default=[])
    parser.add_argument("--stage-bundle", action="store_true")
    parser.add_argument("--acceptance-artifact-id", type=int)
    parser.add_argument("--acceptance-receipt-sha256")
    args = parser.parse_args(argv)
    if not 0 < args.timeout <= 14400 or not 0 < args.operation_started_monotonic < time.monotonic():
        parser.error("reader requires its actual already-started outer Source clock")
    if bool(args.epubcheck_jar) != bool(args.java_executable):
        parser.error("Current native observers require paired caller EPUBCheck/Java nominees")
    for nominee in (args.epubcheck_jar, args.java_executable):
        if nominee is not None and (not nominee.is_absolute() or nominee.is_symlink() or not nominee.is_file()):
            parser.error("Current native observer nominees require physical absolute input files")
    deadline = args.operation_started_monotonic + args.timeout
    root = args.repo_root.resolve(strict=True)
    run = uuid.uuid4().hex
    attempts: dict[str, Any] = {
        "deadline": deadline,
        "current_processes": [],
        "current_failures": [],
        "current_domain_failures": [],
    }
    try:
        remaining(deadline)
        raw = read_bytes_confined(args.implementation_input.parent, args.implementation_input, max_bytes=64 * 1024**2)
        if hashlib.sha256(raw).hexdigest() != args.implementation_sha256:
            raise ValueError("reader selected SDK input differs from its actual parent-held digest")
        sdk = NativeSDKSelection(args.sdk_package_root, raw)
        source = admit_native_source_operation(root, sdk, run_id=run, deadline=deadline, environment=os.environ)
        validate_current_destination(source, args.current_analysis_root)
        if source.reference.commit != args.revision:
            raise ValueError("reader Source differs from the externally selected hosted revision")
        provider_paths = _assignments(args.provider_wheel, pair=False)
        if set(provider_paths) != set(PUBLIC_PROJECT_NAMES):
            raise ValueError("cold reader needs every Source-owned public provider nomination")
        wheels = {str(scope): Path(path) for scope, path in provider_paths.items()}
        # Admit all installed project providers and both PDFium namespaces before
        # any current payload. Receipt paths never select import providers.
        provider_bindings = {}
        for scope in PUBLIC_PROJECT_NAMES:
            provider_bindings[scope], _ = admitted_native_providers(
                source, scope, wheels, Path(sys.executable), deadline=deadline
            )
        selection = NativePDFiumSelection(args.pdfium_site, args.pdfium_wheel)
        providers = {
            scope: admit_full_worker_pdfium_provider(selection, source, scope=scope, deadline=deadline)
            for scope in PUBLIC_PROJECT_NAMES
        }
        runtimes = {
            scope: admit_pdfium_runtime(
                source, scope=scope, site=selection.site, wheel=selection.wheel, deadline=deadline
            )
            for scope in PUBLIC_PROJECT_NAMES
        }
        mermaid = NativeMermaidSelection(
            args.mermaid_package_root,
            args.mermaid_dependency_root,
            args.mermaid_node_executable,
            args.mermaid_chrome_executable,
        )
        fonts = NativeOfficeReaderSelection(mermaid, tuple(args.office_font_file))
        custodian = collect_native_hosted_originals(
            source,
            root / "output/readiness/native-hosted-origin",
            repository=args.repository,
            run_id=args.run_id,
            head_sha=args.revision,
            deadline=deadline,
        )
        originals = admit_authenticated_native_originals(
            custodian, source, current_pdfium_providers=providers, deadline=deadline
        )
        preparation_directory = root / "output/readiness" / f"native-current-preparation-{run}"
        create_private_native_directory(root, preparation_directory)
        attempts.update({"directory": preparation_directory, "original_provider_bindings": provider_bindings})
        current_source, current_wheels = _prepare_current_root(
            source, sdk, args.current_analysis_root, attempts, wheels
        )
        # Admit every Current scope before its first Core or reader import.
        current_providers = {
            scope: admit_full_worker_pdfium_provider(selection, current_source, scope=scope, deadline=deadline)
            for scope in originals
        }
        current_runtimes = {
            scope: admit_pdfium_runtime(
                current_source, scope=scope, site=selection.site, wheel=selection.wheel, deadline=deadline
            )
            for scope in originals
        }
        original_operation = NativeReaderOperation(source, deadline, originals, providers, fonts, runtimes)
        original_reader = SnapshotReader(root, native_operation=original_operation)
        from infrastructure.reporting.release_readiness_profile import required_profile
        from infrastructure.reporting.readiness_receipts import source_fingerprint
        from infrastructure.reporting.native_current_epub_engine_data import prepare_current_epub_observer_tools

        profile, faults = required_profile(root, original_reader, source_fingerprint(root))
        if faults:
            raise ValueError("Current observer preparation lacks the complete admitted Source profile")
        epub_scopes = [row.scope for row in profile if row.kind == "formats" and "epub" in row.formats]
        if epub_scopes:
            completed_epub = [scope for scope in epub_scopes if scope in originals]
            if not completed_epub:
                raise ValueError("Current shared EPUB input preparation lacks a genuinely completed selected Original")
            current_tools = prepare_current_epub_observer_tools(
                completed_epub[0],
                original_reader,
                current_source,
                epubcheck_jar=args.epubcheck_jar,
                java_executable=args.java_executable,
            )
        else:
            # This is whole Source-selection absence, never a missing receipt
            # promoted to an engine or native completion.
            original = next(iter(originals.values()))
            specification_file = original_reader.read(original.specification_relative)
            if specification_file.sha256 != original.specification_sha256:
                raise ValueError("unused Current observer selection changed its held Original specification")
            specification = specification_file.json_object()
            validate_native_specification(specification)
            tools = specification.get(
                "observer_tools", dict.fromkeys(("epubcheck_jar", "java_executable", "frozen_epub_engine"))
            )
            if (
                specification["run_id"] != original.run_id
                or tools["epubcheck_jar"] != (None if args.epubcheck_jar is None else str(args.epubcheck_jar))
                or tools["java_executable"] != (None if args.java_executable is None else str(args.java_executable))
            ):
                raise ValueError("unused Current observer nominees differ from the caller's actual Source selection")
            label = tools["frozen_epub_engine"]
            current_tools = {
                "epubcheck_jar": args.epubcheck_jar,
                "java_executable": args.java_executable,
                "frozen_epub_engine": None if label is None else current_source.bindings.current_root / label,
            }
        current_directories = {}
        for scope in originals:
            directory = (
                current_source.bindings.current_root
                / "output/readiness"
                / f"native-current-{current_source.bindings.run_id}"
                / scope
            )
            create_private_native_directory(current_source.bindings.current_root, directory)
            current_directories[scope] = directory
        current_inputs = NativeCurrentAnalysisInputs(
            current_source,
            deadline,
            current_directories,
            current_wheels,
            pdfium_providers=current_providers,
            pdfium_runtimes=current_runtimes,
            office_font_files=fonts.font_files,
            observer_tools=current_tools,
            failure_observations=attempts["current_failures"],
            domain_failure_observations=attempts["current_domain_failures"],
        )
        operation = NativeReaderOperation(
            source,
            deadline,
            originals,
            providers,
            fonts,
            runtimes,
            SourceImageDecodeBudget(MAX_SOURCE_IMAGE_OCCURRENCES),
            current_analysis=current_inputs,
        )
        operation.verify(SnapshotReader(root))
        handoff = args.acceptance_artifact_id is not None or args.acceptance_receipt_sha256 is not None
        if handoff:
            if args.acceptance_artifact_id is None or args.acceptance_receipt_sha256 is None or args.stage_bundle:
                raise ValueError(
                    "installed handoff needs exact artifact/receipt identities and cannot republish candidate transport"
                )
            binding = collect_required_candidate(
                source,
                custodian,
                directory=root / "output/readiness/candidate-hosted-origin",
                repository=args.repository,
                run_id=args.run_id,
                artifact_id=args.acceptance_artifact_id,
                receipt_sha256=args.acceptance_receipt_sha256,
                deadline=deadline,
            )
            held = SnapshotReader(root).read(RECEIPT_PATH)
            if held.sha256 != binding["sha256"] or held.json_object().get("source_commit") != args.revision:
                raise ValueError("installed handoff receipt differs from the exact authentic producer identity")
            root_origin = held.json_object().get("hosted_origin_artifact")
            if not isinstance(root_origin, dict) or set(root_origin) != {"path", "sha256"}:
                raise ValueError("hosted handoff lacks its original bound six-Root manifest")
        else:
            root_origin = collect_hosted_origin(
                root,
                root / "output/readiness/hosted-origin",
                repository=args.repository,
                run_id=args.run_id,
                head_sha=args.revision,
                timeout=600,
                operation_deadline=deadline,
            )
        context = HostedReadbackContext(root_origin, args.repository, args.run_id, args.revision)
        receipts = [*args.receipt, custodian.native_receipt_binding()["path"]]
        if len(set(receipts)) != len(receipts):
            raise ValueError("reader refuses duplicate native/common original receipt ownership")
        # Current and per-format Office owners are opened serially by the
        # existing complete validator, never inside a hosted-wide producer.
        if handoff:
            state = validate_candidate_handoff(
                root,
                revision=args.revision,
                receipt_sha256=args.acceptance_receipt_sha256,
                repository=args.repository,
                run_id=str(args.run_id),
                artifact_id=str(args.acceptance_artifact_id),
                run_metadata=root / "output/readiness/candidate-hosted-origin/run-response.json",
                artifact_metadata=root / "output/readiness/candidate-hosted-origin/primary-metadata-response.json",
                native_operation=operation,
                hosted_origin=context,
            )
            sys.stdout.write("required candidate acceptance: " + state + "\n")
            return cast(
                int,
                preserve_current_attempts(
                    {"exit_code": {"pass": 0, "fail": 1, "blocked": 75, "unknown": 2}[state]}, attempts
                )["exit_code"],
            )
        roots = _assignments(args.root_receipt, pair=True)
        auxiliary = _assignments(args.auxiliary_receipt, pair=False)
        packing = (
            RequiredCandidatePackingInputs(
                custodian, root / "output/readiness/candidate-transport", args.repository, args.run_id, deadline
            )
            if args.stage_bundle
            else None
        )
        result = produce_aggregate(
            root,
            receipts,
            revision=args.revision,
            root_receipts={key: value for key, value in roots.items() if isinstance(key, tuple)},
            auxiliary_receipts={str(key): value for key, value in auxiliary.items()},
            hosted_origin=context,
            native_operation=operation,
            candidate_packing=packing,
        )
        result = preserve_current_attempts(result, attempts)
        sys.stdout.write("required candidate acceptance: " + result["candidate_state"] + "\n")
        if "candidate_transport" in result:
            sys.stdout.write("receipt_sha256=" + result["candidate_transport"]["receipt_sha256"] + "\n")
        return int(result["exit_code"])
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        packet = getattr(error, "native_current_pipeline", None)
        if isinstance(packet, dict):
            attempts["current_failures"].append(packet)
        domain_attempt = getattr(error, "native_project_domain_attempt", None)
        if isinstance(domain_attempt, dict):
            attempts["current_domain_failures"].append(
                {
                    "attempt": domain_attempt,
                    "controller_exit_code": getattr(
                        error, "native_project_domain_exit_code", getattr(error, "code", None)
                    ),
                }
            )
        sys.stdout.write("authenticated installed reader refused: " + str(error) + "\n")
        return int(preserve_current_attempts({"exit_code": 2}, attempts)["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
