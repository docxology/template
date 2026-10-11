"""Independent loader DATA reconstruction under separately held original custody.

Only authenticate_original_native_artifact supplies authority. Body hashes,
callback records and this bounded parser never create an original operation.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_loader_build import SOURCE, elf_segments
from infrastructure.reporting.native_loader_observation import SCHEMA
from infrastructure.reporting.native_loader_maps import census_images, executable_census, parse_maps
from infrastructure.reporting.native_loader_protocol import mapped_segment
from infrastructure.reporting.native_loader_protocol import CHUNK, MAX_EVENTS, MAX_TOTAL, chunks_content
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

MODULES = (
    "reporting/native_tool_process.py",
    "reporting/native_tool_process_inputs.py",
    "reporting/native_pdf_citation_runtime.py",
    "reporting/native_loader_build.py",
    "reporting/native_loader_protocol.py",
    "reporting/native_loader_observation.py",
    "reporting/native_loader_maps.py",
    "reporting/native_loader_qualification.py",
    "reporting/native_loader_compilation_replay.py",
    "reporting/native_loader_helper_memory.py",
    "reporting/native_environment_custody.py",
)


def _bound(value: object, reader: SnapshotReader) -> Any:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError("loader graph requires one exact retained artifact binding")
    selected = reader.read(value["path"])
    if selected.sha256 != value["sha256"]:
        raise ValueError("loader artifact differs from its exact original bytes")
    return selected


def validate_native_loader_data(
    native: dict[str, Any], reader: SnapshotReader, *, original_deadline: float, original_completion: float
) -> dict[str, Any]:
    """Reconstruct exact bodies/ELF segments/lifecycle, a DATA predicate only."""
    if reader.native_operation is not None:
        from infrastructure.reporting.native_format_joint_source import require_native_operation

        deadline = require_native_operation(reader).deadline
    else:
        deadline = original_deadline
    remaining(deadline)
    selected = _bound(native.get("loader_lifecycle"), reader)
    raw = selected.json_object()
    if not isinstance(raw, dict):
        raise ValueError("loader lifecycle must be a retained JSON object")
    fields = {
        "schema_version",
        "run_id",
        "source_binding",
        "compiler",
        "purpose",
        "owner_pid",
        "consuming_process",
        "command",
        "original_deadline_monotonic",
        "token_sha256",
        "environment_injections",
        "events",
        "opened",
        "closed",
        "complete_callbacks",
        "channel_eof",
        "original_exit_code",
        "resident_terminal",
        "scope_limit",
    }
    if (
        set(raw) != fields
        or raw.get("schema_version") != SCHEMA
        or raw.get("owner_pid") != native.get("owner_pid")
        or raw.get("consuming_process", {}).get("pid") != native.get("pid")
        or raw.get("consuming_process", {}).get("ppid") != native.get("owner_pid")
        or raw.get("command") != native.get("command")
        or raw.get("original_deadline_monotonic") != native.get("original_deadline_monotonic")
        or raw.get("original_exit_code") != native.get("original_exit_code")
        or raw.get("original_exit_code") != 0
        or raw.get("complete_callbacks") is not True
        or raw.get("channel_eof") is not True
        or raw.get("scope_limit") != "this-actual-consuming-process-callback-and-kernel-map-cohort"
        or raw.get("consuming_process", {}).get("platform") != "Linux"
        or not isinstance(raw.get("token_sha256"), str)
        or len(raw["token_sha256"]) != 64
        or any(char not in "0123456789abcdef" for char in raw["token_sha256"])
    ):
        raise ValueError("loader lifecycle differs from its genuine original consuming ToolAPI/OS/clock")
    from infrastructure.reporting.native_loader_compilation_replay import validate_compilation_data

    compiler, library_content = validate_compilation_data(
        raw["compiler"],
        reader,
        native=native,
        source_binding=raw["source_binding"],
        run_id=raw["run_id"],
        original_deadline=original_deadline,
        original_completion=original_completion,
    )
    events = raw.get("events")
    if not isinstance(events, list) or not 0 < len(events) <= MAX_EVENTS or events[0].get("kind") != "hello":
        raise ValueError("loader complete original callback cohort is absent or unbounded")
    active, opened, closed, previous, total = {}, {}, [], 0, 0
    preinit = False
    for sequence, event in enumerate(events, 1):
        remaining(deadline)
        if (
            event.get("sequence") != sequence
            or event.get("pid") != native["pid"]
            or type(event.get("monotonic_ns")) is not int
        ):
            raise ValueError("loader callback original sequence/kernel PID/time differs")
        stamp = event["monotonic_ns"] / 1_000_000_000
        if (
            not previous <= stamp < native["original_deadline_monotonic"] <= original_deadline
            or stamp > original_completion
        ):
            raise ValueError("loader callback did not finish within its genuine original operation clock")
        previous = stamp
        kind, object_id = event["kind"], event["id"]
        rows = None
        if "kernel_maps" in event:
            mapping = event["kernel_maps"]
            observed = reader.read(mapping["path"], max_bytes=CHUNK)
            if observed.sha256 != mapping["sha256"] or len(observed.content) != mapping["bytes"]:
                raise ValueError("loader original kernel mapping differs from its exact retained bytes")
            rows = parse_maps(observed.content, deadline=deadline)
        common = {"sequence", "pid", "monotonic_ns", "kind", "id", "base", "namespace"}
        extra = {
            "open": {"path_label", "body", "segments", "kernel_maps"},
            "close": {"original_open_sequence", "kernel_maps", "consumer_mapped_code"},
            "preinit": {
                "kernel_maps",
                "complete_executable_map_census",
                "source_auditor_mapped_code",
                "consumer_mapped_code",
            },
            "activity": (
                {"kernel_maps", "complete_executable_map_census", "source_auditor_mapped_code", "consumer_mapped_code"}
                if preinit and event["base"] == 0
                else set()
            ),
            "hello": set(),
            "done": set(),
        }
        if kind not in extra or set(event) != common | extra[kind] or event["namespace"] != 0:
            raise ValueError("loader callback differs from its fixed exact Source API fieldset")
        if kind == "open":
            if object_id in opened or event["namespace"] != 0 or not isinstance(event["segments"], list):
                raise ValueError("loader original image was aliased/reopened or uses an unsupported namespace")
            backing = event["body"]
            content = None
            if backing is not None:
                if (
                    set(backing) != {"identity", "sha256", "bytes", "chunks"}
                    or backing["identity"]["size"] != backing["bytes"]
                ):
                    raise ValueError("loader actual original backing body has an unknown schema/identity")
                content = chunks_content(
                    {name: backing[name] for name in ("sha256", "bytes", "chunks")},
                    reader,
                    limit=512 * 1024 * 1024,
                    deadline=deadline,
                )
                expected = elf_segments(content)
                total += len(content)
                if total > MAX_TOTAL or len(expected) != len(event["segments"]):
                    raise ValueError("loader complete backing image cohort exceeds its bound or omits a PT_LOAD row")
            else:
                if event["path_label"] not in {"linux-vdso.so.1", "linux-vdso.so.2"}:
                    raise ValueError("loader bodyless image is not an explicitly kernel-provided vDSO")
                expected = None
            for index, segment in enumerate(event["segments"]):
                actual = (
                    segment["address"] - event["base"],
                    segment["memory_bytes"],
                    segment["file_offset"],
                    segment["file_bytes"],
                    segment["flags"],
                )
                if expected is not None and actual != expected[index]:
                    raise ValueError("loader original callback segment does not cover its actual full ELF body")
                if segment["flags"] & 1:
                    if rows is None:
                        raise ValueError("loader original executable segment lacks its actual kernel mapping")
                    mapped_segment(segment, rows, backing)
                code = segment["mapped_code"]
                if set(code) != {"sha256", "bytes", "chunks", "body_slice"} or code["bytes"] != (
                    segment["file_bytes"] if segment["flags"] & 1 else 0
                ):
                    raise ValueError("loader original mapped executable bytes have an unknown exact schema")
                if content is not None:
                    if code["chunks"] or code["body_slice"] != {
                        "offset": segment["file_offset"],
                        "bytes": code["bytes"],
                    }:
                        raise ValueError("loader file-backed mapped bytes differ from the complete retained body span")
                    physical = content[segment["file_offset"] : segment["file_offset"] + code["bytes"]]
                else:
                    if code["body_slice"] is not None:
                        raise ValueError("kernel-only loader mapped bytes cannot claim a physical backing file")
                    physical = chunks_content(
                        {name: code[name] for name in ("sha256", "bytes", "chunks")},
                        reader,
                        limit=128 * 1024 * 1024,
                        deadline=deadline,
                    )
                if hashlib.sha256(physical).hexdigest() != code["sha256"]:
                    raise ValueError(
                        "loader mapped executable observation differs from the independently held exact body"
                    )
            opened[object_id] = event
            active[object_id] = event
        elif kind == "close":
            if object_id not in active or event["original_open_sequence"] != active[object_id]["sequence"]:
                raise ValueError("loader original close lacks its one prior actual open")
            if rows is None:
                raise ValueError("loader original close omits its actual kernel mapping")
            for segment in active[object_id]["segments"]:
                if segment["flags"] & 1:
                    mapped_segment(segment, rows, active[object_id]["body"])
            from infrastructure.reporting.native_loader_helper_memory import validate_consumer_memory_data

            validate_consumer_memory_data(
                event["consumer_mapped_code"], {object_id: active[object_id]}, pid=native["pid"], deadline=deadline
            )
            del active[object_id]
            closed.append(object_id)
        elif kind == "preinit":
            if (
                preinit
                or not active
                or event.get("complete_executable_map_census", {}).get("schema_version")
                != "template-loader-kernel-executable-census-v1"
            ):
                raise ValueError("loader original preinit omitted its complete kernel executable map census")
            preinit = True
        elif kind == "done":
            if active or not preinit:
                raise ValueError("loader original terminal callback left an unclosed image")
        elif kind == "hello":
            if sequence != 1:
                raise ValueError("loader original initialization repeats")
        elif kind != "activity" or event["base"] not in {0, 1, 2}:
            raise ValueError("loader original callback has an unknown Source API kind")
        if kind == "preinit" or kind == "activity" and preinit and event["base"] == 0:
            if rows is None:
                raise ValueError("loader consistent lifecycle callback omits its complete raw kernel mapping")
            declared = event.get("complete_executable_map_census")
            if not isinstance(declared, dict):
                raise ValueError("loader consistent callback lacks its complete executable census")
            page = declared.get("page_bytes")
            if type(page) is not int:
                raise ValueError("loader complete executable census requires an integer page size")
            from infrastructure.reporting.native_loader_helper_memory import validate_helper_memory_data

            validate_helper_memory_data(
                event["source_auditor_mapped_code"],
                rows,
                compiler,
                library_content,
                binding=raw["compiler"],
                pid=native["pid"],
                page=page,
                deadline=deadline,
            )
            images = census_images(rows, opened, active, closed, deadline=deadline)
            from infrastructure.reporting.native_loader_helper_memory import validate_consumer_memory_data

            validate_consumer_memory_data(event["consumer_mapped_code"], images, pid=native["pid"], deadline=deadline)
            expected_census = executable_census(
                rows,
                images,
                helper_identity=compiler["library_identity"],
                compiler=raw["compiler"],
                page=page,
                deadline=deadline,
            )
            if declared != expected_census:
                raise ValueError("loader declared census differs from independently reconstructed every-map coverage")
    main = [event for event in opened.values() if event["path_label"] == "/proc/self/exe"]
    if (
        len(main) != 1
        or main[0]["body"] is None
        or main[0]["body"]["sha256"] != native["executable_observation_before"]["sha256"]
        or main[0]["body"]["identity"] != native["executable_identity_before"]
    ):
        raise ValueError("loader actual consuming main image differs from its directly nominated executable body")
    terminal = raw.get("resident_terminal")
    if (
        not preinit
        or raw["opened"] != list(opened)
        or raw["closed"] != closed
        or not isinstance(terminal, dict)
        or terminal.get("kind") != "actual-parent-Popen-signed-OS-reaping"
        or terminal.get("original_exit_code") != native["original_exit_code"]
        or terminal.get("resident_object_ids") != list(active)
        or type(terminal.get("observed_monotonic")) not in {float, int}
        or not math.isfinite(terminal["observed_monotonic"])
        or not previous <= terminal["observed_monotonic"] < native["original_deadline_monotonic"]
    ):
        raise ValueError("loader resident lifetime did not close through the actual original parent OS result")
    return raw


def replay_native_loader_original(
    tool_binding: dict[str, str], reader: SnapshotReader, *, run_id: str
) -> dict[str, Any]:
    """Require genuine external original+current Source before any reconstruction."""
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_tool_replay import authenticate_original_native_artifact

    operation = require_native_operation(reader)
    authority = authenticate_original_native_artifact(tool_binding, reader, run_id=run_id, required_sdk_modules=MODULES)
    tool = authority["event"].json_object()
    native = _bound(tool["native_process_artifact"], reader).json_object()
    raw = validate_native_loader_data(
        native,
        reader,
        original_deadline=authority["original"].original_deadline,
        original_completion=authority["original"].observed_completion,
    )
    compiler = _bound(raw["compiler"], reader).json_object()
    source = operation.source.current_source_reader.read(SOURCE)
    scope = authority["source"]["scope"]
    original = operation.originals.get(scope)
    if original is None or original.run_id != run_id:
        raise ValueError("loader consuming process lacks its exact externally held original host cohort")
    host = reader.read(original.process_relative).json_object()["host_before"]
    if host["system"] != "Linux" or host["machine"] != compiler["architecture"]:
        raise ValueError("loader ELF compiler/callback ABI differs from actual original host custody")
    if (
        operation.source.reference.read(SOURCE) != source.content
        or compiler["source"]["sha256"] != source.sha256
        or raw["source_binding"] != [operation.source.reference.commit, operation.source.reference.source_identity]
    ):
        raise ValueError("loader original native helper was not compiled from independently held exact current Source")
    operation.verify(reader)
    return raw
