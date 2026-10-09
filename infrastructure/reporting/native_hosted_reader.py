"""Cold installed Source reader with actual authenticated original custody."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
import uuid
from pathlib import Path

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.public_hosted_origin import HostedReadbackContext, collect_hosted_origin
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_authenticated_original_launch import admit_authenticated_native_originals
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
    admit_source_mermaid_selection,
    source_mermaid_runtime_operation,
)
from infrastructure.reporting.native_office_diagram_runtime import admit_pdfium_runtime
from infrastructure.reporting.native_office_full_worker_context import NativeOfficeReaderSelection
from infrastructure.reporting.native_tool_producer import native_producer_operation
from infrastructure.reporting.required_acceptance_aggregate import produce_aggregate
from infrastructure.reporting.required_candidate_transport import pack_required_candidate
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
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--sdk-package-root", type=Path, required=True)
    parser.add_argument("--implementation-input", type=Path, required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--provider-wheel", action="append", default=[])
    parser.add_argument("--pdfium-site", type=Path, required=True)
    parser.add_argument("--pdfium-wheel", type=Path, required=True)
    parser.add_argument("--office-font-file", action="append", default=[], type=Path)
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
    deadline = args.operation_started_monotonic + args.timeout
    root = args.repo_root.resolve(strict=True)
    run = uuid.uuid4().hex
    try:
        remaining(deadline)
        raw = read_bytes_confined(args.implementation_input.parent, args.implementation_input, max_bytes=64 * 1024**2)
        if hashlib.sha256(raw).hexdigest() != args.implementation_sha256:
            raise ValueError("reader selected SDK input differs from its actual parent-held digest")
        sdk = NativeSDKSelection(args.sdk_package_root, raw)
        source = admit_native_source_operation(root, sdk, run_id=run, deadline=deadline, environment=os.environ)
        if source.reference.commit != args.revision:
            raise ValueError("reader Source differs from the externally selected hosted revision")
        provider_paths = _assignments(args.provider_wheel, pair=False)
        if set(provider_paths) != set(PUBLIC_PROJECT_NAMES):
            raise ValueError("cold reader needs every Source-owned public provider nomination")
        wheels = {str(scope): Path(path) for scope, path in provider_paths.items()}
        # Admit all installed project providers and both PDFium namespaces before
        # any current payload. Receipt paths never select import providers.
        for scope in PUBLIC_PROJECT_NAMES:
            admitted_native_providers(source, scope, wheels, Path(sys.executable), deadline=deadline)
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
        operation = NativeReaderOperation(
            source,
            deadline,
            originals,
            providers,
            fonts,
            runtimes,
            SourceImageDecodeBudget(MAX_SOURCE_IMAGE_OCCURRENCES),
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
        with native_producer_operation(source, run_id=run, deadline=deadline):
            mermaid_directory = root / "output/readiness/current-reader-mermaid"
            mermaid_directory.mkdir(parents=True, mode=0o700)
            runtime = admit_source_mermaid_selection(
                mermaid, source, deadline=deadline, directory=mermaid_directory, env=dict(os.environ)
            )
            with source_mermaid_runtime_operation(runtime, source=source, deadline=deadline):
                if handoff:
                    state = validate_candidate_handoff(
                        root,
                        revision=args.revision,
                        receipt_sha256=args.acceptance_receipt_sha256,
                        repository=args.repository,
                        run_id=str(args.run_id),
                        artifact_id=str(args.acceptance_artifact_id),
                        run_metadata=root / "output/readiness/candidate-hosted-origin/run-response.json",
                        artifact_metadata=root
                        / "output/readiness/candidate-hosted-origin/primary-metadata-response.json",
                        native_operation=operation,
                        hosted_origin=context,
                    )
                    print("required candidate acceptance: " + state)
                    return {"pass": 0, "fail": 1, "blocked": 75, "unknown": 2}[state]
                roots = _assignments(args.root_receipt, pair=True)
                auxiliary = _assignments(args.auxiliary_receipt, pair=False)
                result = produce_aggregate(
                    root,
                    receipts,
                    revision=args.revision,
                    root_receipts={key: value for key, value in roots.items() if isinstance(key, tuple)},
                    auxiliary_receipts={str(key): value for key, value in auxiliary.items()},
                    hosted_origin=context,
                    native_operation=operation,
                )
                print("required candidate acceptance: " + result["candidate_state"])
                if result["exit_code"] == 0 and args.stage_bundle:
                    bundle = pack_required_candidate(
                        source,
                        operation,
                        native_custodian=custodian,
                        hosted_origin=context,
                        directory=root / "output/readiness/candidate-transport",
                        repository=args.repository,
                        run_id=args.run_id,
                        deadline=deadline,
                    )
                    print("receipt_sha256=" + bundle["receipt_sha256"])
                return int(result["exit_code"])
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        print("authenticated installed reader refused: " + str(error))
        return 124 if time.monotonic() >= deadline else 2


if __name__ == "__main__":
    raise SystemExit(main())
