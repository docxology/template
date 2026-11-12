"""Bounded physical ELF preparation checks, not loaded-process acceptance."""

from __future__ import annotations

import os
import re
import stat
import struct
from pathlib import Path

from infrastructure.core.pipeline.fingerprint_files import anchored_parent, observation
from infrastructure.reporting.native_document_provider_contracts import MAX_BINARY_BYTES


def read_physical_file(path: Path, *, limit: int, executable: bool = False) -> bytes:
    """Read one complete bounded real body with held no-follow ancestry."""
    if type(limit) is not int or limit <= 0:
        raise ValueError("document physical read requires a positive finite bound")
    path = path.absolute()
    with anchored_parent(path) as parent:
        if parent is None:
            raise FileNotFoundError(path)
        before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        if (
            not stat.S_ISREG(before.st_mode)
            or not 0 < before.st_size <= limit
            or before.st_nlink < 1
            or (executable and not before.st_mode & 0o111)
        ):
            raise ValueError("document body is not a bounded real regular executable/file")
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            expected = observation(before)
            if observation(os.fstat(descriptor)) != expected:
                raise ValueError("document physical body changed before reading")
            with os.fdopen(descriptor, "rb", closefd=False) as source:
                content = source.read(limit + 1)
            if (
                len(content) != before.st_size
                or observation(os.fstat(descriptor)) != expected
                or observation(os.stat(path.name, dir_fd=parent, follow_symlinks=False)) != expected
            ):
                raise ValueError("document physical body changed during reading")
        finally:
            os.close(descriptor)
    return content


def _elf_headers(content: bytes, machine: str) -> list[tuple[int, ...]]:
    machines = {"x86_64": 62, "amd64": 62, "aarch64": 183, "arm64": 183}
    if machine not in machines:
        raise ValueError("document ELF check has no reviewed machine ABI")
    if len(content) < 64 or content[:7] != b"\x7fELF\x02\x01\x01":
        raise ValueError("document executable is not an actual ELF64 little-endian body")
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", content)
    if header[1] not in {2, 3} or header[2] != machines[machine] or header[3] != 1 or header[8] != 64:
        raise ValueError("document executable has an unsupported ELF type or machine ABI")
    offset, size, count = header[5], header[9], header[10]
    if size != 56 or not 0 < count <= 128 or offset < 64 or offset + size * count > len(content):
        raise ValueError("document executable program headers are absent, truncated or excessive")
    result = [struct.unpack_from("<IIQQQQQQ", content, offset + size * index) for index in range(count)]
    for row in result:
        if row[2] > len(content) or row[5] > len(content) - row[2]:
            raise ValueError("document executable program segment exceeds its complete body")
    if not any(row[0] == 1 and row[1] & 1 and row[5] > 0 for row in result):
        raise ValueError("document ELF lacks an actual executable load segment")
    return result


def glibc_interpreter(content: bytes, *, machine: str) -> str:
    """Decode the single canonical glibc PT_INTERP from complete ELF bytes."""
    rows = [row for row in _elf_headers(content, machine) if row[0] == 3]
    if len(rows) != 1:
        raise ValueError("document executable requires one real glibc PT_INTERP; static ELF is unsupported")
    row = rows[0]
    raw = content[row[2] : row[2] + row[5]]
    if not 2 <= len(raw) <= 4096 or not raw.endswith(b"\0") or b"\0" in raw[:-1]:
        raise ValueError("document executable PT_INTERP is malformed or excessive")
    try:
        interpreter = raw[:-1].decode("ascii")
    except UnicodeError as error:
        raise ValueError("document executable PT_INTERP is not an ASCII loader path") from error
    architecture = "x86_64" if machine in {"x86_64", "amd64"} else "aarch64"
    loader_name = "ld-linux-x86-64.so.2" if architecture == "x86_64" else "ld-linux-aarch64.so.1"
    if (
        re.fullmatch(
            rf"(?:/lib64|/lib|/lib/{architecture}-linux-gnu|"
            r"/nix/store/[0-9abcdfghijklmnpqrsvwxyz]{32}-glibc-[A-Za-z0-9+._-]+/lib)" + "/" + re.escape(loader_name),
            interpreter,
        )
        is None
    ):
        raise ValueError("document executable PT_INTERP is not a reviewed glibc loader (musl is unsupported)")
    return interpreter


def require_glibc_executable(path: Path, *, machine: str) -> str:
    """Require an unchanged real ELF and an installed real glibc interpreter."""
    content = read_physical_file(path.resolve(strict=True), limit=MAX_BINARY_BYTES, executable=True)
    interpreter = glibc_interpreter(content, machine=machine)
    loader = Path(interpreter).resolve(strict=True)
    loader_body = read_physical_file(loader, limit=16 * 1024 * 1024, executable=True)
    if any(row[0] == 3 for row in _elf_headers(loader_body, machine)) or b"GLIBC_PRIVATE\0" not in loader_body:
        raise ValueError("document executable PT_INTERP does not resolve to an actual glibc ELF loader")
    return interpreter
