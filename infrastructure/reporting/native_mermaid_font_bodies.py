"""Live independently nominated Source font bodies, separate from OS shaping.

The factory holds exact original file bytes and physical observations under the
actual Source producer. Browser font labels never nominate paths. This body
capability grants neither platform selection nor loaded-library/kernel proof.
"""

from __future__ import annotations

import hashlib
import io
import json
import stat
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTCollection, TTFont

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_html_source_shaping import SourceHTMLShaper
from infrastructure.reporting.native_mermaid_runtime_custody import (
    FONT_SCHEMA,
    MAX_FONT_BYTES,
    _font_names,
)
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.native_tool_producer import (
    NativeProducerOperation,
    current_native_producer_operation,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

_SEAL = object()


@dataclass(frozen=True)
class NativeMermaidFontSelection:
    """Independent caller nominations; no artifact constructor or discovery."""

    files: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not 0 < len(self.files) <= 2048 or any(not path.is_absolute() for path in self.files):
            raise ValueError("Source Mermaid font bodies require bounded explicit absolute nominees")


def _identity(path: Path) -> tuple[int, int, int, int, int, int, int]:
    observed = path.stat()
    if not stat.S_ISREG(observed.st_mode):
        raise ValueError("Source Mermaid nominated font body is not a regular file")
    return (
        observed.st_dev,
        observed.st_ino,
        observed.st_mode,
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_ctime_ns,
        observed.st_nlink,
    )


@dataclass(frozen=True)
class _OriginalFontBody:
    path: Path
    content: bytes
    identity: tuple[int, int, int, int, int, int, int]
    sha256: str
    names: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class NativeMermaidFontBodies:
    """Exact Source data/body owner; deliberately not a whole-font admission."""

    source: NativeSourceContext
    producer: NativeProducerOperation
    deadline: float
    files: tuple[_OriginalFontBody, ...]
    _seal: object
    _decoded_fonts: dict[tuple[str, int], TTFont] = field(default_factory=dict, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self._seal is not _SEAL:
            raise ValueError("Source font body owner requires its genuine current factory")

    def verify_live(self, *, deadline: float) -> None:
        remaining(deadline)
        if self._closed or deadline > self.deadline or current_native_producer_operation() is not self.producer:
            raise ValueError("Source font bodies lost actual live owner or inherited clock")
        if self.producer.source is not self.source or any(_identity(row.path) != row.identity for row in self.files):
            raise ValueError("Source nominated font physical identities changed during actual operation")

    def verify_terminal_bytes(self, *, deadline: float) -> None:
        self.verify_live(deadline=deadline)
        for row in self.files:
            remaining(deadline)
            if read_bytes_confined(row.path.parent, row.path, max_bytes=MAX_FONT_BYTES) != row.content:
                raise ValueError("Source nominated whole font bytes changed during original operation")
        self.verify_live(deadline=deadline)

    def face_bytes(self, postscript_name: str, *, deadline: float) -> tuple[bytes, int]:
        """Actual held body and exact face index for an independent Source shaper."""
        self.verify_live(deadline=deadline)
        matches = [(row, index) for row in self.files for name, index in row.names if name == postscript_name]
        if not matches or len({(row.sha256, index) for row, index in matches}) != 1:
            raise ValueError("Source declared physical face has missing/ambiguous body ownership: " + postscript_name)
        row, index = matches[0]
        return row.content, index

    def close(self) -> None:
        for font in self._decoded_fonts.values():
            font.close()
        self._decoded_fonts.clear()
        object.__setattr__(self, "_closed", True)

    def portable_fonts(self, platform_fonts: list[dict[str, Any]], *, deadline: float) -> dict[str, Any]:
        """Match actual Source-browser usage to held bodies; paths stay private.

        The caller must separately own the real browser's usage observations.
        Matching a passed label alone never supplies native font selection.
        """
        self.verify_live(deadline=deadline)
        faces = []
        for name in sorted(_font_names(platform_fonts)):
            body, index = self.face_bytes(name, deadline=deadline)
            faces.append(
                {
                    "postscript_name": name,
                    "face_index": index,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                }
            )
        result = {
            "schema_version": FONT_SCHEMA,
            "platform_fonts": platform_fonts,
            "font_faces": faces,
        }
        return {**result, "content_digest": canonical_digest(result)}

    def unshaped_glyph_bodies(self, name: str, text: str, *, deadline: float) -> dict[str, Any]:
        """Decode every original codepoint outline; do not pretend it is shaping."""
        if not isinstance(text, str) or not 0 < len(text) <= 100_000:
            raise ValueError("Source glyph body request must preserve bounded actual original text")
        body, face_index = self.face_bytes(name, deadline=deadline)
        key = (hashlib.sha256(body).hexdigest(), face_index)
        font = self._decoded_fonts.get(key)
        if font is None:
            font = TTFont(io.BytesIO(body), fontNumber=face_index, lazy=False)
            self._decoded_fonts[key] = font
        try:
            if "fvar" in font or "COLR" in font or "CBDT" in font or "sbix" in font:
                raise ValueError("Source glyph body needs an explicitly modeled variable/color outline profile")
            cmap = font.getBestCmap()
            if cmap is None:
                raise ValueError("Source nominated physical face has no supported Unicode cmap")
            glyphs = font.getGlyphSet()
            rows = []
            for ordinal, character in enumerate(text):
                remaining(deadline)
                glyph_name = cmap.get(ord(character))
                if glyph_name is None:
                    rows.append(
                        {
                            "ordinal": ordinal,
                            "character": character,
                            "status": "missing-source-face-cmap",
                        }
                    )
                    continue
                recorded, bounds = RecordingPen(), BoundsPen(glyphs)
                glyphs[glyph_name].draw(recorded)
                glyphs[glyph_name].draw(bounds)
                rows.append(
                    {
                        "ordinal": ordinal,
                        "character": character,
                        "glyph_name": glyph_name,
                        "glyph_id": font.getGlyphID(glyph_name),
                        "commands": recorded.value,
                        "unpositioned_ink_bounds": bounds.bounds,
                        "status": "original-outline-observed",
                    }
                )
            result = {
                "schema_version": "template-native-source-mermaid-unshaped-font-glyph-bodies-v1",
                "postscript_name": name,
                "font_sha256": hashlib.sha256(body).hexdigest(),
                "face_index": face_index,
                "units_per_em": font["head"].unitsPerEm,
                "original_text": text,
                "glyphs": rows,
                "full_shaping_or_ink_admission": False,
                "remaining_admission": [
                    "actual independently admitted shaping/font selection",
                    "Source/native complete ink positions and platform runtime custody",
                ],
            }
            # Preserve exact native observation values as portable DATA. Pen
            # tuples must compare with their JSON-retained list counterparts;
            # this serialization constructs no font or process authority.
            portable = json.loads(json.dumps(result))
            return {**portable, "content_digest": canonical_digest(portable)}
        finally:
            self.verify_live(deadline=deadline)

    def shaped_source_glyph_bodies(
        self,
        shaper: SourceHTMLShaper,
        name: str,
        text: str,
        *,
        deadline: float,
    ) -> dict[str, Any]:
        """Consume the actual Source shaper and exact held face, in font units.

        These are genuinely shaped contours and pen positions. They remain
        independent Source observations: actual Chrome selection, rich inline
        line placement, CSS effects and whole-document ink stay unadmitted.
        """
        self.verify_live(deadline=deadline)
        if not isinstance(shaper, SourceHTMLShaper) or not 0 < len(text) <= 100_000:
            raise ValueError("Source shaped glyph bodies require actual live shaper and original bounded text")
        body, face_index = self.face_bytes(name, deadline=deadline)
        shaped = shaper.shape(body, face_index, text, deadline=deadline, kerning=True, ligatures=True)
        if (
            shaped["font_sha256"] != hashlib.sha256(body).hexdigest()
            or shaped["face_index"] != face_index
            or shaped["original_text"] != text
            or shaped["text_sha256"] != hashlib.sha256(text.encode()).hexdigest()
            or shaped["direction"] != "ltr"
            or shaped["features"] != {"kern": True, "liga": True, "clig": True}
            or shaped["digest"] != canonical_digest({k: v for k, v in shaped.items() if k != "digest"})
        ):
            raise ValueError("actual Source shaping observation differs from exact held font/text/feature inputs")
        # Source must consume the actual native results, rather than attach a
        # provider label to a per-codepoint approximation.
        key = (hashlib.sha256(body).hexdigest(), face_index)
        font = self._decoded_fonts.get(key)
        if font is None:
            font = TTFont(io.BytesIO(body), fontNumber=face_index, lazy=False)
            self._decoded_fonts[key] = font
        if "fvar" in font or "COLR" in font or "CBDT" in font or "sbix" in font:
            raise ValueError("Source shaping needs an explicitly modeled variable/color outline profile")
        if shaped["units_per_em"] != font["head"].unitsPerEm:
            raise ValueError("actual Source shaper/held face use different glyph coordinate units")
        glyphs = font.getGlyphSet()
        rows = []
        pen_x = pen_y = 0
        for ordinal, native in enumerate(shaped["glyphs"]):
            remaining(deadline)
            glyph_name = font.getGlyphName(native["glyph_id"])
            recorded, bounds = RecordingPen(), BoundsPen(glyphs)
            glyphs[glyph_name].draw(recorded)
            glyphs[glyph_name].draw(bounds)
            offset_x, offset_y = pen_x + native["x_offset_units"], pen_y + native["y_offset_units"]
            placed_bounds = (
                None
                if bounds.bounds is None
                else [
                    bounds.bounds[0] + offset_x,
                    bounds.bounds[1] + offset_y,
                    bounds.bounds[2] + offset_x,
                    bounds.bounds[3] + offset_y,
                ]
            )
            rows.append(
                {
                    "ordinal": ordinal,
                    "glyph_name": glyph_name,
                    "native_shape": native,
                    "pen_origin_units": [pen_x, pen_y],
                    "glyph_origin_units": [offset_x, offset_y],
                    "original_contour_commands": recorded.value,
                    "shaped_ink_bounds_units": placed_bounds,
                }
            )
            pen_x += native["x_advance_units"]
            pen_y += native["y_advance_units"]
        self.verify_live(deadline=deadline)
        reference = json.loads(
            json.dumps(
                {
                    "schema_version": "template-native-source-mermaid-shaped-glyph-bodies-v1",
                    "postscript_name": name,
                    "font_sha256": key[0],
                    "face_index": face_index,
                    "units_per_em": shaped["units_per_em"],
                    "original_text": text,
                    "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "features": shaped["features"],
                    "glyphs": rows,
                    "terminal_pen_units": [pen_x, pen_y],
                    "full_platform_font_or_ink_admission": False,
                    "remaining_admission": [
                        "actual source browser font selection and shaping-provider equivalence",
                        "Source rich inline line layout/glyph baseline placement and CSS effects",
                        "complete unclipped whole-document ink and Source-required loaded-library/cache/kernel custody",
                    ],
                }
            )
        )
        result = {
            "reference": reference,
            "actual_shape_observation": shaped,
        }
        return {**result, "content_digest": canonical_digest(result)}


def admit_source_mermaid_font_bodies(
    selection: NativeMermaidFontSelection,
    source: NativeSourceContext,
    *,
    deadline: float,
) -> NativeMermaidFontBodies:
    """Hold independently nominated exact whole bodies under actual Source."""
    remaining(deadline)
    producer = current_native_producer_operation()
    if not isinstance(selection, NativeMermaidFontSelection) or not isinstance(source, NativeSourceContext):
        raise ValueError("Source font bodies need genuine typed Source and independent nominees")
    if producer is None or producer.source is not source:
        raise ValueError("Source font bodies need their actual current Source producer")
    producer.verify(
        SnapshotReader(source.bindings.current_root),
        run_id=source.bindings.run_id,
        deadline=deadline,
    )
    originals = []
    total = 0
    for path in sorted({path.resolve(strict=True) for path in selection.files}):
        remaining(deadline)
        before = _identity(path)
        total += before[3]
        if total > MAX_FONT_BYTES:
            raise ValueError("Source nominated whole font bodies exceed existing128MiB aggregate cap")
        content = read_bytes_confined(path.parent, path, max_bytes=MAX_FONT_BYTES)
        if len(content) != before[3] or _identity(path) != before:
            raise ValueError("Source nominated font body changed during genuine read")
        magic = content[:4]
        if magic not in {b"ttcf", b"OTTO", b"\x00\x01\x00\x00", b"true", b"typ1"}:
            raise ValueError("Source nominated font requires an unsupported table decoder")
        collection = TTCollection(io.BytesIO(content), lazy=False) if magic == b"ttcf" else None
        single = None if collection is not None else TTFont(io.BytesIO(content), lazy=False)
        faces = collection.fonts if collection is not None else [single]
        names = []
        try:
            if not 0 < len(faces) <= 256:
                raise ValueError("Source nominated font collection exceeds its existing face bound")
            for index, face in enumerate(faces):
                remaining(deadline)
                if face is None:
                    raise ValueError("Source nominated font face is absent")
                name = face["name"].getDebugName(6)
                if isinstance(name, str) and name:
                    names.append((name, index))
        finally:
            if collection is not None:
                collection.close()
            elif single is not None:
                single.close()
        if _identity(path) != before:
            raise ValueError("Source nominated font body changed during independent face decoding")
        originals.append(_OriginalFontBody(path, content, before, hashlib.sha256(content).hexdigest(), tuple(names)))
    admitted = NativeMermaidFontBodies(source, producer, deadline, tuple(originals), _SEAL)
    admitted.verify_terminal_bytes(deadline=deadline)
    return admitted


@contextmanager
def source_mermaid_font_bodies_operation(
    selection: NativeMermaidFontSelection,
    source: NativeSourceContext,
    *,
    deadline: float,
) -> Iterator[NativeMermaidFontBodies]:
    owner = admit_source_mermaid_font_bodies(selection, source, deadline=deadline)
    try:
        yield owner
    finally:
        try:
            owner.verify_terminal_bytes(deadline=deadline)
        finally:
            owner.close()
