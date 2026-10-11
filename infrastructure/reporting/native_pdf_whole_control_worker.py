"""Fixed selected-SDK original whole-PDF page/occurrence control child."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard, native_environment
from infrastructure.reporting.native_pdf_whole_control_run import (
    observe_whole_pdf_control_baseline,
    run_whole_pdf_native_control,
)
from infrastructure.reporting.native_print_child_custody import WHOLE_PDF_CHILD_SCHEMA
from infrastructure.reporting.native_source_external_admission import admit_explicitly_bound_native_source
from infrastructure.reporting.native_tool_producer import native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SPEC_FIELDS = frozenset(
    {
        "schema_version",
        "scope",
        "name",
        "run_id",
        "directory",
        "source",
        "implementation",
        "expected_exit",
        "parent_pid",
        "parent_platform",
        "deadline_monotonic",
        "caller_deadline_monotonic",
        "closure_identity",
        "artifact_id",
        "declared_formats",
        "pipeline_run_id",
        "plan_digest",
        "requirements_digest",
    }
)


def main() -> int:
    """Re-admit genuine Source before reading control expectations as DATA.

    The worker exits one only after the actual native effect and required full
    predicate diagnostic exist. Parser/setup/no-op/custody failures never write
    or seal a successful control observation. The parent observes OS status.
    """
    import infrastructure

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--specification", required=True)
    parser.add_argument("--specification-sha256", required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    with native_deadline_guard(args.deadline):
        root = args.root.absolute()
        reader = SnapshotReader(root)
        specification = reader.read(args.specification)
        spec = specification.json_object()
        if (
            set(spec) != SPEC_FIELDS
            or specification.sha256 != args.specification_sha256
            or spec["schema_version"] != WHOLE_PDF_CHILD_SCHEMA
            or spec["run_id"] != args.run_id
            or spec["deadline_monotonic"] != args.deadline
            or spec["scope"] not in PUBLIC_PROJECT_NAMES
            or spec["artifact_id"] != "manuscript:pdf"
            or not isinstance(spec["declared_formats"], list)
            or any(type(value) is not str for value in spec["declared_formats"])
            or type(spec["expected_exit"]) is not int
            or spec["expected_exit"] not in (0, 1)
        ):
            raise ValueError("whole PDF actual worker differs from its fixed Source-owned role/specification")
        implementation = reader.read(spec["implementation"]["path"])
        if (
            implementation.sha256 != args.implementation_sha256
            or implementation.sha256 != spec["implementation"]["sha256"]
            or infrastructure.__file__ is None
        ):
            raise ValueError("whole PDF actual worker SDK nomination differs")
        metadata = root.stat()
        source = admit_explicitly_bound_native_source(
            root,
            environment=dict(os.environ),
            current_root_identity=(metadata.st_dev, metadata.st_ino),
            selected_sdk_package_root=Path(infrastructure.__file__).absolute().parent,
            expected_implementation_bytes=implementation.content,
            run_id=args.run_id,
            deadline=args.deadline,
            fresh_pycache_prefix=Path(sys.pycache_prefix) if sys.pycache_prefix else None,
        )
        if source is None or json.loads(source.descriptor(spec["scope"], deadline=args.deadline)) != spec["source"]:
            raise ValueError("whole PDF actual child lacks fresh independent genuine Source correspondence")
        leaf = root / spec["directory"]
        if (
            specification.path != leaf / "specification.json"
            or type(spec["parent_pid"]) is not int
            or spec["parent_pid"] != os.getppid()
            or spec["parent_platform"] != platform.system()
        ):
            raise ValueError("whole PDF actual child differs from its independently observed parent/root/platform")
        with native_producer_operation(source, run_id=args.run_id, deadline=args.deadline) as owner:
            reader = SnapshotReader(root, native_producer_operation=owner)
            env = native_environment(root, Path(sys.executable), leaf)
            baseline = observe_whole_pdf_control_baseline(
                root,
                leaf / "baseline",
                spec["scope"],
                tuple(spec["declared_formats"]),
                artifact_id=spec["artifact_id"],
                pipeline_run_id=spec["pipeline_run_id"],
                plan_digest=spec["plan_digest"],
                reader=reader,
                env=env,
                deadline=args.deadline,
                run_id=args.run_id,
            )
            requirements = baseline["source_predicates"]["control_requirements"]
            controls = [row for row in requirements["controls"] if row["identity"] == spec["name"]]
            if (
                requirements["content_digest"] != spec["requirements_digest"]
                or len(controls) != 1
                or controls[0]["unsupported"] is not None
                or spec["expected_exit"] != int(controls[0]["intended_diagnostic"] is not None)
            ):
                raise ValueError(
                    "whole PDF actual child control differs from complete independently compiled Source roster"
                )
            result = run_whole_pdf_native_control(
                root,
                leaf / "mutant",
                spec["scope"],
                baseline,
                spec["name"],
                reader,
                env=env,
                deadline=args.deadline,
                run_id=args.run_id,
            )
            result.update({"worker_pid": os.getpid(), "worker_platform": platform.system()})
            if result["oracle_exit_code"] != spec["expected_exit"]:
                raise ValueError("whole PDF actual native predicate differs from the expected original OS oracle")
            write_json(root, leaf / "control-observation.json", result)
            source.verify_correspondence(source.reference, root, reader, args.deadline)
            observed = reader.read((leaf / "control-observation.json").relative_to(root).as_posix())
            if not reader.unchanged():
                raise ValueError("whole PDF actual child retained input/body changed before original seal")
            sys.stdout.write(
                f"WHOLE_PDF_OBSERVATION_V1 {specification.sha256} {observed.sha256} "
                f"{args.run_id} {result['oracle_exit_code']}\n"
            )
            sys.stdout.flush()
            return int(result["oracle_exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
