"""Exact compiler/header/body DATA reconstruction under enclosing Tool custody."""

from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_loader_build import FLAGS, SOURCE, _auditor_abi
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "source_binding",
        "source",
        "compiler_header_selection",
        "compiler",
        "headers",
        "flags",
        "library",
        "platform",
        "architecture",
        "audit_abi",
        "audit_namespace_dependencies",
        "library_identity",
    }
)


def validate_compilation_data(
    binding: dict[str, str],
    reader: SnapshotReader,
    *,
    native: dict[str, Any],
    source_binding: list[str],
    run_id: str,
    original_deadline: float,
    original_completion: float,
) -> tuple[dict[str, Any], bytes]:
    """Reconstruct actual compiler commands and every selected retained header."""
    from infrastructure.reporting.native_loader_replay import _bound
    from infrastructure.reporting.native_tool_replay import validate_native_tool_data

    deadline = reader.native_operation.deadline if reader.native_operation is not None else original_deadline
    remaining(deadline)
    raw = _bound(binding, reader).json_object()
    flags = list(FLAGS) + (["-mno-outline-atomics"] if raw.get("architecture") == "aarch64" else [])
    if (
        set(raw) != _FIELDS
        or raw["schema_version"] != "template-source-native-loader-compilation-v1"
        or raw["run_id"] != run_id
        or raw["source_binding"] != source_binding
        or set(raw["source"]) != {"path", "sha256"}
        or raw["source"]["path"] != SOURCE
        or raw["flags"] != flags
        or raw["platform"] != "Linux"
        or raw["architecture"] not in {"x86_64", "aarch64"}
        or raw["audit_abi"] != 2
        or raw["audit_namespace_dependencies"] != []
    ):
        raise ValueError("loader compilation differs from fixed exact Source/host/ABI/flags")
    library = _bound(raw["library"], reader)
    _auditor_abi(library.content, architecture=raw["architecture"])
    identity = raw["library_identity"]
    if (
        set(identity) != {"device", "inode", "mode", "size", "mtime_ns", "ctime_ns", "links"}
        or any(type(value) is not int for value in identity.values())
        or identity["size"] != len(library.content)
        or identity["inode"] <= 0
        or identity["links"] != 1
    ):
        raise ValueError("loader compiled physical body has an unknown exact metadata shape")
    tools = {}
    for key, purpose in (
        ("compiler_header_selection", "loader-header-selection"),
        ("compiler", "loader-source-compilation"),
    ):
        tool = _bound(raw[key], reader).json_object()
        if (
            tool["owner_pid"] != native["owner_pid"]
            or tool["tool"] != "cc"
            or tool["purpose"] != purpose
            or tool["run_id"] != run_id
            or tool["original_exit_code"] != 0
            or tool["exit_code"] != 0
        ):
            raise ValueError("loader compiler command belongs to another actual owner/role/run/signed OS result")
        validate_native_tool_data(
            tool, reader, original_deadline=original_deadline, original_completion=original_completion
        )
        tools[key] = tool
    dependency, compilation = tools["compiler_header_selection"], tools["compiler"]
    source_inputs = dependency["consumed_input_artifacts"]
    if len(source_inputs) != 1:
        raise ValueError("fixed compiler header discovery must consume exactly one held Source C body")
    c_input = source_inputs[0]
    held_c = _bound(c_input["artifact"], reader)
    c_path = c_input["observation"]["path"]
    if held_c.sha256 != raw["source"]["sha256"] or Path(c_path).name != "source-loader-audit.c":
        raise ValueError("loader fixed actual compiler input differs from retained Source C bytes")
    if dependency["command"] != [dependency["executable"], "-std=c11", "-M", "-MT", "source-loader-audit.o", c_path]:
        raise ValueError("loader header discovery command differs from its fixed Source argv")
    output = str(Path(c_path).parent / "source-loader-audit.so")
    if compilation["command"] != [compilation["executable"], *flags, c_path, "-o", output]:
        raise ValueError("loader actual compilation command differs from fixed Source input/output/flags")
    if compilation["cwd"] != dependency["cwd"] or compilation["environment_digest"] != dependency["environment_digest"]:
        raise ValueError("loader compiler/header selection changed actual CWD or sanitized environment")
    stream = _bound({key: dependency["raw_stdout"][key] for key in ("path", "sha256")}, reader).content
    tokens = shlex.split(stream.decode("utf-8", "strict").replace("\\\n", ""), posix=True)
    if not tokens or tokens.pop(0) != "source-loader-audit.o:" or not 0 < len(tokens) <= 1024:
        raise ValueError("loader actual complete compiler header roster is absent or unbounded")
    selected_names = {
        os.path.normpath(value if Path(value).is_absolute() else str(Path(dependency["cwd"]) / value))
        for value in tokens
    }
    headers = raw["headers"]
    if not isinstance(headers, list) or not 0 < len(headers) <= 1024:
        raise ValueError("loader retained complete compiler header cohort exceeds its bound")
    consumed = compilation["consumed_input_artifacts"]
    if len(consumed) != len(headers) + 1 or _bound(consumed[0]["artifact"], reader).content != held_c.content:
        raise ValueError("loader compilation omitted its exact Source body or full selected header cohort")
    names, physical_names, total = set(), set(), 0
    for row, entry in zip(headers, consumed[1:], strict=True):
        remaining(deadline)
        if set(row) != {"observation", "compiler_paths", "artifact"}:
            raise ValueError("loader compiler header row has an unknown exact schema")
        observed = row["observation"]
        aliases = row["compiler_paths"]
        body = _bound(row["artifact"], reader)
        if (
            set(observed) != {"path", "name", "sha256", "bytes"}
            or observed["path"] in physical_names
            or observed["name"] != Path(observed["path"]).name
            or observed["sha256"] != body.sha256
            or not 0 < len(body.content) == observed["bytes"] <= 8 * 1024 * 1024
            or not isinstance(aliases, list)
            or not aliases
            or len(set(aliases)) != len(aliases)
            or any(not Path(name).is_absolute() or name in names for name in aliases)
            or _bound(entry["artifact"], reader).content != body.content
            or entry["observation"]["sha256"] != body.sha256
        ):
            raise ValueError("loader selected header body/name/aliases differ from actual complete consumed bytes")
        names.update(aliases)
        physical_names.add(observed["path"])
        total += len(body.content)
        if total > 128 * 1024 * 1024:
            raise ValueError("loader complete selected header bodies exceed aggregate ceiling")
    if names != selected_names or c_path not in names:
        raise ValueError("loader retained header names omit or add actual compiler-selected dependencies")
    return raw, library.content
