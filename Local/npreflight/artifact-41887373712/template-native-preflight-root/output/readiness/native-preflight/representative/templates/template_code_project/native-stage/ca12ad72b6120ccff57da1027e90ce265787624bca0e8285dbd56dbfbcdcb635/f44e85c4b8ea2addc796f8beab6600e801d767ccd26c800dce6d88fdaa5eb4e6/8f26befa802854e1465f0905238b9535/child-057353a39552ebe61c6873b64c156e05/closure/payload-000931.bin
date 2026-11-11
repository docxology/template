"""Fixed complete Source stage-child Code/cache closure, granting no authority."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from infrastructure.core.bytecode_audit import MAX_CACHE_BYTES, MAX_EXECUTIONS, canonical_code
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_office_cache_structure import verify_office_execution_cache
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_stage_child_contracts import audit_roots
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _stage_closure(
    source: NativeSourceContext,
    spec: dict[str, Any],
    selected_binding: dict[str, str],
    reader: SnapshotReader,
    *,
    deadline: float,
    worker_code: int,
) -> dict[str, Any]:
    """Reconstruct every retained actual Code/cache body under all four roots."""
    from infrastructure.reporting.native_code_runtime import validate_native_code_runtime
    from infrastructure.reporting.native_format_acceptance_evidence import _file

    selected = _file(selected_binding, reader)
    raw = selected.json_object()
    sdk = Path(spec["source"]["selected_sdk"]["package_root"])
    mirror = Path(spec["source"]["current_mirror"]["root"])
    roots = audit_roots(mirror, sdk, spec["scope"])
    expected = json.loads(source.bindings.expected_implementation_bytes)["files"]
    code = {
        str(sdk / name.removeprefix("infrastructure/")): digest
        for name, digest in expected.items()
        if name.startswith("infrastructure/") and name.endswith(".py")
    }
    lanes = ("scripts/", f"projects/{spec['scope']}/src/", f"projects/{spec['scope']}/scripts/")
    for name, kind, _ in source.source_records:
        if kind == "file" and name.startswith(lanes) and name.endswith(".py"):
            actual = source.current_source_reader.read(name)
            if actual.content != source.reference.read(name):
                raise ValueError("native stage closure Source differs from independently held original")
            code[str(mirror / name)] = actual.sha256
    if (
        raw.get("schema_version") != "template-native-selected-sdk-execution-closure-v3"
        or raw.get("status") != "pass"
        or raw.get("errors") != []
        or raw.get("original_operation_deadline") != spec["deadline_monotonic"]
        or raw.get("source_roots") != [str(path) for path in roots]
        or raw.get("selected_sdk_package_root") != str(sdk)
        or raw.get("prefix") != str(mirror / spec["directory"] / "bytecode")
        or raw.get("native_os_exit_authority") != "original external process guardian only"
        or selected.path != reader.root / spec["directory"] / "closure/receipt.json"
        or not isinstance(raw.get("executions"), list)
        or len(raw["executions"]) > MAX_EXECUTIONS
    ):
        raise ValueError("native stage child lacks its exact complete Source/Code/preimport closure")
    validate_native_code_runtime(raw.get("runtime"))
    total = count = 0
    seen: set[str] = set()
    payload_names: set[str] = set()

    def payload(value: dict[str, Any]) -> bytes:
        nonlocal total
        remaining(deadline)
        if (
            not isinstance(value, dict)
            or set(value) != {"path", "sha256", "bytes"}
            or not isinstance(value["path"], str)
            or Path(value["path"]).name != value["path"]
            or not value["path"].startswith("payload-")
            or not value["path"].endswith(".bin")
            or value["path"] in payload_names
        ):
            raise ValueError("native stage actual closure payload label is unsafe or repeated")
        payload_names.add(value["path"])
        snapshot = reader.read((selected.path.parent / value["path"]).relative_to(reader.root).as_posix())
        total += len(snapshot.content)
        if (
            snapshot.sha256 != value["sha256"]
            or type(value["bytes"]) is not int
            or len(snapshot.content) != value["bytes"]
            or total + len(selected.content) > MAX_CACHE_BYTES
        ):
            raise ValueError("native stage actual closure payload bytes/bounds differ")
        return snapshot.content

    hook, implementation = payload(raw["raw_hook"]), payload(raw["implementation_bytes"])
    if (
        hashlib.sha256(hook).hexdigest() != code[str(sdk / "core/bytecode_audit.py")]
        or raw.get("hook_sha256") != hashlib.sha256(hook).hexdigest()
        or hashlib.sha256(implementation).hexdigest() != spec["implementation"]["sha256"]
        or raw["implementation_input"]
        != {"path": str(mirror / spec["implementation"]["path"]), "sha256": spec["implementation"]["sha256"]}
        or json.loads(implementation)["files"] != expected
    ):
        raise ValueError("native stage actual audit hook/SDK implementation differs from admitted Source")
    prefix = Path(raw["prefix"])
    for row in raw["executions"]:
        remaining(deadline)
        if (
            not isinstance(row, dict)
            or set(row) != {"source_path", "source", "runs"}
            or row["source_path"] in seen
            or not isinstance(row["runs"], list)
            or not row["runs"]
        ):
            raise ValueError("native stage actual Code execution row differs or repeats")
        filename = row["source_path"]
        seen.add(filename)
        held = payload(row["source"])
        if code.get(filename) != hashlib.sha256(held).hexdigest():
            raise ValueError("native stage child executed unadmitted SDK/root/project Source")
        compiled = compile(held, filename, "exec", dont_inherit=True, optimize=sys.flags.optimize)
        for execution in row["runs"]:
            count += 1
            if (
                not isinstance(execution, dict)
                or set(execution) != {"executed_code", "cache"}
                or count > MAX_EXECUTIONS
                or payload(execution["executed_code"]) != canonical_code(compiled)
            ):
                raise ValueError("native stage child actual executable Code differs from admitted Source")
            if execution["cache"] is not None:
                cached = execution["cache"]
                if not isinstance(cached, dict) or set(cached) != {"original_path", "execution_sha256", "bytes"}:
                    raise ValueError("native stage actual cache observation fields differ")
                verify_office_execution_cache(
                    payload(cached["bytes"]),
                    compiled,
                    original_path=cached["original_path"],
                    prefix=prefix,
                    execution_sha256=cached["execution_sha256"],
                    deadline=deadline,
                )
    required = {
        str(sdk / "reporting/native_stage_child_worker.py"),
        str(sdk / "core/pipeline/stage_worker.py"),
        str(sdk / "reporting/native_source_external_admission.py"),
        str(mirror / spec["script"]["path"]),
    }
    if (
        not required <= seen
        or total != raw["retained_payload_bytes"]
        or raw["worker_outcome"]
        != {
            "kind": "raised",
            "class": "SystemExit",
            "module": "builtins",
            "system_exit_code": worker_code,
        }
    ):
        raise ValueError("native stage child lacks actual fixed role/script executions and unchanged worker intent")
    if {path.name for path in selected.path.parent.iterdir()} != payload_names | {"receipt.json"}:
        raise ValueError("native stage actual closure has missing, duplicate or unbound payload files")
    remaining(deadline)
    return raw
