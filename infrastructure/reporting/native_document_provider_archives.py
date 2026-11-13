"""Bounded document-provider tar.xz DATA decoding; no native or Source authority."""

from __future__ import annotations

import hashlib
import lzma
import math
import tarfile
import time
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any

MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_EXECUTABLE_BYTES = 512 * 1024 * 1024
_MAX_PAYLOAD_BYTES = 1024 * 1024 * 1024
_MAX_MEMBERS = 1000
_XZ_MEMORY_BYTES = 128 * 1024 * 1024
_MAX_METADATA_READ_BYTES = 8 * 1024 * 1024
_CHUNK_BYTES = 65536


def _remaining(deadline: float) -> None:
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("document provider archive requires an original finite monotonic deadline")
    if deadline <= time.monotonic():
        raise TimeoutError("document provider archive original deadline exhausted")


def _uncompressed(archive: bytes, *, deadline: float) -> bytes:
    """Bound all decompressed bytes before tarfile consumes internal metadata."""
    _remaining(deadline)
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=_XZ_MEMORY_BYTES)
    chunks: list[bytes] = []
    cursor = size = 0
    while not decoder.eof:
        _remaining(deadline)
        if decoder.needs_input:
            if cursor == len(archive):
                raise ValueError("document provider XZ stream is truncated")
            content = archive[cursor : cursor + _CHUNK_BYTES]
            cursor += len(content)
        else:
            content = b""
        chunk = decoder.decompress(content, max_length=_CHUNK_BYTES)
        _remaining(deadline)
        size += len(chunk)
        if size > _MAX_PAYLOAD_BYTES:
            raise ValueError("document provider complete uncompressed stream exceeds its finite bound")
        chunks.append(chunk)
    if decoder.unused_data or cursor != len(archive):
        raise ValueError("document provider archive has unsupported concatenated or trailing XZ streams")
    if not size:
        raise ValueError("document provider archive has an empty uncompressed stream")
    result = b"".join(chunks)
    _remaining(deadline)
    return result


class _BoundedTarBytes(BytesIO):
    """Keep tarfile's internal longname/PAX/sparse reads on the original clock."""

    def __init__(self, content: bytes, deadline: float) -> None:
        self.deadline = deadline
        super().__init__(content)

    def read(self, size: int | None = -1) -> bytes:
        _remaining(self.deadline)
        if type(size) is not int or not 0 <= size <= _MAX_METADATA_READ_BYTES:
            raise ValueError("document provider tar parser requested unsupported or excessive metadata bytes")
        result = super().read(size)
        _remaining(self.deadline)
        return result

    def seek(self, offset: int, whence: int = 0) -> int:
        _remaining(self.deadline)
        result = super().seek(offset, whence)
        _remaining(self.deadline)
        return result


def provider_archive_member(archive: bytes, pin: dict[str, Any], *, deadline: float) -> tuple[dict[str, Any], bytes]:
    """Decode complete bounded tar.xz against a selected provider's exact pins.

    Source builds pin the executable body, not producer compression or receipts.
    Official archives pin all compressed bytes as well as member correspondence.
    The caller separately authenticates Source, build provenance and execution.
    """
    _remaining(deadline)
    if not 0 < len(archive) <= MAX_ARCHIVE_BYTES:
        raise ValueError("document provider archive exceeds its finite compressed byte bound")
    kind = pin["kind"]
    if kind == "official-archives":
        if (
            pin["format"] != "tar.xz"
            or len(archive) != pin["archive_bytes"]
            or hashlib.sha256(archive).hexdigest() != pin["archive_sha256"]
        ):
            raise ValueError("official document provider archive bytes differ from the actual current Source pin")
    elif kind != "nix-source-build":
        raise ValueError("document archive has no admitted Source-selected provider kind")
    selected = None
    selected_data = None
    names = set()
    payload_bytes = count = 0
    complete = _uncompressed(archive, deadline=deadline)
    with _BoundedTarBytes(complete, deadline) as stream, tarfile.open(fileobj=stream, mode="r:") as members:
        for member in members:
            _remaining(deadline)
            count += 1
            name = PurePosixPath(member.name)
            if count > _MAX_MEMBERS or name.is_absolute() or ".." in name.parts or not name.parts:
                raise ValueError("document provider archive has an unsafe or excessive complete member roster")
            label = name.as_posix()
            if label in names or member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise ValueError("document provider archive has duplicate, linked or unsupported member types")
            names.add(label)
            if member.isfile():
                payload_bytes += member.size
                if not 0 <= member.size <= MAX_EXECUTABLE_BYTES or payload_bytes > _MAX_PAYLOAD_BYTES:
                    raise ValueError("document provider archive exceeds its finite uncompressed payload bound")
            if label == pin["member"]:
                if selected is not None or not member.isfile() or member.mode & 0o111 == 0:
                    raise ValueError("document provider Source member is not one real executable file")
                member_stream = members.extractfile(member)
                if member_stream is None:
                    raise ValueError("document provider archive cannot read its selected Source member")
                chunks, size = [], 0
                with member_stream:
                    while chunk := member_stream.read(_CHUNK_BYTES):
                        _remaining(deadline)
                        size += len(chunk)
                        if size > MAX_EXECUTABLE_BYTES:
                            raise ValueError("document provider extracted executable exceeds its native byte bound")
                        chunks.append(chunk)
                selected_data = b"".join(chunks)
                if size != member.size or not selected_data:
                    raise ValueError("document provider extracted Source member is truncated or empty")
                selected = {
                    "name": member.name,
                    "canonical_name": label,
                    "mode": member.mode,
                    "bytes": size,
                    "sha256": hashlib.sha256(selected_data).hexdigest(),
                }
    if selected is None or selected_data is None:
        raise ValueError("document provider archive omitted its exact Source-selected executable")
    if kind == "nix-source-build" and (
        count != 1 or selected["bytes"] != pin["binary_bytes"] or selected["sha256"] != pin["binary_sha256"]
    ):
        raise ValueError("source-built document archive differs from its exact Source-pinned single executable body")
    _remaining(deadline)
    return {
        **selected,
        "archive_members": count,
        "uncompressed_payload_bytes": payload_bytes,
        "complete_uncompressed_archive_bytes": len(complete),
    }, selected_data
