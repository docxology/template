"""Actual fixed auxiliary print worker entry and retained executed Code.

The parent-derived payload, rather than a receipt or matching argv, enters the
role. Retained Code remains DATA until a genuine supervisor/collector owns it.
"""

from __future__ import annotations

import hashlib
import os
import sys
import types
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any
from collections.abc import Iterator

from infrastructure.core.bytecode_audit import MAX_CACHE_BYTES, MAX_EXECUTIONS, canonical_code
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

ROLE = "root:macos:rendering"
SCHEMA = "template-auxiliary-print-code-v1"
_ENTRY: ContextVar[tuple[Path, dict[str, Any]] | None] = ContextVar("auxiliary_print_entry", default=None)


def nomination(root: Path, arguments: tuple[str, ...]) -> dict[str, Any] | None:
    """Capture parent-written exact spec bytes before the actual worker starts."""
    if len(arguments) != 2 or arguments[0] != "--spec":
        return None
    path = Path(arguments[1])
    raw = read_bytes_confined(root, path, max_bytes=1024 * 1024)
    from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

    spec = json_object_from_bytes(raw)
    if spec.get("gate") != ROLE or spec.get("negative"):
        return None
    if not {"run_id", "operation_deadline", "parent_pid"} <= spec.keys():
        return None  # Unnominated standalone workers receive no capability.
    import math
    import re

    if (
        not isinstance(spec["run_id"], str)
        or re.fullmatch(r"[0-9a-f]{32}", spec["run_id"]) is None
        or type(spec["operation_deadline"]) not in (float, int)
        or not math.isfinite(spec["operation_deadline"])
        or spec["parent_pid"] != os.getpid()
    ):
        raise ValueError("auxiliary print needs its actual parent run/PID/finite deadline")
    remaining(spec["operation_deadline"])
    return {
        "spec_path": str(path),
        "spec_sha256": hashlib.sha256(raw).hexdigest(),
        "run_id": spec["run_id"],
        "deadline": spec["operation_deadline"],
        "parent_pid": spec["parent_pid"],
        "producer_root": str(root),
    }


@contextmanager
def audited_entry(root: Path, held: dict[str, Any], payload_path: Path) -> Iterator[None]:
    """Enter only from the actual Source-generated preimport-audited payload."""
    frame = sys._getframe(2)  # contextlib enters the generator from the payload.
    from infrastructure.project.public_acceptance_auxiliary_bootstrap import WORKER, _body

    expected, _ = _body(
        Path(sys.executable),
        root,
        WORKER,
        ("--spec", held["spec_path"]),
        payload_path.parent,
        original_root=root,
        print_nomination=held,
    )
    payload_body = read_bytes_confined(root, payload_path)
    registry = getattr(sys, "_template_executed_bytecode_audit", None)
    if (
        _ENTRY.get() is not None
        or not isinstance(registry, types.MappingProxyType)
        or sys.pycache_prefix is None
        or registry.get("prefix") != sys.pycache_prefix
        or registry.get("hook_source_path") != str(root / "infrastructure/core/bytecode_audit.py")
        or frame.f_code.co_filename != "<string>"
        or payload_body != expected
        or canonical_code(frame.f_code)
        != canonical_code(compile(payload_body, frame.f_code.co_filename, "exec", dont_inherit=True))
        or os.getppid() != held["parent_pid"]
        or hashlib.sha256(read_bytes_confined(root, Path(held["spec_path"]))).hexdigest() != held["spec_sha256"]
    ):
        raise ValueError("auxiliary print entry lacks its actual audited parent-bound fixed worker payload")
    from infrastructure.core.bytecode_audit import verify_executed_source_code

    remaining(held["deadline"])
    verify_executed_source_code(root / "infrastructure", Path(sys.pycache_prefix))
    token = _ENTRY.set((root, dict(held)))
    try:
        yield
    finally:
        _ENTRY.reset(token)


def require_entry(root: Path) -> dict[str, Any]:
    value = _ENTRY.get()
    if value is None or value[0] != root:
        raise ValueError("auxiliary print requires its actual audited fixed worker entry")
    held = value[1]
    remaining(held["deadline"])
    if os.getppid() != held["parent_pid"]:
        raise ValueError("auxiliary print original parent changed")
    return dict(held)


def retain_code(root: Path, directory: Path, held: dict[str, Any], outcome: dict[str, Any]) -> dict[str, str]:
    """Close actual registry Code/cache before the supervisor removes the prefix."""
    from infrastructure.core.bytecode_audit import _read_cache, verify_executed_source_code
    from infrastructure.reporting.native_code_runtime import observe_native_code_runtime

    require_entry(root)
    registry = getattr(sys, "_template_executed_bytecode_audit")
    prefix = Path(sys.pycache_prefix or "")
    snapshot = registry["snapshot"]()
    if not isinstance(snapshot, types.MappingProxyType) or len(snapshot) > MAX_EXECUTIONS:
        raise ValueError("auxiliary print actual Code inventory exceeds its finite bound")
    directory.mkdir(mode=0o700)
    total = count = 0

    def retain(body: bytes) -> dict[str, str]:
        nonlocal total, count
        remaining(held["deadline"])
        total += len(body)
        if total > MAX_CACHE_BYTES:
            raise ValueError("auxiliary print retained Code exceeds its existing byte ceiling")
        path = directory / f"payload-{count:06d}.bin"
        count += 1
        atomic_write_bytes_confined(root, path, body, mode=0o600)
        return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(body).hexdigest()}

    for source in registry["source_roots"]:
        verify_executed_source_code(Path(source), prefix)
    executions = []
    for filename, runs in sorted(snapshot.items()):
        source = Path(filename)
        relative = source.relative_to(root).as_posix()
        body = _read_cache(source)
        observed = []
        for code, cache, digest in runs:
            observed.append(
                {
                    "code": retain(canonical_code(code)),
                    "cache": None
                    if cache is None
                    else {"bytes": retain(_read_cache(Path(cache))), "sha256": digest, "original_path": cache},
                }
            )
        executions.append({"path": relative, "filename": filename, "source": retain(body), "runs": observed})
    return write_json(
        root,
        directory / "receipt.json",
        {
            "schema_version": SCHEMA,
            "nomination": held,
            "pid": os.getpid(),
            "outcome": outcome,
            "runtime": observe_native_code_runtime(),
            "prefix": str(prefix),
            "hook": retain(_read_cache(Path(registry["hook_source_path"]))),
            "executions": executions,
            "payload_bytes": total,
        },
    )


def validate_code(
    reader: SnapshotReader, binding: dict[str, str], held: dict[str, Any], pid: int, deadline: float
) -> None:
    """Validate retained bytes only after an external original was authenticated."""
    from infrastructure.reporting.native_code_runtime import validate_native_code_runtime

    snapshot = reader.read(binding["path"])
    if snapshot.sha256 != binding["sha256"]:
        raise ValueError("auxiliary print original Code closure changed")
    raw = snapshot.json_object()
    if (
        set(raw)
        != {
            "schema_version",
            "nomination",
            "pid",
            "outcome",
            "runtime",
            "prefix",
            "hook",
            "executions",
            "payload_bytes",
        }
        or raw.get("schema_version") != SCHEMA
        or raw.get("nomination") != held
        or raw.get("pid") != pid
        or raw.get("outcome") != {"kind": "raised", "system_exit_code": 0}
        or raw.get("prefix") != str(Path(held["spec_path"]).parent / "execution/bytecode")
    ):
        raise ValueError("auxiliary print Code lacks its original successful worker/run/PID")
    runtime = validate_native_code_runtime(raw.get("runtime"))
    total = count = 0
    consumed = set()

    def payload(value: dict[str, str]) -> bytes:
        nonlocal total
        remaining(deadline)
        if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
            raise ValueError("auxiliary print Code payload binding is not exact")
        selected = reader.read(value["path"])
        if selected.sha256 != value["sha256"] or selected.path.parent != snapshot.path.parent:
            raise ValueError("auxiliary print retained Code payload changed or escaped")
        if selected.relative in consumed:
            raise ValueError("auxiliary print retained Code payload was reused")
        consumed.add(selected.relative)
        total += len(selected.content)
        if total > MAX_CACHE_BYTES:
            raise ValueError("auxiliary print retained Code exceeds its existing byte ceiling")
        return selected.content

    if payload(raw["hook"]) != reader.read("infrastructure/core/bytecode_audit.py").content:
        raise ValueError("auxiliary print raw hook differs from current Source")
    rows = raw.get("executions")
    if not isinstance(rows, list) or not 0 < len(rows) <= MAX_EXECUTIONS:
        raise ValueError("auxiliary print actual Code inventory is absent or excessive")
    seen = set()
    from infrastructure.reporting.native_office_cache_structure import verify_office_execution_cache

    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "filename", "source", "runs"}:
            raise ValueError("auxiliary print executed Source fields differ")
        path = row["path"]
        if path in seen:
            raise ValueError("auxiliary print Code contains duplicate Source")
        seen.add(path)
        body = payload(row["source"])
        if body != reader.read(path).content or row["filename"] != str(Path(held["producer_root"]) / path):
            raise ValueError("auxiliary print executed Source differs from current bytes")
        compiled = compile(body, row["filename"], "exec", dont_inherit=True, optimize=runtime["optimize"])
        if not isinstance(row["runs"], list) or not row["runs"]:
            raise ValueError("auxiliary print Source omitted actual execution")
        for run in row["runs"]:
            count += 1
            if (
                set(run) != {"code", "cache"}
                or count > MAX_EXECUTIONS
                or payload(run["code"]) != canonical_code(compiled)
            ):
                raise ValueError("auxiliary print actual Code differs from Source compilation")
            if run["cache"] is not None:
                if set(run["cache"]) != {"bytes", "sha256", "original_path"}:
                    raise ValueError("auxiliary print original cache fields differ")
                cache = payload(run["cache"]["bytes"])
                if (
                    len(cache) < 16
                    or cache[:4].hex() != runtime["magic_hex"]
                    or hashlib.sha256(cache).hexdigest() != run["cache"]["sha256"]
                ):
                    raise ValueError("auxiliary print cache differs from original execution")
                verify_office_execution_cache(
                    cache,
                    compiled,
                    original_path=run["cache"]["original_path"],
                    prefix=Path(raw["prefix"]),
                    execution_sha256=run["cache"]["sha256"],
                    deadline=deadline,
                )
    required = {
        "infrastructure/project/public_acceptance_auxiliary_worker.py",
        "infrastructure/reporting/native_print_witness.py",
        "infrastructure/reporting/native_tool_process.py",
    }
    members = {path.relative_to(reader.root).as_posix() for path in snapshot.path.parent.iterdir()}
    if (
        not required <= seen
        or total != raw["payload_bytes"]
        or members != consumed | {snapshot.relative}
        or not reader.unchanged()
    ):
        raise ValueError("auxiliary print original Code closure is incomplete or changed")
