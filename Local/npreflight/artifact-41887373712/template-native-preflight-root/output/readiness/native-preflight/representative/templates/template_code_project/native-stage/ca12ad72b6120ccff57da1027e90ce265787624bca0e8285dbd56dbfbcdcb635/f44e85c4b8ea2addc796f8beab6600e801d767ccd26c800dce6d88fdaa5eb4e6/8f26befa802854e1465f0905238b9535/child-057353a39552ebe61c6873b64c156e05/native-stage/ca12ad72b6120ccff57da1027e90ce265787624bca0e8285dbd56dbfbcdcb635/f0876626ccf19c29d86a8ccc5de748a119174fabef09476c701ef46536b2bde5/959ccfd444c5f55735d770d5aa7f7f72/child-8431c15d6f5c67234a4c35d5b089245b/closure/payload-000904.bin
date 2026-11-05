"""One fixed child that independently admits Source before an existing stage."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard
from infrastructure.reporting.native_source_external_admission import admit_explicitly_bound_native_source
from infrastructure.reporting.native_stage_child import directory_identity
from infrastructure.reporting.native_stage_child_contracts import (
    OBSERVATION_SCHEMA,
    audit_roots,
    binding,
    validate_request,
    validate_specification,
    verify_stage_observation,
)
from infrastructure.reporting.native_tool_producer import native_producer_operation
from infrastructure.reporting.native_stage_child_scope import (
    _actual_native_stage_scope,
    _retained_native_stage_artifacts,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def main() -> int:
    """Existing script intent is retained; the enclosing ToolAPI owns OS status."""
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
        validate_specification(spec)
        if (
            specification.sha256 != args.specification_sha256
            or spec["run_id"] != args.run_id
            or spec["deadline_monotonic"] != args.deadline
        ):
            raise ValueError("native stage child specification differs from its actual parent command")
        implementation = reader.read(spec["implementation"]["path"])
        if (
            implementation.sha256 != args.implementation_sha256
            or implementation.sha256 != spec["implementation"]["sha256"]
            or infrastructure.__file__ is None
        ):
            raise ValueError("native stage child selected SDK differs from its actual parent binding")
        source = admit_explicitly_bound_native_source(
            root,
            environment=dict(os.environ),
            current_root_identity=directory_identity(root),
            selected_sdk_package_root=Path(infrastructure.__file__).absolute().parent,
            expected_implementation_bytes=implementation.content,
            run_id=args.run_id,
            deadline=args.deadline,
            fresh_pycache_prefix=Path(sys.pycache_prefix) if sys.pycache_prefix else None,
        )
        if source is None or json.loads(source.descriptor(spec["scope"], deadline=args.deadline)) != spec["source"]:
            raise ValueError("native stage child lacks fresh independent full Source/SDK correspondence")
        leaf = root / spec["directory"]
        if (
            specification.path != leaf / "specification.json"
            or spec["parent_pid"] != os.getppid()
            or spec["parent_platform"] != platform.system()
            or Path.cwd() != Path(spec["cwd"])
            or spec["source_audit_roots"]
            != [str(path) for path in audit_roots(root, source.bindings.selected_sdk_package_root, spec["scope"])]
            or directory_identity(leaf) != tuple(spec["directory_identity"])
            or directory_identity(leaf / "closure") != tuple(spec["closure_identity"])
            or directory_identity(leaf / "bytecode") != tuple(spec["prefix_identity"])
            or sys.pycache_prefix != str(leaf / "bytecode")
        ):
            raise ValueError("native stage actual child differs from its independently observed parent/roots/cache")
        request = reader.read(spec["request"]["path"])
        payload, protocol, script_sha = validate_request(source, spec["scope"], request, deadline=args.deadline)
        if (
            binding(request) != spec["request"]
            or protocol != spec["protocol"]
            or script_sha != spec["script"]["sha256"]
            or payload["run_id"] != spec["pipeline_run_id"]
            or payload["stage_key"] != spec["stage_key"]
        ):
            raise ValueError("native stage actual child request differs from its global and pipeline identities")
        with native_producer_operation(
            source,
            run_id=args.run_id,
            deadline=args.deadline,
            scope=spec["scope"],
            directory=leaf,
        ) as owner:
            with _actual_native_stage_scope(owner, specification):
                from infrastructure.core.pipeline.stage_worker import main as stage_main

                returned, error, code = None, None, 1
                previous_argv = list(sys.argv)
                try:
                    sys.argv = ["native-stage-child", str(request.path), spec["request_digest"], protocol]
                    returned = stage_main()
                    if type(returned) is not int or not 0 <= returned <= 255:
                        raise ValueError("existing Source stage worker returned an invalid intent convention")
                    code = returned
                except BaseException as exc:
                    error = {"class": type(exc).__name__, "module": type(exc).__module__}
                    returned = None
                    code = 130 if isinstance(exc, KeyboardInterrupt) else 1
                finally:
                    sys.argv = previous_argv
                active_reader = SnapshotReader(root, native_producer_operation=owner)
                optional = {}
                for name, filename in (("result", "result.json"), ("original_checkpoint", "original.json")):
                    optional[name] = (
                        binding(active_reader.read((leaf / filename).relative_to(root).as_posix()))
                        if (leaf / filename).exists()
                        else None
                    )
                observation = {
                    "schema_version": OBSERVATION_SCHEMA,
                    "scope": spec["scope"],
                    "run_id": args.run_id,
                    "pipeline_run_id": spec["pipeline_run_id"],
                    "stage_key": spec["stage_key"],
                    "nonce": spec["nonce"],
                    "request": binding(request),
                    "request_digest": spec["request_digest"],
                    "worker_pid": os.getpid(),
                    "parent_pid": os.getppid(),
                    "stage_return_code": returned,
                    "stage_exception": error,
                    **optional,
                    "nested_tool_artifacts": list(owner.retained_tool_bindings),
                    "stage_children": list(owner.stage_children),
                    "stage_artifacts": _retained_native_stage_artifacts(),
                    "script_intent_authority": "Source stage worker only; child signed OS belongs to parent ToolAPI",
                }
                verify_stage_observation(spec, observation, child_pid=os.getpid(), request=request)
                observed = write_json(root, leaf / "observation.json", observation)
                source.verify_correspondence(source.reference, root, active_reader, args.deadline)
                if not reader.unchanged() or not active_reader.unchanged():
                    raise ValueError(
                        "native stage child Source/request/result changed before its original observation seal"
                    )
                sys.stdout.write(
                    f"STAGE_CHILD_OBSERVATION_V1 {specification.sha256} {observed['sha256']} "
                    f"{args.run_id} {spec['nonce']} {code}\n"
                )
                sys.stdout.flush()
                return code


if __name__ == "__main__":
    raise SystemExit(main())
