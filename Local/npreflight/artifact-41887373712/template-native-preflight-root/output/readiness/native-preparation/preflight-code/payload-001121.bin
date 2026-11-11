"""Genuine bounded HarfBuzz shaping of exact independently admitted font bytes.

The callable factory nominates a finite physical platform provider. Actual
function-to-library association and physical bytes are observed before/after.
These observations do not admit Chromium's shaper, dependencies or kernel.
"""

from __future__ import annotations

import ctypes
import hashlib
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_acceptance_contracts import (
    native_deadline_guard,
)

_TOKEN = object()
_CALLABLES = (
    "hb_blob_create",
    "hb_blob_destroy",
    "hb_face_create",
    "hb_face_destroy",
    "hb_face_get_upem",
    "hb_face_get_glyph_count",
    "hb_font_create",
    "hb_font_destroy",
    "hb_ot_font_set_funcs",
    "hb_font_set_scale",
    "hb_buffer_create",
    "hb_buffer_destroy",
    "hb_buffer_add_utf32",
    "hb_buffer_set_direction",
    "hb_buffer_guess_segment_properties",
    "hb_buffer_get_glyph_infos",
    "hb_buffer_get_glyph_positions",
    "hb_shape",
    "hb_version_string",
)
_NOMINATIONS = {
    "darwin": (
        "/opt/homebrew/lib/libharfbuzz.0.dylib",
        "/usr/local/lib/libharfbuzz.0.dylib",
    ),
    "linux": (
        "/usr/lib/x86_64-linux-gnu/libharfbuzz.so.0",
        "/usr/lib/aarch64-linux-gnu/libharfbuzz.so.0",
        "/usr/lib64/libharfbuzz.so.0",
    ),
}


class _GlyphInfo(ctypes.Structure):
    _fields_ = [
        ("codepoint", ctypes.c_uint32),
        ("mask", ctypes.c_uint32),
        ("cluster", ctypes.c_uint32),
        ("var1", ctypes.c_uint32),
        ("var2", ctypes.c_uint32),
    ]


class _GlyphPosition(ctypes.Structure):
    _fields_ = [
        ("x_advance", ctypes.c_int32),
        ("y_advance", ctypes.c_int32),
        ("x_offset", ctypes.c_int32),
        ("y_offset", ctypes.c_int32),
        ("var", ctypes.c_uint32),
    ]


class _Feature(ctypes.Structure):
    _fields_ = [
        ("tag", ctypes.c_uint32),
        ("value", ctypes.c_uint32),
        ("start", ctypes.c_uint32),
        ("end", ctypes.c_uint32),
    ]


class _DlInfo(ctypes.Structure):
    _fields_ = [
        ("filename", ctypes.c_char_p),
        ("base", ctypes.c_void_p),
        ("symbol", ctypes.c_char_p),
        ("symbol_address", ctypes.c_void_p),
    ]


def _clock(deadline: float) -> None:
    if type(deadline) not in {int, float} or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("Source shaping exhausted the original caller clock")


def _physical(path: Path, *, deadline: float) -> dict[str, Any]:
    _clock(deadline)
    path = path.resolve(strict=True)
    before = path.stat()
    content = read_bytes_confined(path.parent, path, max_bytes=512 * 1024 * 1024)
    after = path.stat()
    keys = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
        "st_nlink",
    )
    if any(getattr(before, key) != getattr(after, key) for key in keys):
        raise ValueError("Source shaping physical provider changed during read")
    _clock(deadline)
    return {
        "path": str(path),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "identity": {key: getattr(after, key) for key in keys},
    }


def _configure(library: ctypes.CDLL) -> None:
    signatures = {
        "hb_blob_create": (
            [
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.c_int,
                ctypes.c_void_p,
                ctypes.c_void_p,
            ],
            ctypes.c_void_p,
        ),
        "hb_blob_destroy": ([ctypes.c_void_p], None),
        "hb_face_create": ([ctypes.c_void_p, ctypes.c_uint], ctypes.c_void_p),
        "hb_face_destroy": ([ctypes.c_void_p], None),
        "hb_face_get_upem": ([ctypes.c_void_p], ctypes.c_uint),
        "hb_face_get_glyph_count": ([ctypes.c_void_p], ctypes.c_uint),
        "hb_font_create": ([ctypes.c_void_p], ctypes.c_void_p),
        "hb_font_destroy": ([ctypes.c_void_p], None),
        "hb_ot_font_set_funcs": ([ctypes.c_void_p], None),
        "hb_font_set_scale": ([ctypes.c_void_p, ctypes.c_int, ctypes.c_int], None),
        "hb_buffer_create": ([], ctypes.c_void_p),
        "hb_buffer_destroy": ([ctypes.c_void_p], None),
        "hb_buffer_add_utf32": (
            [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_uint,
                ctypes.c_int,
            ],
            None,
        ),
        "hb_buffer_set_direction": ([ctypes.c_void_p, ctypes.c_int], None),
        "hb_buffer_guess_segment_properties": ([ctypes.c_void_p], None),
        "hb_buffer_get_glyph_infos": (
            [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)],
            ctypes.POINTER(_GlyphInfo),
        ),
        "hb_buffer_get_glyph_positions": (
            [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)],
            ctypes.POINTER(_GlyphPosition),
        ),
        "hb_shape": (
            [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(_Feature), ctypes.c_uint],
            None,
        ),
        "hb_version_string": ([], ctypes.c_char_p),
    }
    for name, (args, result) in signatures.items():
        function = getattr(library, name)
        function.argtypes, function.restype = args, result


def _provider_symbols(library: ctypes.CDLL, path: Path, *, deadline: float) -> list[dict[str, Any]]:
    system = ctypes.CDLL(None)
    system.dladdr.argtypes = [ctypes.c_void_p, ctypes.POINTER(_DlInfo)]
    system.dladdr.restype = ctypes.c_int
    rows = []
    for name in _CALLABLES:
        _clock(deadline)
        pointer = ctypes.cast(getattr(library, name), ctypes.c_void_p).value
        info = _DlInfo()
        if not pointer or system.dladdr(pointer, ctypes.byref(info)) != 1 or not info.filename:
            raise ValueError("Source shaping callable lacks genuine loaded-provider association")
        actual = Path(os.fsdecode(info.filename)).resolve(strict=True)
        if actual != path:
            raise ValueError("Source shaping callable came from an unadmitted physical provider")
        rows.append(
            {
                "symbol": name,
                "actual_address": pointer,
                "actual_loaded_image": str(actual),
            }
        )
    return rows


@dataclass(frozen=True)
class SourceHTMLShaper:
    """Process-local factory capability; JSON cannot nominate this provider."""

    _token: object
    owner_pid: int
    library: ctypes.CDLL
    physical_before: dict[str, Any]
    symbols_before: list[dict[str, Any]]

    def close(self, *, deadline: float) -> None:
        if self._token is not _TOKEN or self.owner_pid != os.getpid():
            raise ValueError("Source shaping capability is not this genuine process owner")
        path = Path(self.physical_before["path"])
        if (
            _physical(path, deadline=deadline) != self.physical_before
            or _provider_symbols(self.library, path, deadline=deadline) != self.symbols_before
        ):
            raise ValueError("actual Source shaping provider bytes/functions changed")

    def shape(
        self,
        font_bytes: bytes,
        face_index: int,
        text: str,
        *,
        deadline: float,
        kerning: bool = True,
        ligatures: bool = True,
    ) -> dict[str, Any]:
        """Shape complete original text clusters, including spaces/combining marks."""
        self.close(deadline=deadline)
        if not 0 < len(font_bytes) <= 32 * 1024 * 1024 or not 0 <= face_index < 256 or len(text) > 200000:
            raise ValueError("Source shaping font/face/text exceeds its original finite bound")
        library = self.library
        blob = face = font = buffer = None
        original: BaseException | None = None
        try:
            with native_deadline_guard(deadline):
                storage = ctypes.create_string_buffer(font_bytes)
                blob = library.hb_blob_create(storage, len(font_bytes), 0, None, None)
                face = library.hb_face_create(blob, face_index) if blob else None
                upem = int(library.hb_face_get_upem(face)) if face else 0
                glyph_count = int(library.hb_face_get_glyph_count(face)) if face else 0
                if not face or not 16 <= upem <= 16384 or not 0 < glyph_count <= 65536:
                    raise ValueError("Source shaping font face is not a genuine bounded SFNT face")
                font = library.hb_font_create(face)
                buffer = library.hb_buffer_create()
                if not font or not buffer:
                    raise ValueError("actual Source shaping provider failed to allocate its font/buffer")
                library.hb_ot_font_set_funcs(font)
                library.hb_font_set_scale(font, upem, upem)
                codepoints = (ctypes.c_uint32 * len(text))(*(ord(character) for character in text))
                library.hb_buffer_add_utf32(buffer, codepoints, len(text), 0, len(text))
                library.hb_buffer_set_direction(buffer, 4)
                library.hb_buffer_guess_segment_properties(buffer)
                features = (_Feature * 3)(
                    _Feature(int.from_bytes(b"kern", "big"), int(kerning), 0, 0xFFFFFFFF),
                    _Feature(int.from_bytes(b"liga", "big"), int(ligatures), 0, 0xFFFFFFFF),
                    _Feature(int.from_bytes(b"clig", "big"), int(ligatures), 0, 0xFFFFFFFF),
                )
                library.hb_shape(font, buffer, features, len(features))
                count, position_count = ctypes.c_uint(), ctypes.c_uint()
                infos = library.hb_buffer_get_glyph_infos(buffer, ctypes.byref(count))
                positions = library.hb_buffer_get_glyph_positions(buffer, ctypes.byref(position_count))
                if (
                    count.value != position_count.value
                    or count.value > 200000
                    or (count.value and (not infos or not positions))
                ):
                    raise ValueError("actual Source shaper returned an incomplete/unbounded glyph census")
                glyphs = []
                for index in range(count.value):
                    _clock(deadline)
                    info, position = infos[index], positions[index]
                    if info.codepoint >= glyph_count or info.cluster >= len(text):
                        raise ValueError("actual Source shaper returned a glyph/cluster outside original font/text")
                    glyphs.append(
                        {
                            "glyph_id": info.codepoint,
                            "source_cluster": info.cluster,
                            "x_advance_units": position.x_advance,
                            "y_advance_units": position.y_advance,
                            "x_offset_units": position.x_offset,
                            "y_offset_units": position.y_offset,
                        }
                    )
                base = {
                    "schema_version": "template-original-source-html-contextual-shaping-v1",
                    "font_sha256": hashlib.sha256(font_bytes).hexdigest(),
                    "face_index": face_index,
                    "original_text": text,
                    "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "units_per_em": upem,
                    "glyphs": glyphs,
                    "direction": "ltr",
                    "features": {"kern": kerning, "liga": ligatures, "clig": ligatures},
                    "physical_provider": self.physical_before,
                    "actual_provider_symbols": self.symbols_before,
                    "provider_version": library.hb_version_string().decode("ascii"),
                    "blockers": [
                        "Chromium consumed shaper equivalence and loaded dependencies "
                        "remain outside this physical provider witness"
                    ],
                }
                return {**base, "digest": canonical_digest(base)}
        except BaseException as error:
            original = error
            raise
        finally:
            for value, destructor in (
                (buffer, "hb_buffer_destroy"),
                (font, "hb_font_destroy"),
                (face, "hb_face_destroy"),
                (blob, "hb_blob_destroy"),
            ):
                if value:
                    getattr(library, destructor)(value)
            try:
                self.close(deadline=deadline)
            except BaseException as error:
                if original is None:
                    raise
                original.add_note("Source shaping provider closing error: " + str(error))


def select_source_html_shaper(*, deadline: float) -> SourceHTMLShaper:
    """Choose only a Source-owned physical nomination, then verify real symbols."""
    _clock(deadline)
    for nominated in _NOMINATIONS.get(sys.platform, ()):
        path = Path(nominated)
        if not path.is_file():
            continue
        selected = path.resolve(strict=True)
        before = _physical(selected, deadline=deadline)
        library = ctypes.CDLL(str(selected))
        _configure(library)
        symbols = _provider_symbols(library, selected, deadline=deadline)
        result = SourceHTMLShaper(_TOKEN, os.getpid(), library, before, symbols)
        result.close(deadline=deadline)
        return result
    raise ValueError("actual platform lacks a Source-nominated independently physical HarfBuzz shaping provider")


def shape_physical_source_font(
    font_bytes: bytes,
    face_index: int,
    requested_font: dict[str, Any],
    *,
    deadline: float,
) -> dict[str, Any] | None:
    """Actual platform probe child consumes Source-requested complete text runs."""
    runs = requested_font.get("contextual_runs", [])
    if not isinstance(runs, list) or sum(len(row["text"]) for row in runs) > 200000:
        raise ValueError("Source contextual font request exceeds the original aggregate text bound")
    if not runs:
        return None
    provider = select_source_html_shaper(deadline=deadline)
    rows = []
    for run in runs:
        _clock(deadline)
        if not isinstance(run["source_id"], str) or not isinstance(run["text"], str):
            raise ValueError("Source contextual font run omitted its original occurrence/text")
        shaped = provider.shape(font_bytes, face_index, run["text"], deadline=deadline)
        shaped.pop("digest")
        shaped.pop("actual_provider_symbols")
        shaped.pop("physical_provider")
        shaped["digest"] = canonical_digest(shaped)
        rows.append(
            {
                "source_id": run["source_id"],
                "source_run_id": run["source_run_id"],
                "source_start": run["source_start"],
                "source_end": run["source_end"],
                "shaping": shaped,
            }
        )
    provider.close(deadline=deadline)
    return {
        "runs": rows,
        "physical_provider_before": provider.physical_before,
        "physical_provider_after": _physical(Path(provider.physical_before["path"]), deadline=deadline),
        "actual_provider_symbols_before": provider.symbols_before,
        "actual_provider_symbols_after": _provider_symbols(
            provider.library, Path(provider.physical_before["path"]), deadline=deadline
        ),
    }
