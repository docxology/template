"""Compile the one Source-owned Linux auditor through the actual native ToolAPI.

The resulting capability retains its genuine live producer and actual compiler
observation. JSON, a caller-selected shared object or a hash cannot construct it.
"""

from __future__ import annotations

import hashlib
import os
import platform
import shlex
import struct
import sys
from pathlib import Path
from typing import Any

from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, file_observation
from infrastructure.reporting.native_tool_producer import NativeProducerOperation, current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SOURCE = "infrastructure/reporting/native_loader_assets/linux_audit.c"
_KEY = object()
FLAGS = (
    "-std=c11",
    "-O2",
    "-shared",
    "-fPIC",
    "-nostdlib",
    "-nodefaultlibs",
    "-ffreestanding",
    "-fno-builtin",
    "-fno-stack-protector",
    "-fvisibility=default",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-Wl,-z,defs",
    "-Wl,-z,relro",
    "-Wl,-z,now",
    "-Wl,-z,noexecstack",
)


def elf_segments(content: bytes) -> list[tuple[int, int, int, int, int]]:
    """Decode the complete fixed 64-bit little-endian ELF PT_LOAD roster."""
    if len(content) < 64 or content[:7] != b"\x7fELF\x02\x01\x01":
        raise ValueError("loader body does not use the reviewed ELF64 little-endian ABI")
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", content)
    offset, width, count = header[5], header[9], header[10]
    if width != 56 or not 0 < count <= 128 or offset > 4 * 1024 * 1024 or offset + width * count > len(content):
        raise ValueError("loader complete program header table is absent or unbounded")
    rows = []
    for index in range(count):
        kind, flags, file_offset, address, _, file_size, memory_size, _ = struct.unpack_from(
            "<II6Q", content, offset + index * width
        )
        if kind == 2:
            if file_offset + file_size > len(content) or file_size % 16:
                raise ValueError("loader dynamic table exceeds its complete backing body")
            for cursor in range(file_offset, file_offset + file_size, 16):
                tag, value = struct.unpack_from("<qQ", content, cursor)
                if tag == 0:
                    break
                if tag == 22 or tag == 30 and value & 4:
                    raise ValueError("loader executable body requires unsupported text relocations")
        if kind == 1:
            if file_size > memory_size or file_offset + file_size > len(content) or address + memory_size > 2**64 - 1:
                raise ValueError("loader body program segment exceeds its physical file/ABI bounds")
            rows.append((address, memory_size, file_offset, file_size, flags))
    if not rows:
        raise ValueError("loader body has no complete executable-image load roster")
    return rows


def _auditor_abi(content: bytes, *, architecture: str | None = None) -> None:
    elf_segments(content)
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", content)
    architecture = platform.machine() if architecture is None else architecture
    if architecture not in {"x86_64", "aarch64"}:
        raise ValueError("Source auditor requires a reviewed actual ELF architecture")
    expected_machine = 62 if architecture == "x86_64" else 183
    if header[1:3] != (3, expected_machine):
        raise ValueError("Source auditor output differs from this actual host ELF ABI")
    offset, width, count = header[5], header[9], header[10]
    for index in range(count):
        kind, flags, position, _, _, size, _, _ = struct.unpack_from("<II6Q", content, offset + index * width)
        if kind == 2:
            if size % 16:
                raise ValueError("auditor dynamic table has an unknown ABI")
            for cursor in range(position, position + size, 16):
                tag, _ = struct.unpack_from("<qQ", content, cursor)
                if tag == 0:
                    break
                if tag in {1, 22}:
                    raise ValueError("Source auditor must have no audit-namespace dependencies or text relocations")
        if kind == 0x6474E551 and flags & 1:
            raise ValueError("Source auditor cannot request an executable stack")


class CompiledNativeLoader:
    """Actual fixed Source/compiler output held by its genuine live owner."""

    def __init__(
        self, owner: NativeProducerOperation, directory: Path, binding: dict[str, str], library: Path, *, key: object
    ):
        if key is not _KEY:
            raise ValueError("compiled loader requires the fixed actual Source compiler route")
        self.owner, self.directory, self.binding, self.library = owner, directory, binding, library
        self.owner_pid = os.getpid()
        self.observation = file_observation(library)
        from infrastructure.reporting.native_tool_process import _physical_identity

        self.identity = _physical_identity(library)

    def verify(self, *, deadline: float) -> None:
        self.owner.verify(
            SnapshotReader(self.owner.source.bindings.current_root), run_id=self.owner.run_id, deadline=deadline
        )
        from infrastructure.reporting.native_tool_process import _physical_identity

        if (
            self.owner_pid != os.getpid()
            or file_observation(self.library) != self.observation
            or _physical_identity(self.library) != self.identity
        ):
            raise ValueError("actual Source compiler output changed before consuming process admission")
        remaining(deadline)


def compile_native_loader(runtime: CitationRuntime) -> CompiledNativeLoader:
    """Use exact Source asset/flags, actual compiler/header inputs, one clock."""
    if (
        not sys.platform.startswith("linux")
        or sys.byteorder != "little"
        or platform.machine() not in {"x86_64", "aarch64"}
    ):
        raise ValueError("complete loader qualification currently requires the reviewed glibc Linux host")
    refused = {
        "CPATH",
        "C_INCLUDE_PATH",
        "CPLUS_INCLUDE_PATH",
        "OBJC_INCLUDE_PATH",
        "LIBRARY_PATH",
        "GCC_EXEC_PREFIX",
        "COMPILER_PATH",
        "LD_AUDIT",
        "LD_PRELOAD",
    }
    if refused & set(runtime.env):
        raise ValueError("fixed loader compiler refuses ambient search-path/code-injection settings")
    owner = current_native_producer_operation()
    if type(owner) is not NativeProducerOperation:
        raise ValueError("loader compilation needs this process's genuine independently admitted Source owner")
    reader = SnapshotReader(runtime.root, native_producer_operation=owner)
    owner.verify(reader, run_id=runtime.run_id, deadline=runtime.deadline)
    source = owner.source.current_source_reader.read(SOURCE)
    if owner.source.reference.read(SOURCE) != source.content:
        raise ValueError("fixed loader C body differs from the independently held original Source")
    c_input = runtime.freeze("source-loader-audit.c", source.content)
    output = runtime.directory / "source-loader-audit.so"
    if output.exists() or output.is_symlink() or ":" in str(output) or " " in str(output):
        raise ValueError("fixed loader output must be fresh and unambiguous in the glibc audit list")
    runtime.tool(
        "cc",
        ["-std=c11", "-M", "-MT", "source-loader-audit.o", str(c_input)],
        "loader-header-selection",
        input_paths=(c_input,),
    )
    dependency = runtime.tools[-1]
    raw = runtime.read(runtime.directory / "loader-header-selection.stdout.bin").decode("utf-8", "strict")
    tokens = shlex.split(raw.replace("\\\n", ""), posix=True)
    if not tokens or tokens.pop(0) != "source-loader-audit.o:" or not 0 < len(tokens) <= 1024:
        raise ValueError("actual fixed compiler header roster is absent, ambiguous or unbounded")
    nominated_headers: dict[Path, list[str]] = {}
    for value in tokens:
        selected = Path(value)
        selected = (selected if selected.is_absolute() else runtime.directory / selected).absolute()
        aliases = nominated_headers.setdefault(selected.resolve(strict=True), [])
        if str(selected) not in aliases:
            aliases.append(str(selected))
    headers = tuple(nominated_headers)
    observed = []
    frozen_headers = []
    total = 0
    for index, header in enumerate(headers):
        remaining(runtime.deadline)
        if not 0 < header.stat().st_size <= 8 * 1024 * 1024:
            raise ValueError("actual fixed compiler header exceeds its admitted body bound")
        row = file_observation(header)
        total += row["bytes"]
        if total > 128 * 1024 * 1024:
            raise ValueError("actual fixed compiler header/body aggregate exceeds its finite bound")
        with header.open("rb") as stream:
            content = stream.read(8 * 1024 * 1024 + 1)
        if len(content) > 8 * 1024 * 1024 or hashlib.sha256(content).hexdigest() != row["sha256"]:
            raise ValueError("actual fixed compiler header changed or exceeds its admitted bound")
        held = runtime.freeze(f"loader-header-{index:04d}.input", content)
        frozen_headers.append(held)
        observed.append(
            {
                "observation": row,
                "compiler_paths": nominated_headers[header],
                "artifact": {"path": held.relative_to(runtime.root).as_posix(), "sha256": row["sha256"]},
            }
        )
    flags = [*FLAGS, *(["-mno-outline-atomics"] if platform.machine() == "aarch64" else [])]
    runtime.tool(
        "cc",
        [*flags, str(c_input), "-o", str(output)],
        "loader-source-compilation",
        input_paths=(c_input, *frozen_headers),
    )
    compilation = runtime.tools[-1]
    for row, header in zip(observed, headers, strict=True):
        if row["observation"] != file_observation(header):
            raise ValueError("fixed compiler's independently selected header changed during actual compilation")
    for tool in (dependency, compilation):
        tool_record = reader.read(tool["path"])
        owner.validate_tool(tool, tool_record.json_object(), reader, run_id=runtime.run_id)
        if tool_record.json_object()["original_exit_code"] != 0:
            raise ValueError("fixed Source loader compiler/header-selection command did not actually succeed")
    with output.open("rb") as stream:
        output_bytes = stream.read(8 * 1024 * 1024 + 1)
    if not 0 < len(output_bytes) <= 8 * 1024 * 1024:
        raise ValueError("fixed Source auditor compiled body exceeds its admitted ceiling")
    _auditor_abi(output_bytes)
    library = runtime.freeze("source-loader-audit-held.so", output_bytes)
    payload: dict[str, Any] = {
        "schema_version": "template-source-native-loader-compilation-v1",
        "run_id": runtime.run_id,
        "source_binding": [owner.source.reference.commit, owner.source.reference.source_identity],
        "source": {"path": SOURCE, "sha256": source.sha256},
        "compiler_header_selection": dependency,
        "compiler": compilation,
        "headers": observed,
        "flags": flags,
        "library": {
            "path": library.relative_to(runtime.root).as_posix(),
            "sha256": hashlib.sha256(output_bytes).hexdigest(),
        },
        "platform": "Linux",
        "architecture": platform.machine(),
        "audit_abi": 2,
        "audit_namespace_dependencies": [],
    }
    from infrastructure.reporting.native_tool_process import _physical_identity

    payload["library_identity"] = _physical_identity(library)
    binding = write_json(runtime.root, runtime.directory / "source-loader-compilation.json", payload)
    result = CompiledNativeLoader(owner, runtime.directory, binding, library, key=_KEY)
    result.verify(deadline=runtime.deadline)
    return result
