"""Observe actual loaded Darwin framework code without inventing absent files.

The symbol, dyld image, Mach-O header and readable executable segment bytes are
observed in the current genuine process. This is a bounded loaded-code witness,
not admission of the complete dyld cache, its dependencies or shaping.
Only the Source-nominated CoreFoundation and CoreText function cohorts qualify.
"""

from __future__ import annotations

import ctypes
import hashlib
import math
import os
import struct
import sys
import time
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined

_FRAMEWORKS = {
    "CoreFoundation": (
        "CFStringCreateWithCString",
        "CFStringGetCString",
        "CFRelease",
        "CFURLGetFileSystemRepresentation",
    ),
    "CoreText": (
        "CTFontCreateWithName",
        "CTFontCopyPostScriptName",
        "CTFontCopyAttribute",
        "CTFontGetGlyphsForCharacters",
    ),
}
_MAXIMUM_IMAGE = 512 * 1024 * 1024


class _DlInfo(ctypes.Structure):
    _fields_ = [
        ("dli_fname", ctypes.c_char_p),
        ("dli_fbase", ctypes.c_void_p),
        ("dli_sname", ctypes.c_char_p),
        ("dli_saddr", ctypes.c_void_p),
    ]


def _clock(deadline: float) -> None:
    if type(deadline) not in {int, float} or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("Darwin loaded-image observation exhausted its original caller clock")


def _physical_file(path: Path, *, deadline: float) -> dict[str, Any]:
    """Preserve an absent nomination explicitly, never hash a replacement file."""
    _clock(deadline)
    try:
        selected = path.resolve(strict=True)
    except FileNotFoundError:
        return {"nominated_path": str(path), "physical_file_present": False}
    before = selected.stat()
    content = read_bytes_confined(selected.parent, selected, max_bytes=_MAXIMUM_IMAGE)
    after = selected.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
        "st_nlink",
    )
    if any(getattr(before, key) != getattr(after, key) for key in fields):
        raise ValueError("Darwin nominated physical framework changed during observation")
    _clock(deadline)
    return {
        "nominated_path": str(path),
        "physical_file_present": True,
        "physical_path": str(selected),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "metadata": {key: getattr(after, key) for key in fields},
    }


def _loaded_images(system: ctypes.CDLL, *, deadline: float) -> dict[int, str]:
    system._dyld_image_count.argtypes = []
    system._dyld_image_count.restype = ctypes.c_uint32
    system._dyld_get_image_header.argtypes = [ctypes.c_uint32]
    system._dyld_get_image_header.restype = ctypes.c_void_p
    system._dyld_get_image_name.argtypes = [ctypes.c_uint32]
    system._dyld_get_image_name.restype = ctypes.c_char_p
    count = int(system._dyld_image_count())
    if not 0 < count <= 32768:
        raise ValueError("Darwin loaded-image inventory exceeds its finite Source bound")
    images: dict[int, str] = {}
    for index in range(count):
        _clock(deadline)
        address = system._dyld_get_image_header(index)
        name = system._dyld_get_image_name(index)
        if not address or not name or len(name) > 4096:
            raise ValueError("Darwin actual loaded-image inventory is incomplete")
        images[int(address)] = os.fsdecode(name)
    if count != int(system._dyld_image_count()):
        raise ValueError("Darwin loaded-image inventory changed during observation")
    return images


def _executable_segments(base: int, *, deadline: float) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Read only segments of an actual dyld-enumerated, symbol-bound image."""
    _clock(deadline)
    header = ctypes.string_at(base, 32)
    magic, cpu, subtype, file_type, count, command_bytes, flags, reserved = struct.unpack("<8I", header)
    if magic != 0xFEEDFACF or file_type != 6 or not 0 < count <= 4096 or not 0 < command_bytes <= 4 * 1024 * 1024:
        raise ValueError("Darwin provider omitted a bounded genuine 64-bit dylib Mach-O header")
    commands = ctypes.string_at(base + 32, command_bytes)
    segments: list[dict[str, Any]] = []
    image_uuids: list[str] = []
    offset = 0
    for _ in range(count):
        _clock(deadline)
        if offset + 8 > len(commands):
            raise ValueError("Darwin loaded-image command table is truncated")
        command, size = struct.unpack_from("<II", commands, offset)
        if size < 8 or size % 8 or offset + size > len(commands):
            raise ValueError("Darwin loaded-image command has an invalid bounded size")
        if command == 0x19:
            if size < 72:
                raise ValueError("Darwin 64-bit segment command is truncated")
            segment_fields = struct.unpack_from("<II16sQQQQiiII", commands, offset)
            segments.append(
                {
                    "name": segment_fields[2].split(b"\0", 1)[0].decode("ascii"),
                    "vmaddr": segment_fields[3],
                    "vmsize": segment_fields[4],
                    "fileoff": segment_fields[5],
                    "filesize": segment_fields[6],
                    "maxprot": segment_fields[7],
                    "initprot": segment_fields[8],
                }
            )
        if command == 0x1B:
            if size != 24:
                raise ValueError("Darwin image UUID load command is malformed")
            image_uuids.append(commands[offset + 8 : offset + 24].hex())
        offset += size
    if offset != len(commands):
        raise ValueError("Darwin loaded-image command table has unconsumed bytes")
    text = [row for row in segments if row["name"] == "__TEXT" and row["fileoff"] == 0]
    if len(text) != 1:
        raise ValueError("Darwin loaded-image header has no unique mapped __TEXT origin")
    slide = base - text[0]["vmaddr"]
    executable = [row for row in segments if (row["initprot"] & 5) == 5]
    total = sum(row["vmsize"] for row in executable)
    if not executable or not 0 < total <= _MAXIMUM_IMAGE:
        raise ValueError("Darwin executable loaded segments exceed their finite byte budget")
    retained: list[dict[str, Any]] = []
    for row in executable:
        _clock(deadline)
        address = row["vmaddr"] + slide
        if address <= 0 or row["vmsize"] <= 0 or row["initprot"] & 2:
            raise ValueError("Darwin provider code segment is not a positive read-only executable mapping")
        digest = hashlib.sha256()
        for position in range(0, row["vmsize"], 64 * 1024):
            _clock(deadline)
            digest.update(ctypes.string_at(address + position, min(64 * 1024, row["vmsize"] - position)))
        retained.append({**row, "actual_address": address, "sha256": digest.hexdigest()})
    return {
        "actual_header_address": base,
        "header_sha256": hashlib.sha256(header).hexdigest(),
        "load_commands_sha256": hashlib.sha256(commands).hexdigest(),
        "cpu_type": cpu,
        "cpu_subtype": subtype,
        "flags": flags,
        "reserved": reserved,
        "declares_dyld_shared_cache": bool(flags & 0x80000000),
        "slide": slide,
        "image_uuids": image_uuids,
    }, retained


def observe_darwin_framework_sources(
    library: ctypes.CDLL,
    nominated_path: Path,
    symbols: tuple[str, ...],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Bind actual callable symbols to current loaded code on the same clock."""
    _clock(deadline)
    name = nominated_path.name
    expected = Path("/System/Library/Frameworks") / (name + ".framework") / name
    if (
        sys.platform != "darwin"
        or name not in _FRAMEWORKS
        or symbols != _FRAMEWORKS[name]
        or nominated_path != expected
        or library._name != str(expected)
    ):
        raise ValueError("Darwin image reader requires the exact Source-owned framework and symbol cohort")
    system = ctypes.CDLL(None)
    system.dladdr.argtypes = [ctypes.c_void_p, ctypes.POINTER(_DlInfo)]
    system.dladdr.restype = ctypes.c_int
    images = _loaded_images(system, deadline=deadline)
    allowed = {str(expected), str(expected.parent / "Versions" / "A" / name)}
    actual_symbols: list[dict[str, Any]] = []
    bases: set[int] = set()
    for symbol in symbols:
        _clock(deadline)
        pointer = ctypes.cast(getattr(library, symbol), ctypes.c_void_p).value
        info = _DlInfo()
        if not pointer or system.dladdr(pointer, ctypes.byref(info)) != 1 or not info.dli_fbase or not info.dli_fname:
            raise ValueError("Darwin callable provider has no actual dladdr image association")
        base = int(info.dli_fbase)
        image_name = os.fsdecode(info.dli_fname)
        if image_name not in allowed or images.get(base) != image_name:
            raise ValueError("Darwin callable symbol was substituted outside its Source-owned dyld image")
        bases.add(base)
        actual_symbols.append({"symbol": symbol, "actual_address": pointer, "image": image_name})
    if len(bases) != 1:
        raise ValueError("Darwin framework callable cohort spans unmodeled loaded images")
    base = bases.pop()
    header, segments = _executable_segments(base, deadline=deadline)
    for observed_symbol in actual_symbols:
        if not any(
            row["actual_address"] <= observed_symbol["actual_address"] < row["actual_address"] + row["vmsize"]
            for row in segments
        ):
            raise ValueError("Darwin callable symbol is outside the witnessed executable image segments")
    if _loaded_images(system, deadline=deadline).get(base) != images[base]:
        raise ValueError("Darwin actual callable image changed during observation")
    _clock(deadline)
    association = _shared_cache_association(system, expected, header, segments, deadline=deadline)
    return {
        "schema_version": "template-native-darwin-loaded-framework-code-v1",
        "actual_pid": os.getpid(),
        "physical_nomination": _physical_file(expected, deadline=deadline),
        "actual_loaded_image": images[base],
        "symbols": actual_symbols,
        "mach_o": header,
        "executable_segments": segments,
        "shared_cache_association": association,
        "complete_OS_runtime_admitted": False,
        "unclosed_scope": ["complete consumed dyld shared-cache/dependency byte closure"],
    }


def _cache_prefix(path: Path, *, deadline: float) -> dict[str, Any] | None:
    """Read only the real nominated cache header; never call it a whole-file hash."""
    _clock(deadline)
    if not path.exists():
        return None
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        header = os.read(descriptor, 104)
        after = os.fstat(descriptor)
        keys = (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
            "st_nlink",
        )
        if len(header) != 104 or any(getattr(before, key) != getattr(after, key) for key in keys):
            raise ValueError("Darwin actual cache header changed or is truncated")
        if not header[:16].startswith(b"dyld_v1"):
            raise ValueError("Darwin nominated cache has an unmodeled header magic")
        _clock(deadline)
        return {
            "path": str(path),
            "header_bytes": len(header),
            "header_sha256": hashlib.sha256(header).hexdigest(),
            "uuid": header[88:104].hex(),
            "metadata": {key: getattr(after, key) for key in keys},
            "whole_file_bytes_hashed": False,
        }
    finally:
        os.close(descriptor)


def _shared_cache_association(
    system: ctypes.CDLL,
    nominated: Path,
    header: dict[str, Any],
    segments: list[dict[str, Any]],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Use actual dyld APIs on previously enumerated/symbol-bound addresses.

    UUID/header and immutable-range associations are observations. They do not
    replace the retained executable body hashes or admit every cache dependency.
    No address or provider path is accepted from serialized receipt data.
    """
    _clock(deadline)
    required = (
        "_dyld_get_shared_cache_uuid",
        "_dyld_get_shared_cache_range",
        "_dyld_get_image_uuid",
        "_dyld_is_memory_immutable",
        "_dyld_shared_cache_real_path",
    )
    unavailable = [name for name in required if not hasattr(system, name)]
    if unavailable:
        return {
            "available": False,
            "unavailable_apis": unavailable,
            "complete_cache_admitted": False,
        }
    uuid_type = ctypes.c_ubyte * 16
    cache_uuid, image_uuid = uuid_type(), uuid_type()
    length = ctypes.c_size_t()
    system._dyld_get_shared_cache_uuid.argtypes = [ctypes.c_void_p]
    system._dyld_get_shared_cache_uuid.restype = ctypes.c_bool
    system._dyld_get_shared_cache_range.argtypes = [ctypes.POINTER(ctypes.c_size_t)]
    system._dyld_get_shared_cache_range.restype = ctypes.c_void_p
    system._dyld_get_image_uuid.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    system._dyld_get_image_uuid.restype = ctypes.c_bool
    system._dyld_is_memory_immutable.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    system._dyld_is_memory_immutable.restype = ctypes.c_bool
    system._dyld_shared_cache_real_path.argtypes = [ctypes.c_char_p]
    system._dyld_shared_cache_real_path.restype = ctypes.c_char_p
    cache_present = bool(system._dyld_get_shared_cache_uuid(cache_uuid))
    cache_base = system._dyld_get_shared_cache_range(ctypes.byref(length))
    image_present = bool(system._dyld_get_image_uuid(header["actual_header_address"], image_uuid))
    canonical = system._dyld_shared_cache_real_path(os.fsencode(nominated))
    if image_present and header["image_uuids"] != [bytes(image_uuid).hex()]:
        raise ValueError("actual dyld image UUID differs from its witnessed Mach-O command")
    immutable = [
        {
            "actual_address": row["actual_address"],
            "bytes": row["vmsize"],
            "dyld_owned_immutable": bool(system._dyld_is_memory_immutable(row["actual_address"], row["vmsize"])),
            "within_actual_shared_cache_range": bool(
                cache_base
                and int(cache_base) <= row["actual_address"]
                and row["actual_address"] + row["vmsize"] <= int(cache_base) + length.value
            ),
        }
        for row in segments
    ]
    roots = (
        Path("/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld"),
        Path("/System/Library/dyld"),
    )
    matches = []
    for root in roots:
        for name in ("arm64e", "arm64", "x86_64", "x86_64h"):
            prefix = _cache_prefix(root / ("dyld_shared_cache_" + name), deadline=deadline)
            if prefix is not None and cache_present and prefix["uuid"] == bytes(cache_uuid).hex():
                matches.append(prefix)
    _clock(deadline)
    return {
        "available": True,
        "cache_in_use": cache_present,
        "actual_cache_uuid": bytes(cache_uuid).hex() if cache_present else None,
        "actual_cache_base": int(cache_base) if cache_base else None,
        "actual_cache_range_bytes": length.value,
        "actual_image_uuid": bytes(image_uuid).hex() if image_present else None,
        "actual_canonical_image_path": os.fsdecode(canonical) if canonical else None,
        "executable_ranges": immutable,
        "uuid_matched_physical_cache_headers": matches,
        "complete_cache_admitted": False,
    }
