"""Actual Darwin/Linux font-file resolution and source-codepoint glyph observations.

No installed font or library is modified or archived. A real enclosing process
receipt must bind this probe's SDK, source input, original successful exit and
before/after decoder/platform observations. Unreadable dyld framework closure
stays an explicit blocker, even when a glyph font's file hash is available.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.rendering._web_font_assets import FONT_BODIES, read_source_web_font
from infrastructure.reporting.native_format_acceptance_contracts import (
    native_deadline_guard,
)
from infrastructure.reporting.native_format_html_darwin_image_custody import (
    observe_darwin_framework_sources,
)
from infrastructure.reporting.native_format_html_source_shaping import (
    shape_physical_source_font,
)

PROBE_SCHEMA = "template-native-html-platform-font-probe-v1"
CORE_TEXT = Path("/System/Library/Frameworks/CoreText.framework/CoreText")
CORE_FOUNDATION = Path("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")


def _clock(deadline: float) -> None:
    if type(deadline) not in {int, float} or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("platform font probe exhausted its original caller clock")


def _file(path: Path, maximum: int = 32 * 1024 * 1024) -> tuple[bytes, dict[str, Any]]:
    selected = path.resolve(strict=True)
    before = selected.stat()
    content = read_bytes_confined(selected.parent, selected, max_bytes=maximum)
    after = selected.stat()
    fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(before, key) != getattr(after, key) for key in fields):
        raise ValueError("platform font/framework bytes changed during observation")
    return content, {
        "path": str(selected),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "metadata": {key: getattr(after, key) for key in fields},
    }


def probe_platform_fonts(request: dict[str, Any], *, deadline: float) -> dict[str, Any]:
    """Resolve actual CoreText file URLs and Unicode glyph IDs without a canvas."""
    _clock(deadline)
    if request.get("font_provider") == "source-web-font-assets-v1":
        with native_deadline_guard(deadline):
            return _probe_source_web_fonts(request, deadline=deadline)
    if sys.platform == "linux":
        from infrastructure.reporting.native_format_html_linux_font_probe import (
            probe_linux_platform_fonts,
        )

        return probe_linux_platform_fonts(request, deadline=deadline)
    with native_deadline_guard(deadline):
        return _probe_darwin_platform_fonts(request, deadline=deadline)


def _probe_darwin_platform_fonts(request: dict[str, Any], *, deadline: float) -> dict[str, Any]:
    if sys.platform != "darwin" or request.get("schema_version") != "template-native-html-platform-font-request-v1":
        raise ValueError("actual platform font byte probe requires the declared Darwin source request")
    rows = request.get("fonts")
    if not isinstance(rows, list) or len(rows) > 256:
        raise ValueError("platform font request exceeds its finite face budget")
    if sum(len(row.get("characters", "")) for row in rows) > 200000:
        raise ValueError("aggregate platform glyph codepoints exceed the existing bound")
    cf = ctypes.CDLL(str(CORE_FOUNDATION))
    ct = ctypes.CDLL(str(CORE_TEXT))
    cf.CFStringCreateWithCString.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_uint32,
    ]
    cf.CFStringCreateWithCString.restype = ctypes.c_void_p
    cf.CFStringGetCString.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_long,
        ctypes.c_uint32,
    ]
    cf.CFStringGetCString.restype = ctypes.c_bool
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    cf.CFRelease.restype = None
    cf.CFURLGetFileSystemRepresentation.argtypes = [
        ctypes.c_void_p,
        ctypes.c_bool,
        ctypes.c_void_p,
        ctypes.c_long,
    ]
    cf.CFURLGetFileSystemRepresentation.restype = ctypes.c_bool
    ct.CTFontCreateWithName.argtypes = [
        ctypes.c_void_p,
        ctypes.c_double,
        ctypes.c_void_p,
    ]
    ct.CTFontCreateWithName.restype = ctypes.c_void_p
    ct.CTFontCopyPostScriptName.argtypes = [ctypes.c_void_p]
    ct.CTFontCopyPostScriptName.restype = ctypes.c_void_p
    ct.CTFontCopyAttribute.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    ct.CTFontCopyAttribute.restype = ctypes.c_void_p
    ct.CTFontGetGlyphsForCharacters.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_long,
    ]
    ct.CTFontGetGlyphsForCharacters.restype = ctypes.c_bool
    attribute = ctypes.c_void_p.in_dll(ct, "kCTFontURLAttribute").value
    framework_before = [
        observe_darwin_framework_sources(
            cf,
            CORE_FOUNDATION,
            (
                "CFStringCreateWithCString",
                "CFStringGetCString",
                "CFRelease",
                "CFURLGetFileSystemRepresentation",
            ),
            deadline=deadline,
        ),
        observe_darwin_framework_sources(
            ct,
            CORE_TEXT,
            (
                "CTFontCreateWithName",
                "CTFontCopyPostScriptName",
                "CTFontCopyAttribute",
                "CTFontGetGlyphsForCharacters",
            ),
            deadline=deadline,
        ),
    ]
    blockers = ["loaded framework code observations do not admit complete consumed dyld cache/dependency bytes"]
    observations = []
    for row in rows:
        _clock(deadline)
        name, characters = row["postscript_name"], row["characters"]
        if not isinstance(name, str) or not isinstance(characters, str) or len(name) > 256 or len(characters) > 200000:
            raise ValueError("platform glyph source request is malformed/unbounded")
        source_name = cf.CFStringCreateWithCString(None, name.encode(), 0x08000100)
        font = None
        native_name = None
        url = None
        try:
            font = ct.CTFontCreateWithName(source_name, 12, None)
            if not font:
                raise ValueError("source-requested platform font was unavailable")
            native_name = ct.CTFontCopyPostScriptName(font)
            buffer = ctypes.create_string_buffer(4096)
            if not cf.CFStringGetCString(native_name, buffer, len(buffer), 0x08000100) or buffer.value.decode() != name:
                raise ValueError("CoreText substituted a different physical source font")
            url = ct.CTFontCopyAttribute(font, attribute)
            if not url or not cf.CFURLGetFileSystemRepresentation(url, True, buffer, len(buffer)):
                raise ValueError("actual native font omitted its source file URL")
            path = Path(os.fsdecode(buffer.value))
            content, before = _file(path)
            # CoreText consumes UniChar units; original Source indexes remain
            # Unicode scalar indexes. Surrogate pairs are mapped at their first
            # unit by the actual provider, with the second unit required zero.
            encoded = characters.encode("utf-16-le")
            units = [int.from_bytes(encoded[index : index + 2], "little") for index in range(0, len(encoded), 2)]
            codepoints = (ctypes.c_uint16 * len(units))(*units)
            utf16_glyphs = (ctypes.c_uint16 * len(units))()
            complete = ct.CTFontGetGlyphsForCharacters(font, codepoints, utf16_glyphs, len(units))
            glyphs = []
            unit_index = 0
            for character in characters:
                glyphs.append(int(utf16_glyphs[unit_index]))
                if ord(character) > 0xFFFF:
                    if utf16_glyphs[unit_index + 1] != 0:
                        raise ValueError("actual CoreText surrogate pair has an unmodeled second glyph")
                    unit_index += 2
                else:
                    unit_index += 1
            after = _file(path)[1]
            if before != after:
                raise ValueError("actual platform font bytes changed during Unicode glyph mapping")
            if row.get("contextual_runs") and content.startswith(b"ttcf"):
                raise ValueError(
                    "actual contextual CoreText collection face requires explicit native face-index custody"
                )
            contextual = shape_physical_source_font(content, 0, row, deadline=deadline)
            observations.append(
                {
                    "postscript_name": name,
                    "font_file_before": before,
                    "font_file_after": after,
                    "font_sha256": hashlib.sha256(content).hexdigest(),
                    "characters": characters,
                    "glyph_ids": list(glyphs),
                    "all_characters_mapped": bool(complete),
                    **(
                        {"utf16_units": units, "utf16_glyph_ids": list(utf16_glyphs)}
                        if len(units) != len(characters)
                        else {}
                    ),
                    **({"contextual_runs": contextual} if contextual else {}),
                }
            )
            if not complete:
                blockers.append(name + ": CoreText source codepoint mapping requires a modeled fallback run")
        finally:
            for value in (url, native_name, font, source_name):
                if value:
                    cf.CFRelease(value)
    framework_after = [
        observe_darwin_framework_sources(
            cf,
            CORE_FOUNDATION,
            (
                "CFStringCreateWithCString",
                "CFStringGetCString",
                "CFRelease",
                "CFURLGetFileSystemRepresentation",
            ),
            deadline=deadline,
        ),
        observe_darwin_framework_sources(
            ct,
            CORE_TEXT,
            (
                "CTFontCreateWithName",
                "CTFontCopyPostScriptName",
                "CTFontCopyAttribute",
                "CTFontGetGlyphsForCharacters",
            ),
            deadline=deadline,
        ),
    ]
    if framework_before != framework_after:
        raise ValueError("platform font resolver/framework bytes changed")
    result = {
        "schema_version": PROBE_SCHEMA,
        "request_sha256": hashlib.sha256(
            json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "framework_before": framework_before,
        "framework_after": framework_after,
        "fonts": observations,
        "blockers": blockers,
    }
    _clock(deadline)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    args = parser.parse_args()
    request = json.loads(read_bytes_confined(args.request.parent, args.request, max_bytes=8 * 1024 * 1024))
    print(json.dumps(probe_platform_fonts(request, deadline=args.deadline), sort_keys=True))


def _probe_source_web_fonts(request: dict[str, Any], *, deadline: float) -> dict[str, Any]:
    """Consume fixed actual Source bodies, not installed fallback font names."""
    if request.get("schema_version") != "template-native-html-platform-font-request-v1":
        raise ValueError("Source body probe requires the exact Source font request")
    rows = request.get("fonts")
    if not isinstance(rows, list) or not 0 < len(rows) <= 12:
        raise ValueError("Source font body probe exceeds its finite physical face cohort")
    # Validate the complete request before reading any face or allocating glyphs.
    # The original Darwin/Linux codepoint budget belongs to the whole request.
    character_count = 0
    contextual_character_count = 0
    contextual_run_count = 0
    for row in rows:
        _clock(deadline)
        if not isinstance(row, dict):
            raise ValueError("Source font body request requires typed physical face rows")
        name, characters = row.get("postscript_name"), row.get("characters")
        if not isinstance(name, str) or name not in FONT_BODIES or not isinstance(characters, str):
            raise ValueError("Source font body request is outside its fixed face/text bounds")
        character_count += len(characters)
        if character_count > 200000:
            raise ValueError("aggregate platform glyph codepoints exceed the existing bound")
        contexts = row.get("contextual_runs", [])
        if not isinstance(contexts, list):
            raise ValueError("Source contextual shaping requires original typed run lists")
        contextual_run_count += len(contexts)
        if contextual_run_count > 200000:
            raise ValueError("Source contextual shaping request exceeds its existing run bound")
        for context in contexts:
            _clock(deadline)
            if not isinstance(context, dict) or not isinstance(context.get("text"), str):
                raise ValueError("Source contextual shaping requires original typed text runs")
            contextual_character_count += len(context["text"])
            if contextual_character_count > 200000:
                raise ValueError("aggregate Source contextual characters exceed the existing bound")
    from io import BytesIO
    from fontTools.ttLib import TTFont

    observations = []
    blockers = []
    for row in rows:
        _clock(deadline)
        name, characters = row["postscript_name"], row["characters"]
        if name not in FONT_BODIES or not isinstance(characters, str) or len(characters) > 200000:
            raise ValueError("Source font body request is outside its fixed face/text bounds")
        content, before = read_source_web_font(name, deadline=deadline)
        font = TTFont(BytesIO(content), lazy=False)
        try:
            if font["name"].getDebugName(6) != name:
                raise ValueError("Source font body has a different actual physical face")
            cmap = font.getBestCmap() or {}
            glyphs = [font.getGlyphID(cmap[ord(char)]) if ord(char) in cmap else 0 for char in characters]
        finally:
            font.close()
        contextual = shape_physical_source_font(content, 0, row, deadline=deadline)
        _, after = read_source_web_font(name, deadline=deadline)
        if before != after:
            raise ValueError("actual Source font body changed across shaping/glyph observation")
        complete = all(glyph != 0 or char.isspace() for char, glyph in zip(characters, glyphs, strict=True))
        if not complete:
            blockers.append(name + ": Source body needs independently modeled missing-character fallback")
        observations.append(
            {
                "postscript_name": name,
                "font_file_before": before,
                "font_file_after": after,
                "font_sha256": before["sha256"],
                "characters": characters,
                "glyph_ids": glyphs,
                "all_characters_mapped": complete,
                "provider": "Source font body/HarfBuzz",
                "face_index": 0,
                **({"contextual_runs": contextual} if contextual else {}),
            }
        )
    _clock(deadline)
    return {
        "schema_version": PROBE_SCHEMA,
        "request_sha256": hashlib.sha256(
            json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "framework_before": [],
        "framework_after": [],
        "fonts": observations,
        "blockers": blockers,
        "provider_scope": "fixed physical Source font bytes and actual independently physical HarfBuzz; "
        "no OS/browser decoder admission",
    }


if __name__ == "__main__":
    main()
