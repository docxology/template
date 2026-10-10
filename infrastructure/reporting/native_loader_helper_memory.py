"""Observe only the Source auditor's actual RX bytes in the consuming child.

The caller must already hold the real live ToolAPI process and compiler owner.
Ordinary proc-mem denial is a refusal; this route never attaches, stops or
changes a process, adjusts security settings or chooses a caller-supplied PID.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, TYPE_CHECKING

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_loader_build import elf_segments
from infrastructure.reporting.native_loader_protocol import CHUNK
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_loader_build import CompiledNativeLoader
    from infrastructure.reporting.native_tool_process import NativeLiveToolProcess

SCHEMA = "template-source-auditor-mapped-code-v1"


def helper_ranges(
    rows: list[dict[str, Any]], identity: dict[str, int], content: bytes, *, page: int, deadline: float
) -> tuple[int, list[dict[str, int]]]:
    """Derive every auditor RX range from complete ELF and actual kernel maps."""
    if page not in {4096, 16384, 65536}:
        raise ValueError("auditor memory uses an unsupported actual kernel page ABI")
    selected = [
        row
        for row in rows
        if "x" in row["protection"] and row["device"] == identity["device"] and row["inode"] == identity["inode"]
    ]
    expected = [segment for segment in elf_segments(content) if segment[4] & 1]
    if not selected or len(selected) != len(expected):
        raise ValueError("auditor actual kernel maps omit or add an executable Source segment")
    ranges, base = [], None
    for address, memory, offset, size, flags in expected:
        remaining(deadline)
        if flags & 2 or size != memory or size <= 0:
            raise ValueError("auditor Source executable segment uses unsupported writable/zero-filled code")
        matches = [row for row in selected if row["offset"] == offset // page * page]
        if len(matches) != 1:
            raise ValueError("auditor actual executable mapping is ambiguous by ELF file offset")
        row = matches[0]
        current_base = row["low"] - address // page * page
        if (
            row["protection"] != "r-xp"
            or row["high"] != current_base + (address + size + page - 1) // page * page
            or base is not None
            and base != current_base
        ):
            raise ValueError("auditor actual map exceeds its exact Source ELF range/permissions/load base")
        base = current_base
        ranges.append({"address": base + address, "file_offset": offset, "bytes": size})
        selected.remove(row)
    if base is None or selected:
        raise ValueError("auditor actual full executable-map cohort cannot be established")
    return base, ranges


def observe_helper_memory(
    live: NativeLiveToolProcess,
    compiled: CompiledNativeLoader,
    rows: list[dict[str, Any]],
    *,
    page: int,
    deadline: float,
) -> dict[str, Any]:
    """Read the blocked actual Popen child using ordinary parent proc access."""
    from infrastructure.reporting.native_loader_build import CompiledNativeLoader
    from infrastructure.reporting.native_tool_process import NativeLiveToolProcess

    if type(live) is not NativeLiveToolProcess or type(compiled) is not CompiledNativeLoader:
        raise ValueError("auditor memory needs the real fixed compiler and live original ToolAPI")
    live.verify_live()
    compiled.verify(deadline=deadline)
    content = (
        SnapshotReader(compiled.owner.source.bindings.current_root)
        .read(
            compiled.library.relative_to(compiled.owner.source.bindings.current_root).as_posix(),
            max_bytes=8 * 1024 * 1024,
        )
        .content
    )
    base, ranges = helper_ranges(rows, compiled.identity, content, page=page, deadline=deadline)
    # The kernel path comes solely from the genuine live Popen capability. No
    # pid from JSON/environment/caller DATA is accepted here.
    try:
        descriptor = os.open(Path("/proc") / str(live.pid) / "mem", os.O_RDONLY | os.O_CLOEXEC)
    except OSError as error:
        raise ValueError("ordinary Linux parent proc-mem access denied auditor mapped-byte qualification") from error
    observed = []
    try:
        for selected in ranges:
            digest, offset = hashlib.sha256(), 0
            while offset < selected["bytes"]:
                remaining(deadline)
                live.verify_live()
                count = min(CHUNK, selected["bytes"] - offset)
                piece = os.pread(descriptor, count, selected["address"] + offset)
                start = selected["file_offset"] + offset
                if len(piece) != count or piece != content[start : start + count]:
                    raise ValueError("auditor actual consuming-process code differs from fixed compiled Source bytes")
                digest.update(piece)
                offset += count
            observed.append({**selected, "sha256": digest.hexdigest()})
    finally:
        os.close(descriptor)
    live.verify_live()
    compiled.verify(deadline=deadline)
    return {
        "schema_version": SCHEMA,
        "pid": live.pid,
        "compiler": compiled.binding,
        "load_base": base,
        "segments": observed,
    }


def validate_helper_memory_data(
    raw: dict[str, Any],
    rows: list[dict[str, Any]],
    compiler: dict[str, Any],
    content: bytes,
    *,
    binding: dict[str, str],
    pid: int,
    page: int,
    deadline: float,
) -> None:
    """Reconstruct exact Source ranges/byte commitments under enclosing custody."""
    base, ranges = helper_ranges(rows, compiler["library_identity"], content, page=page, deadline=deadline)
    expected = [
        {
            **item,
            "sha256": hashlib.sha256(content[item["file_offset"] : item["file_offset"] + item["bytes"]]).hexdigest(),
        }
        for item in ranges
    ]
    if raw != {"schema_version": SCHEMA, "pid": pid, "compiler": binding, "load_base": base, "segments": expected}:
        raise ValueError("auditor original mapped bytes differ from independently reconstructed complete Source code")


CONSUMER_SCHEMA = "template-consumer-boundary-mapped-code-v1"


def observe_consumer_memory(
    live: NativeLiveToolProcess,
    images: dict[int, dict[str, Any]],
    descriptors: dict[int, int],
    rows: list[dict[str, Any]],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Re-read every current Source-nominated RX byte at one blocked boundary."""
    from infrastructure.reporting.native_loader_protocol import identity, mapped_segment
    from infrastructure.reporting.native_tool_process import NativeLiveToolProcess

    if type(live) is not NativeLiveToolProcess:
        raise ValueError("consumer memory needs the actual original live Popen capability")
    live.verify_live()
    try:
        memory = os.open(Path("/proc") / str(live.pid) / "mem", os.O_RDONLY | os.O_CLOEXEC)
    except OSError as error:
        raise ValueError("ordinary parent proc-mem access denied consumer boundary byte qualification") from error
    observed = []
    try:
        for object_id, image in images.items():
            remaining(deadline)
            body = image["body"]
            descriptor = descriptors.get(object_id)
            if body is not None and (descriptor is None or identity(descriptor) != body["identity"]):
                raise ValueError("consumer boundary lost its actual retained original backing descriptor")
            code = []
            for segment in image["segments"]:
                if not segment["flags"] & 1:
                    continue
                mapped_segment(segment, rows, body)
                digest, offset = hashlib.sha256(), 0
                while offset < segment["file_bytes"]:
                    remaining(deadline)
                    live.verify_live()
                    count = min(CHUNK, segment["file_bytes"] - offset)
                    piece = os.pread(memory, count, segment["address"] + offset)
                    if (
                        len(piece) != count
                        or descriptor is not None
                        and piece != os.pread(descriptor, count, segment["file_offset"] + offset)
                    ):
                        raise ValueError("consumer persistent RX byte drift differs from its original backing body")
                    digest.update(piece)
                    offset += count
                if digest.hexdigest() != segment["mapped_code"]["sha256"]:
                    raise ValueError("consumer persistent RX byte drift differs from original mapped-code commitment")
                code.append({"address": segment["address"], "bytes": offset, "sha256": digest.hexdigest()})
            if descriptor is not None and identity(descriptor) != body["identity"]:
                raise ValueError("consumer boundary backing descriptor changed during actual memory read")
            observed.append({"object_id": object_id, "original_open_sequence": image["sequence"], "segments": code})
    finally:
        os.close(memory)
    live.verify_live()
    return {"schema_version": CONSUMER_SCHEMA, "pid": live.pid, "images": observed}


def validate_consumer_memory_data(
    raw: dict[str, Any], images: dict[int, dict[str, Any]], *, pid: int, deadline: float
) -> None:
    """Reconstruct exact original RX cohort under separately authenticated custody."""
    expected = []
    for object_id, image in images.items():
        remaining(deadline)
        segments = [
            {"address": segment["address"], "bytes": segment["file_bytes"], "sha256": segment["mapped_code"]["sha256"]}
            for segment in image["segments"]
            if segment["flags"] & 1
        ]
        expected.append({"object_id": object_id, "original_open_sequence": image["sequence"], "segments": segments})
    if raw != {"schema_version": CONSUMER_SCHEMA, "pid": pid, "images": expected}:
        raise ValueError("consumer original boundary memory differs from its complete Source-nominated RX cohort")
