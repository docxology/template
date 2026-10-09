"""Actual Linux Fontconfig face resolution and FreeType Unicode glyph mapping.

The caller supplies a source-bound request obtained from actual CDP usage. The
physical file, collection index and PostScript face must match both libraries.
This narrow codepoint probe does not admit Chrome's shaping, renderer, font
configuration, hinting, dependency closure, or complete OS runtime custody.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import math
import os
import platform
import stat
import sys
import time
from pathlib import Path
from typing import Any
from infrastructure.reporting.native_format_html_source_shaping import (
    shape_physical_source_font,
)

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.reporting.native_format_acceptance_contracts import (
    native_deadline_guard,
)

PROBE_SCHEMA = "template-native-html-platform-font-probe-v1"
FONTCONFIG_ABI = "libfontconfig.so.1"
FREETYPE_ABI = "libfreetype.so.6"


def _clock(deadline: float) -> None:
    if type(deadline) not in {int, float} or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("Linux font probe exhausted its original caller deadline")


def _file(path: Path, deadline: float, maximum: int = 32 * 1024 * 1024) -> tuple[bytes, dict[str, Any]]:
    _clock(deadline)
    selected = path.resolve(strict=True)
    before = selected.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("Linux font/provider requires an actual regular physical file")
    content = read_bytes_confined(selected.parent, selected, max_bytes=maximum)
    after = selected.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if any(getattr(before, key) != getattr(after, key) for key in fields):
        raise ValueError("Linux font/provider physical bytes changed during observation")
    _clock(deadline)
    return content, {
        "path": str(selected),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "metadata": {key: getattr(after, key) for key in fields},
    }


def _mapped_provider(soname: str, deadline: float) -> dict[str, Any]:
    """Bind the actual loaded Linux mapping to its current physical library.

    This records the named provider only. Dependency/configuration/loader and
    Chrome-process mappings remain explicit enclosing runtime obligations.
    """
    _clock(deadline)
    with Path("/proc/self/maps").open("rb") as stream:
        raw = stream.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Linux mapping inventory exceeds its finite byte bound")
    paths: set[Path] = set()
    mappings: list[dict[str, Any]] = []
    for line in raw.decode("ascii", "strict").splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) != 6 or not fields[5].startswith("/"):
            continue
        name = Path(fields[5]).name
        if name != soname and not name.startswith(soname + "."):
            continue
        if fields[5].endswith(" (deleted)") or "\\" in fields[5]:
            raise ValueError("Linux provider has a deleted or escaped mapping path")
        path = Path(fields[5]).resolve(strict=True)
        if not fields[4].isdecimal() or path.stat().st_ino != int(fields[4]):
            raise ValueError("Linux actual provider mapping differs from physical library inode")
        major, minor = (int(value, 16) for value in fields[3].split(":"))
        if os.major(path.stat().st_dev) != major or os.minor(path.stat().st_dev) != minor:
            raise ValueError("Linux actual provider mapping differs from physical library device")
        paths.add(path)
        mappings.append(
            {
                "address": fields[0],
                "permissions": fields[1],
                "offset": fields[2],
                "device": fields[3],
                "inode": int(fields[4]),
                "path": str(path),
            }
        )
    if len(paths) != 1 or not any("x" in row["permissions"] for row in mappings):
        raise ValueError("Linux named provider lacks one genuine executable physical mapping")
    physical = _file(next(iter(paths)), deadline, 512 * 1024 * 1024)[1]
    _clock(deadline)
    return {"soname": soname, "physical": physical, "mappings": mappings}


def _declare_fontconfig(library: ctypes.CDLL) -> None:
    library.FcGetVersion.argtypes = []
    library.FcGetVersion.restype = ctypes.c_int
    library.FcInitLoadConfigAndFonts.argtypes = []
    library.FcInitLoadConfigAndFonts.restype = ctypes.c_void_p
    library.FcConfigDestroy.argtypes = [ctypes.c_void_p]
    library.FcConfigDestroy.restype = None
    library.FcPatternCreate.argtypes = []
    library.FcPatternCreate.restype = ctypes.c_void_p
    library.FcPatternDestroy.argtypes = [ctypes.c_void_p]
    library.FcPatternDestroy.restype = None
    library.FcPatternAddString.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    library.FcPatternAddString.restype = ctypes.c_int
    library.FcConfigSubstitute.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int,
    ]
    library.FcConfigSubstitute.restype = ctypes.c_int
    library.FcDefaultSubstitute.argtypes = [ctypes.c_void_p]
    library.FcDefaultSubstitute.restype = None
    library.FcFontMatch.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_int),
    ]
    library.FcFontMatch.restype = ctypes.c_void_p
    library.FcPatternGetString.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_char_p),
    ]
    library.FcPatternGetString.restype = ctypes.c_int
    library.FcPatternGetInteger.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
    ]
    library.FcPatternGetInteger.restype = ctypes.c_int


def _declare_freetype(library: ctypes.CDLL) -> None:
    library.FT_Init_FreeType.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    library.FT_Init_FreeType.restype = ctypes.c_int
    library.FT_Done_FreeType.argtypes = [ctypes.c_void_p]
    library.FT_Done_FreeType.restype = ctypes.c_int
    library.FT_New_Face.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_long,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    library.FT_New_Face.restype = ctypes.c_int
    library.FT_Done_Face.argtypes = [ctypes.c_void_p]
    library.FT_Done_Face.restype = ctypes.c_int
    library.FT_Get_Postscript_Name.argtypes = [ctypes.c_void_p]
    library.FT_Get_Postscript_Name.restype = ctypes.c_char_p
    library.FT_Select_Charmap.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    library.FT_Select_Charmap.restype = ctypes.c_int
    library.FT_Get_Char_Index.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    library.FT_Get_Char_Index.restype = ctypes.c_uint
    library.FT_Library_Version.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
    ]
    library.FT_Library_Version.restype = None


def _matched_face(config: int, fc: ctypes.CDLL, name: str) -> tuple[Path, int]:
    request, matched = fc.FcPatternCreate(), None
    if not request:
        raise ValueError("Fontconfig could not allocate its physical face request")
    try:
        if not fc.FcPatternAddString(request, b"postscriptname", name.encode("utf-8")):
            raise ValueError("Fontconfig rejected the source face name")
        if not fc.FcConfigSubstitute(config, request, 0):
            raise ValueError("Fontconfig source face substitution failed")
        fc.FcDefaultSubstitute(request)
        result = ctypes.c_int()
        matched = fc.FcFontMatch(config, request, ctypes.byref(result))
        if not matched or result.value != 0:
            raise ValueError("Fontconfig did not resolve an actual source face")
        actual_name, physical = ctypes.c_char_p(), ctypes.c_char_p()
        index = ctypes.c_int()
        if (
            fc.FcPatternGetString(matched, b"postscriptname", 0, ctypes.byref(actual_name)) != 0
            or actual_name.value != name.encode("utf-8")
            or fc.FcPatternGetString(matched, b"file", 0, ctypes.byref(physical)) != 0
            or not physical.value
            or fc.FcPatternGetInteger(matched, b"index", 0, ctypes.byref(index)) != 0
        ):
            raise ValueError("Fontconfig substituted or omitted source face/file/index")
        if not 0 <= index.value < 256:
            raise ValueError("Linux collection or named-variable face exceeds the modeled source face bound")
        path = Path(os.fsdecode(physical.value))
        if not path.is_absolute():
            raise ValueError("Fontconfig physical source font is not absolute")
        return path, index.value
    finally:
        if matched:
            fc.FcPatternDestroy(matched)
        fc.FcPatternDestroy(request)


def _cleanup_result(code: int, message: str) -> None:
    if code:
        original = sys.exception()
        if original is not None:
            original.add_note(message)
        else:
            raise ValueError(message)


def probe_linux_platform_fonts(request: dict[str, Any], *, deadline: float) -> dict[str, Any]:
    """Map genuine Linux source-codepoint glyph IDs without candidate pixels.

    Exact-face substitution is refused. A missing native provider fails and is
    never turned into a skip, synthetic glyph or portable acceptance flag.
    """
    _clock(deadline)
    if sys.platform != "linux" or request.get("schema_version") != "template-native-html-platform-font-request-v1":
        raise ValueError("Linux source glyph probe requires its genuine Linux/source request")
    rows = request.get("fonts")
    if not isinstance(rows, list) or len(rows) > 256:
        raise ValueError("Linux font request exceeds its finite face budget")
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("postscript_name"), str)
            or not 0 < len(row["postscript_name"]) <= 256
            or "\x00" in row["postscript_name"]
            or not isinstance(row.get("characters"), str)
            or len(row["characters"]) > 200000
            or any(ord(character) > 0xFFFF or 0xD800 <= ord(character) <= 0xDFFF for character in row["characters"])
        ):
            raise ValueError("Linux source face/codepoint request is unsupported or malformed")
    if sum(len(row["characters"]) for row in rows) > 200000:
        raise ValueError("aggregate Linux source glyph codepoints exceed the existing bound")
    with native_deadline_guard(deadline):
        fc = ctypes.CDLL(FONTCONFIG_ABI, mode=ctypes.RTLD_LOCAL)
        ft = ctypes.CDLL(FREETYPE_ABI, mode=ctypes.RTLD_LOCAL)
        _declare_fontconfig(fc)
        _declare_freetype(ft)
        before = [_mapped_provider(name, deadline) for name in (FONTCONFIG_ABI, FREETYPE_ABI)]
        library = ctypes.c_void_p()
        if ft.FT_Init_FreeType(ctypes.byref(library)) or not library.value:
            raise ValueError("Linux actual FreeType initialization failed")
        config = None
        observations = []
        blockers = [
            "Linux loaded provider observations do not admit complete loader/dependency/OS custody",
            "Linux Fontconfig configuration/cache/substitution and Chrome font consumption remain obligated",
            "Linux source codepoint mapping does not admit HarfBuzz shaping, hinting, styles or raster calibration",
        ]
        try:
            config = fc.FcInitLoadConfigAndFonts()
            if not config:
                raise ValueError("Linux actual Fontconfig configuration initialization failed")
            versions = [ctypes.c_int(), ctypes.c_int(), ctypes.c_int()]
            ft.FT_Library_Version(library, *(ctypes.byref(value) for value in versions))
            provider_versions = {
                "fontconfig": fc.FcGetVersion(),
                "freetype": [value.value for value in versions],
            }
            for row in rows:
                _clock(deadline)
                name, characters = row["postscript_name"], row["characters"]
                path, index = _matched_face(config, fc, name)
                content, font_before = _file(path, deadline)
                face = ctypes.c_void_p()
                if ft.FT_New_Face(library, os.fsencode(path), index, ctypes.byref(face)):
                    raise ValueError("FreeType could not open the exact Fontconfig physical source face")
                try:
                    if ft.FT_Get_Postscript_Name(face) != name.encode("utf-8"):
                        raise ValueError("FreeType substituted a different physical source face")
                    if ft.FT_Select_Charmap(face, 0x756E6963):
                        raise ValueError("FreeType source face omitted an actual Unicode charmap")
                    glyphs = []
                    for character in characters:
                        _clock(deadline)
                        glyphs.append(ft.FT_Get_Char_Index(face, ord(character)))
                    font_after = _file(path, deadline)[1]
                    if font_before != font_after:
                        raise ValueError("Linux physical font changed during actual Unicode glyph mapping")
                    complete = all(glyphs)
                    contextual = shape_physical_source_font(content, index, row, deadline=deadline)
                    observations.append(
                        {
                            "postscript_name": name,
                            "face_index": index,
                            "font_file_before": font_before,
                            "font_file_after": font_after,
                            "font_sha256": hashlib.sha256(content).hexdigest(),
                            "characters": characters,
                            "glyph_ids": glyphs,
                            "all_characters_mapped": complete,
                            "provider": "Fontconfig/FreeType",
                            **({"contextual_runs": contextual} if contextual else {}),
                        }
                    )
                    if not complete:
                        blockers.append(name + ": Linux source codepoint mapping requires a modeled fallback run")
                finally:
                    _cleanup_result(
                        ft.FT_Done_Face(face),
                        "Linux actual FreeType physical face cleanup failed",
                    )
        finally:
            if config:
                fc.FcConfigDestroy(config)
            _cleanup_result(
                ft.FT_Done_FreeType(library),
                "Linux actual FreeType library cleanup failed",
            )
        after = [_mapped_provider(name, deadline) for name in (FONTCONFIG_ABI, FREETYPE_ABI)]
        if before != after:
            raise ValueError("Linux actual font provider mappings/physical bytes changed")
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
            "framework_before": before,
            "framework_after": after,
            "provider_versions": provider_versions,
            "fonts": observations,
            "blockers": blockers,
        }
