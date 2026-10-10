"""Fixed basic/semantic browser children with genuine Source and native custody."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _role(semantic: bool) -> tuple[Any, str, str, str, dict[str, str | None]]:
    from infrastructure.reporting.native_format_browser_oracles import BROWSER_CONTROL_CODES
    from infrastructure.reporting.native_format_browser_semantic_controls import SEMANTIC_CONTROL_CODES
    from infrastructure.reporting.native_print_child_custody import (
        BasicBrowserControlReaderOperation,
        SemanticBrowserControlReaderOperation,
    )

    if type(semantic) is not bool:
        raise ValueError("browser child requires a Source-owned fixed basic/semantic role")
    return (
        (
            SemanticBrowserControlReaderOperation,
            "infrastructure.reporting.native_format_browser_semantic_controls",
            "browser-semantic-child",
            "BROWSER_SEMANTIC_OBSERVATION_V1",
            SEMANTIC_CONTROL_CODES,
        )
        if semantic
        else (
            BasicBrowserControlReaderOperation,
            "infrastructure.reporting.native_format_browser_oracles",
            "browser-child",
            "BROWSER_OBSERVATION_V1",
            BROWSER_CONTROL_CODES,
        )
    )


def supervise_browser_source_controls(
    root: Path,
    directory: Path,
    scope: str,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    interpreter: Path,
    semantic: bool,
) -> list[dict[str, Any]]:
    """Actual parent ToolAPI holds every child; original outcome DATA is separate."""
    from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
    from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation

    role, worker, purpose, _, names = _role(semantic)
    owner = current_native_producer_operation()
    if owner is None or owner.run_id != run_id or owner.deadline != deadline:
        raise ValueError("browser controls require the actual original live Source owner/run/clock")
    source = owner.source
    selected = json.loads(source.bindings.expected_implementation_bytes)["runtime_environment"]
    if not interpreter.is_absolute() or str(interpreter.resolve(strict=True)) != selected["python_executable"]:
        raise ValueError("browser control launcher differs from independently admitted selected SDK interpreter")
    parent = SnapshotReader(root, native_producer_operation=owner)
    records = []
    for name, finding in names.items():
        remaining(deadline)
        child_deadline = min(deadline, time.monotonic() + 120.0)
        prefix = "browser-semantic" if semantic else "browser-control"
        leaf = directory / f"{prefix}-{name}"
        create_private_native_directory(root, leaf)
        create_private_native_directory(root, leaf / "closure")
        source.verify_correspondence(source.reference, root, parent, child_deadline)
        implementation_path = leaf / "implementation.json"
        atomic_write_bytes_confined(
            root, implementation_path, source.bindings.expected_implementation_bytes, mode=0o600
        )
        implementation = parent.read(implementation_path.relative_to(root).as_posix())
        identity = (leaf / "closure").stat()
        expected = 0 if finding is None else 1
        spec = write_json(
            root,
            leaf / "specification.json",
            {
                "schema_version": role.schema,
                "scope": scope,
                "name": name,
                "run_id": run_id,
                "directory": leaf.relative_to(root).as_posix(),
                "source": json.loads(source.descriptor(scope, deadline=child_deadline)),
                "implementation": {"path": implementation.relative, "sha256": implementation.sha256},
                "expected_exit": expected,
                "parent_pid": os.getpid(),
                "parent_platform": platform.system(),
                "deadline_monotonic": child_deadline,
                "caller_deadline_monotonic": deadline,
                "closure_identity": [identity.st_dev, identity.st_ino],
            },
        )
        hook = source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
        if (
            hashlib.sha256(hook).hexdigest()
            != json.loads(source.bindings.expected_implementation_bytes)["files"][
                "infrastructure/core/bytecode_audit.py"
            ]
        ):
            raise ValueError("browser child raw hook differs from actual admitted installed SDK")
        bootstrap = format_selected_sdk_native_bootstrap(
            hook,
            source.bindings.selected_sdk_package_root,
            (),
            implementation_path,
            implementation.sha256,
            leaf / "closure",
            (identity.st_dev, identity.st_ino),
            child_deadline,
            required_worker_module=worker,
        )
        command = [
            str(interpreter),
            "-I",
            "-c",
            bootstrap,
            "--root",
            str(root),
            "--specification",
            spec["path"],
            "--specification-sha256",
            spec["sha256"],
            "--implementation-sha256",
            implementation.sha256,
            "--deadline",
            repr(child_deadline),
            "--run-id",
            run_id,
        ]
        process = native_tool_record(
            root,
            leaf,
            str(interpreter),
            command[1:],
            env=env,
            deadline=child_deadline,
            run_id=run_id,
            purpose=purpose,
            preserve_nominated_launcher=True,
        )
        if process["exit_code"] != expected or process["original_exit_code"] != expected:
            raise ValueError("browser child did not preserve its actual original native oracle exit")
        observation = parent.read((leaf / "control-observation.json").relative_to(root).as_posix())
        closure = parent.read((leaf / "closure/receipt.json").relative_to(root).as_posix())
        item = {
            "name": name,
            "artifact": {"path": observation.relative, "sha256": observation.sha256},
            "process_artifact": process["artifact"],
            "specification_artifact": spec,
            "closure_artifact": {"path": closure.relative, "sha256": closure.sha256},
            "original_exit_code": expected,
        }
        context = role(source, parent, [item], scope=scope, run_id=run_id, deadline=deadline)
        context.child(item, SnapshotReader(root, native_control_operation=context))
        records.append(item)
        source.verify_correspondence(source.reference, root, parent, deadline)
    return records


def browser_source_child_main(*, semantic: bool) -> int:
    """Admit the actual child before any control execution and emit raw OS seals."""
    from infrastructure.reporting.native_format_acceptance_contracts import native_deadline_guard, native_environment
    from infrastructure.reporting.native_source_external_admission import admit_explicitly_bound_native_source
    from infrastructure.reporting.native_tool_producer import native_producer_operation
    import infrastructure

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--specification", required=True)
    parser.add_argument("--specification-sha256", required=True)
    parser.add_argument("--implementation-sha256", required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    role, _, _, seal, names = _role(semantic)
    with native_deadline_guard(args.deadline):
        root = args.root.absolute()
        reader = SnapshotReader(root)
        original = reader.read(args.specification)
        spec = original.json_object()
        if (
            original.sha256 != args.specification_sha256
            or spec.get("schema_version") != role.schema
            or spec.get("deadline_monotonic") != args.deadline
            or spec.get("run_id") != args.run_id
            or spec.get("name") not in names
            or spec.get("expected_exit") != (0 if names[spec["name"]] is None else 1)
        ):
            raise ValueError("browser child differs from exact parent Source-owned roster/role/clock")
        implementation = reader.read(spec["implementation"]["path"])
        if (
            implementation.sha256 != args.implementation_sha256
            or implementation.sha256 != spec["implementation"]["sha256"]
        ):
            raise ValueError("browser child selected implementation differs from actual parent nomination")
        if infrastructure.__file__ is None:
            raise ValueError("browser child actual selected SDK origin is unavailable")
        identity = root.stat()
        source = admit_explicitly_bound_native_source(
            root,
            environment=dict(os.environ),
            current_root_identity=(identity.st_dev, identity.st_ino),
            selected_sdk_package_root=Path(infrastructure.__file__).absolute().parent,
            expected_implementation_bytes=implementation.content,
            run_id=args.run_id,
            deadline=args.deadline,
            fresh_pycache_prefix=Path(sys.pycache_prefix) if sys.pycache_prefix else None,
        )
        if source is None or json.loads(source.descriptor(spec["scope"], deadline=args.deadline)) != spec["source"]:
            raise ValueError("browser child lacks genuine fresh Source/current selected SDK correspondence")
        directory = root / spec["directory"]
        if (
            original.path != directory / "specification.json"
            or spec["parent_pid"] != os.getppid()
            or spec["parent_platform"] != platform.system()
        ):
            raise ValueError("browser child differs from actual original parent/root/platform")
        with native_producer_operation(source, run_id=args.run_id, deadline=args.deadline) as owner:
            reader = SnapshotReader(root, native_producer_operation=owner)
            env = native_environment(root, Path(sys.executable), directory)
            if semantic:
                from infrastructure.reporting.native_format_browser_semantic_controls import run_semantic_control

                raw = run_semantic_control(
                    root, directory, spec["name"], env=env, deadline=args.deadline, run_id=args.run_id
                )
            else:
                from infrastructure.reporting.native_format_observer_dispatch import _chrome
                from infrastructure.reporting.native_format_browser_oracles import (
                    audit_browser_html,
                    browser_control_bytes,
                    browser_control_contract,
                    require_browser_control_result,
                )

                observed = audit_browser_html(
                    root,
                    directory,
                    browser_control_bytes(spec["name"]),
                    browser_control_contract(),
                    chrome=_chrome(env),
                    env=env,
                    deadline=args.deadline,
                    run_id=args.run_id,
                )
                raw = {
                    "schema_version": "template-native-browser-valid-control-v1",
                    "name": spec["name"],
                    "run_id": args.run_id,
                    "observation": observed,
                    "oracle_exit_code": require_browser_control_result(spec["name"], observed),
                }
            code = raw["oracle_exit_code"]
            if type(code) is not int or code != spec["expected_exit"]:
                raise ValueError("browser child setup failure cannot replace its actual intended native diagnostic")
            binding = write_json(root, directory / "control-observation.json", raw)
            source.verify_correspondence(source.reference, root, reader, args.deadline)
            observation = reader.read(binding["path"])
            sys.stdout.write(f"{seal} {original.sha256} {observation.sha256} {args.run_id} {code}\n")
            sys.stdout.flush()
            return int(code)
