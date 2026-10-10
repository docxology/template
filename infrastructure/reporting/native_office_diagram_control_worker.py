"""One actual Source-owned Office child, invoked only by its original supervisor."""

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import (
    NativeArtifact,
    native_artifact_contract,
    native_deadline_guard,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    MAX_SOURCE_IMAGE_OCCURRENCES,
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_office_control_custody import SCHEMA
from infrastructure.reporting.native_office_control_supervisor import KINDS
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_office_diagram_controls import (
    CONTROL_CODES,
    run_office_diagram_control,
)
from infrastructure.reporting.native_office_diagram_positive import (
    build_office_diagram_native_positive,
)
from infrastructure.reporting.native_office_diagram_runtime import admit_pdfium_runtime
from infrastructure.reporting.native_office_diagram_source import (
    prepare_office_diagram_source,
)
from infrastructure.reporting.native_office_full_observer import (
    observe_office_full_source,
)
from infrastructure.reporting.native_source_external_admission import (
    admit_explicitly_bound_native_source,
)
from infrastructure.reporting.native_tool_producer import native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _path(value: Any) -> Path | None:
    return None if value is None else Path(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--specification", required=True)
    parser.add_argument("--specification-sha256", required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    for nomination in ("mermaid-package-root", "mermaid-dependency-root", "mermaid-node", "mermaid-chrome"):
        parser.add_argument("--" + nomination, type=Path)
    args = parser.parse_args()
    with native_deadline_guard(args.deadline):
        remaining(args.deadline)
        root = args.root.absolute()
        reader = SnapshotReader(root)
        spec = reader.read(args.specification)
        if spec.sha256 != args.specification_sha256:
            raise ValueError("Office child differs from parent's exact prelaunch Source/control bytes")
        value = spec.json_object()
        if (
            value["schema_version"] != SCHEMA
            or value["run_id"] != args.run_id
            or value["original_deadline_monotonic"] != args.deadline
        ):
            raise ValueError("Office child Source/control role/run/original clock differs")
        scope, kind, control = value["scope"], value["kind"], value["control"]
        if (
            scope not in PUBLIC_PROJECT_NAMES
            or kind not in KINDS
            or control not in ("office-cell", "diagram-census", "baseline", *CONTROL_CODES)
        ):
            raise ValueError("Office child role is outside the literal public Source artifact/control contract")
        if (control in ("baseline", *CONTROL_CODES)) != isinstance(value.get("target"), dict):
            raise ValueError("Office child target nomination differs from its fixed Source role")
        implementation = reader.read(value["implementation"]["path"])
        if (
            implementation.sha256 != args.implementation_sha256
            or implementation.sha256 != value["implementation"]["sha256"]
        ):
            raise ValueError("Office child selected implementation differs from actual supervisor nomination")
        import infrastructure

        if infrastructure.__file__ is None:
            raise ValueError("Office actual installed SDK origin is unavailable")
        selected = Path(infrastructure.__file__).absolute().parent
        observed = root.stat()
        context = admit_explicitly_bound_native_source(
            root,
            environment=dict(os.environ),
            current_root_identity=(observed.st_dev, observed.st_ino),
            selected_sdk_package_root=selected,
            expected_implementation_bytes=implementation.content,
            run_id=args.run_id,
            deadline=args.deadline,
            fresh_pycache_prefix=Path(sys.pycache_prefix) if sys.pycache_prefix else None,
        )
        if context is None or json.loads(context.descriptor(scope, deadline=args.deadline)) != value["source"]:
            raise ValueError("Office child actual Source correspondence differs from parent's prelaunch admission")
        directory = root / value["directory"]
        if spec.path != directory / "specification.json":
            raise ValueError("Office child directory differs from parent's exact Source-owned spec path")
        dependencies = value["dependencies"]
        runtime = admit_pdfium_runtime(
            context,
            scope=scope,
            site=Path(dependencies["pdfium_site"]),
            wheel=Path(dependencies["pdfium_wheel"]),
            deadline=args.deadline,
        )
        if runtime.wheel_observation["sha256"] != value["pdfium_wheel_sha256"]:
            raise ValueError("Office child actual selected PDFium differs from parent's Source-locked platform wheel")
        # One existing finite source decoder budget for every held decoded copy
        # in this original child. It is never replaced after source production.
        budget = SourceImageDecodeBudget(MAX_SOURCE_IMAGE_OCCURRENCES)
        with (
            native_producer_operation(context, run_id=args.run_id, deadline=args.deadline) as owner,
            ExitStack() as runtime_scope,
        ):
            reader = SnapshotReader(root, native_producer_operation=owner)
            contracts = native_artifact_contract(root, scope, (kind,), reader)
            artifact = NativeArtifact(**value["artifact"])
            if artifact not in contracts or artifact.id != f"manuscript:{kind}":
                raise ValueError("Office child artifact is not the exact current Source-declared manuscript")
            mermaid_runtime = None
            if value["mermaid_selection"] is not None:
                from infrastructure.reporting.native_mermaid_runtime_selection import (
                    NativeMermaidSelection,
                    readmit_source_mermaid_selection,
                    source_mermaid_runtime_operation,
                )

                nominations = (
                    args.mermaid_package_root,
                    args.mermaid_dependency_root,
                    args.mermaid_node,
                    args.mermaid_chrome,
                )
                if any(not isinstance(item, Path) for item in nominations):
                    raise ValueError("Office Source11 requires independently command-pinned actual runtime nominations")
                selection = NativeMermaidSelection(*nominations)
                mermaid_runtime = readmit_source_mermaid_selection(
                    value["mermaid_selection"],
                    selection,
                    context,
                    deadline=args.deadline,
                    directory=directory / "source-mermaid-runtime",
                    env=dict(os.environ),
                )
                runtime_scope.enter_context(
                    source_mermaid_runtime_operation(mermaid_runtime, source=context, deadline=args.deadline)
                )
            elif any(
                item is not None
                for item in (
                    args.mermaid_package_root,
                    args.mermaid_dependency_root,
                    args.mermaid_node,
                    args.mermaid_chrome,
                )
            ):
                raise ValueError("Office child has undeclared Source11 command nominations")
            mermaid = prepare_office_diagram_source(
                root,
                directory / "diagram-source",
                scope,
                artifact,
                context,
                package_root=Path(dependencies["package_root"]),
                runtime_admission=mermaid_runtime,
                node_executable=Path(dependencies["node_executable"]),
                chrome_executable=Path(dependencies["chrome_executable"]),
                font_files=tuple(Path(item) for item in dependencies["font_files"]),
                decoded_pixel_budget=budget,
                pdfium_runtime=runtime,
                env=dict(os.environ),
                deadline=args.deadline,
                run_id=args.run_id,
            )
            native_kwargs = {
                "epubcheck_jar": _path(dependencies["epubcheck_jar"]),
                "java_executable": _path(dependencies["java_executable"]),
                "frozen_epub_engine": _path(dependencies["frozen_epub_engine"]),
            }
            try:
                if control == "office-cell":
                    candidate = reader.read(value["candidate"]["path"])
                    if candidate.relative != artifact.path or candidate.sha256 != value["candidate"]["sha256"]:
                        raise ValueError("Office actual candidate differs from original supervisor's exact input")
                    record = observe_office_full_source(
                        root,
                        directory / "full-source",
                        scope,
                        artifact,
                        candidate,
                        reader,
                        env=dict(os.environ),
                        deadline=args.deadline,
                        run_id=args.run_id,
                        mermaid_admission=mermaid,
                        **native_kwargs,
                    )
                    observed_outcome = record["observation"]
                    code = (
                        0
                        if observed_outcome["status"] == "observed"
                        and not observed_outcome["findings"]
                        and not observed_outcome["blockers"]
                        else 2
                    )
                    record = {
                        "scope": scope,
                        "kind": kind,
                        "control": control,
                        "oracle_exit_code": code,
                        "full_source": record,
                    }
                elif control == "diagram-census":
                    from infrastructure.reporting.native_office_diagram_census import observe_office_diagram_census

                    record = observe_office_diagram_census(
                        root,
                        directory,
                        scope,
                        artifact,
                        context,
                        mermaid,
                        env=dict(os.environ),
                        deadline=args.deadline,
                        run_id=args.run_id,
                        **native_kwargs,
                    )
                    code = 0
                else:
                    if mermaid is None:
                        raise ValueError("Office diagram control has no genuine current Source diagrams")
                    positive = build_office_diagram_native_positive(
                        root,
                        directory / "positive-native",
                        scope,
                        artifact,
                        context,
                        mermaid,
                        env=dict(os.environ),
                        deadline=args.deadline,
                        run_id=args.run_id,
                        **native_kwargs,
                    )
                    code, record = run_office_diagram_control(
                        root,
                        directory,
                        positive.pdf,
                        positive.sources,
                        control,
                        target_ordinal=value["target"]["ordinal"],
                        budget=budget,
                        positive=positive,
                        pdfium_runtime=runtime,
                        env=dict(os.environ),
                        deadline=args.deadline,
                        run_id=args.run_id,
                    )
                    if record["target"] != value["target"]:
                        raise ValueError("Office child independently selected a different complete-census placement")
                    record.update({"scope": scope, "kind": kind})
            except Exception as error:
                code = 2
                record = {
                    "scope": scope,
                    "kind": kind,
                    "control": control,
                    "oracle_exit_code": code,
                    "blocked": {"class": type(error).__name__, "message": str(error)},
                }
            binding = write_json(root, directory / "observation.json", record)
            retained = reader.read(binding["path"])
            if retained.sha256 != binding["sha256"]:
                raise ValueError("Office actual original observation changed during terminal custody")
            runtime.verify()
            context.verify_correspondence(context.reference, root, reader, args.deadline)
            remaining(args.deadline)
            sys.stdout.write(f"OFFICE_OBSERVATION_V1 {spec.sha256} {retained.sha256} {args.run_id} {code}\n")
            sys.stdout.flush()
            remaining(args.deadline)
            return code


if __name__ == "__main__":
    raise SystemExit(main())
