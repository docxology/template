"""Read exact retained original Code from actual prepared installed invocations."""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from infrastructure.core.bytecode_audit import MAX_CACHE_BYTES, MAX_EXECUTIONS, canonical_code
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_code_runtime import validate_native_code_runtime
from infrastructure.reporting.native_installed_preparation import NativePreparedRuntime
from infrastructure.reporting.native_source_provider_bootstrap import CLOSURE_SCHEMA
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def validate_prepared_code(
    prepared: NativePreparedRuntime,
    closure_directory: Path,
    implementation_bytes: bytes,
    process: Mapping[str, Any],
    *,
    role: str,
    provider_sources: Mapping[str, str],
) -> None:
    """Require actual signed OS0 plus exact Source-wheel Code/cache/member bytes.

    This consumes a direct result in the actual parent, not a JSON original
    constructor. Prepared SDK/wheel bodies are independently rechecked first
    and last. Native/kernelloaded approval remains outside this Code predicate.
    """
    prepared.verify()
    if process.get("accepted") is not True or process.get("original_exit_code") != 0:
        raise ValueError("prepared Code readback requires genuine successful original supervision")
    reader = SnapshotReader(prepared.current_root)
    closure = reader.read((closure_directory / "receipt.json").relative_to(reader.root).as_posix())
    raw = closure.json_object()
    if (
        raw.get("schema_version") != CLOSURE_SCHEMA
        or raw.get("status") != "pass"
        or raw.get("errors") != []
        or raw.get("original_operation_deadline") != prepared.deadline
        or raw.get("selected_sdk_package_root") != str(prepared.sdk_package_root)
        or raw.get("worker_outcome")
        != {"kind": "raised", "class": "SystemExit", "module": "builtins", "system_exit_code": 0}
    ):
        raise ValueError(
            "prepared original SDK Code closure is missing, failed or has a different original clock/OS result"
        )
    runtime = validate_native_code_runtime(raw.get("runtime"))
    expected_sources = {
        str(prepared.sdk_package_root / name.removeprefix("infrastructure/")): digest
        for name, digest in prepared.core_wheel.members.items()
        if name.startswith("infrastructure/") and name.endswith(".py")
    }
    expected_sources.update(provider_sources)
    consumed: set[str] = set()
    total = count = 0

    def payload(binding: object) -> bytes:
        nonlocal total
        remaining(prepared.deadline)
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256", "bytes"}:
            raise ValueError("prepared retained Code payload fields differ")
        name = binding["path"]
        if not isinstance(name, str) or Path(name).name != name or not name.startswith("payload-") or name in consumed:
            raise ValueError("prepared retained Code payload membership is unsafe or repeated")
        consumed.add(name)
        item = reader.read((closure_directory / name).relative_to(reader.root).as_posix())
        total += len(item.content)
        if (
            item.sha256 != binding["sha256"]
            or len(item.content) != binding["bytes"]
            or total + len(closure.content) > MAX_CACHE_BYTES
        ):
            raise ValueError("prepared retained actual Code payload changed or exceeded the unchanged byte ceiling")
        return item.content

    hook = payload(raw.get("raw_hook"))
    if hashlib.sha256(hook).hexdigest() != prepared.core_wheel.members["infrastructure/core/bytecode_audit.py"]:
        raise ValueError("prepared original raw audit hook differs from actual Source-wheel body")
    if payload(raw.get("implementation_bytes")) != implementation_bytes:
        raise ValueError("prepared Code closure retained different actual SDK input bytes")
    rows = raw.get("executions")
    if not isinstance(rows, list) or not rows or len(rows) > MAX_EXECUTIONS:
        raise ValueError("prepared actual execution inventory is absent or exceeds the original bound")
    seen: set[str] = set()
    for row in rows:
        remaining(prepared.deadline)
        if not isinstance(row, dict) or set(row) != {"source_path", "source", "runs"}:
            raise ValueError("prepared retained actual execution fields differ")
        label = row["source_path"]
        body = payload(row["source"])
        if label in seen or expected_sources.get(label) != hashlib.sha256(body).hexdigest():
            raise ValueError("prepared executed provider was not independently admitted by Source wheel membership")
        seen.add(label)
        canonical = canonical_code(compile(body, label, "exec", dont_inherit=True, optimize=sys.flags.optimize))
        if not isinstance(row["runs"], list) or not row["runs"]:
            raise ValueError("prepared source has no genuine retained execution")
        for run in row["runs"]:
            count += 1
            if (
                count > MAX_EXECUTIONS
                or set(run) != {"executed_code", "cache"}
                or payload(run["executed_code"]) != canonical
            ):
                raise ValueError("prepared actual Code differs from original Source compilation")
            cache = run["cache"]
            if cache is not None:
                cached = payload(cache["bytes"])
                if (
                    set(cache) != {"original_path", "execution_sha256", "bytes"}
                    or not Path(cache["original_path"]).is_relative_to(raw["prefix"])
                    or len(cached) < 16
                    or cached[:4].hex() != runtime["magic_hex"]
                    or hashlib.sha256(cached).hexdigest() != cache["execution_sha256"]
                ):
                    raise ValueError("prepared original cache differs from the actual execution-time bytes")
    worker = str(prepared.sdk_package_root / (role.removeprefix("infrastructure.").replace(".", "/") + ".py"))
    if worker not in seen or raw.get("retained_payload_bytes") != total:
        raise ValueError("prepared Code closure lacks its actual Source-owned role or exact payload count")
    if {path.name for path in closure_directory.iterdir()} != consumed | {"receipt.json"} or not reader.unchanged():
        raise ValueError("prepared Code closure membership changed")
    prepared.verify()
    remaining(prepared.deadline)
