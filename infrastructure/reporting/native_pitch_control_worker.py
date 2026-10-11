"""One fixed selected-SDK child for a complete configured Pitch control axis."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_pitch_control_plan import SCOPE, compile_pitch_control_plan
from infrastructure.reporting.native_pitch_control_run import run_pitch_control
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

WORKER = "infrastructure.reporting.native_pitch_control_worker"
CHILD_SCHEMA = "template-source-owned-pitch-child-v1"


def main() -> int:
    import infrastructure
    from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard, native_environment
    from infrastructure.reporting.native_source_external_admission import admit_explicitly_bound_native_source
    from infrastructure.reporting.native_tool_producer import native_producer_operation

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--specification", required=True)
    parser.add_argument("--specification-sha256", required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    with native_deadline_guard(args.deadline):
        remaining(args.deadline)
        root = args.root.absolute()
        reader = SnapshotReader(root)
        snapshot = reader.read(args.specification)
        spec = snapshot.json_object()
        if (
            set(spec)
            != {
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
                "formats",
                "plan_digest",
            }
            or snapshot.sha256 != args.specification_sha256
            or spec["schema_version"] != CHILD_SCHEMA
            or spec["scope"] != SCOPE
            or spec["deadline_monotonic"] != args.deadline
            or spec["run_id"] != args.run_id
            or type(spec["expected_exit"]) is not int
            or spec["expected_exit"] != (0 if spec["name"] == "baseline" else 1)
        ):
            raise ValueError("Pitch child differs from exact parent prelaunch Source/control/clock")
        implementation = reader.read(spec["implementation"]["path"])
        if (
            implementation.sha256 != args.implementation_sha256
            or implementation.sha256 != spec["implementation"]["sha256"]
        ):
            raise ValueError("Pitch child actual selected SDK differs from genuine parent nomination")
        if infrastructure.__file__ is None:
            raise ValueError("Pitch child actual installed SDK origin is unavailable")
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
        if source is None or json.loads(source.descriptor(SCOPE, deadline=args.deadline)) != spec["source"]:
            raise ValueError("Pitch child lacks fresh real original/current Source/SDK admission")
        directory = root / spec["directory"]
        if (
            snapshot.path != directory / "specification.json"
            or spec["parent_pid"] != os.getppid()
            or spec["parent_platform"] != platform.system()
            or directory != directory.resolve(strict=True)
        ):
            raise ValueError("Pitch child differs from actual parent/PID/private leaf")
        formats = spec["formats"]
        if not isinstance(formats, list) or not all(isinstance(value, str) for value in formats):
            raise ValueError("Pitch child lost the exact ordered declared native formats")
        with native_producer_operation(
            source, run_id=args.run_id, deadline=args.deadline, scope=SCOPE, directory=directory
        ) as owner:
            reader = SnapshotReader(root, native_producer_operation=owner)
            plan, _ = compile_pitch_control_plan(root, reader, formats=tuple(formats), deadline=args.deadline)
            if plan["digest"] != spec["plan_digest"] or spec["name"] not in plan["active_controls"]:
                raise ValueError("Pitch child complete Source-selected pair/page plan differs")
            binding = run_pitch_control(
                root,
                directory / "fixture",
                spec["name"],
                formats=tuple(formats),
                reader=reader,
                env=native_environment(root, Path(sys.executable), directory),
                deadline=args.deadline,
                run_id=args.run_id,
            )
            observation = reader.read(binding["path"])
            if (
                observation.sha256 != binding["sha256"]
                or observation.json_object()["oracle_exit_code"] != spec["expected_exit"]
            ):
                raise ValueError("Pitch child terminal observation differs from actual complete oracle")
            owner.verify(reader, run_id=args.run_id, deadline=args.deadline)
            remaining(args.deadline)
            sys.stdout.write(
                f"PITCH_OBSERVATION_V1 {snapshot.sha256} {observation.sha256} {args.run_id} {spec['expected_exit']}\n"
            )
            sys.stdout.flush()
            remaining(args.deadline)
            return int(spec["expected_exit"])


if __name__ == "__main__":
    raise SystemExit(main())
