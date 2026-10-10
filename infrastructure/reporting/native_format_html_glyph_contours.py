"""Original character occurrences and independent admitted-font glyph contours."""

from __future__ import annotations

import hashlib
import math
import time
import unicodedata
from io import BytesIO
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_acceptance_contracts import (
    native_deadline_guard,
)
from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes
from infrastructure.reporting.native_format_html_source_metadata import (
    remaining_seconds,
)
from infrastructure.reporting.native_format_html_source_styles import (
    expected_source_text_style,
)

GLYPH_SOURCE_SCHEMA = "template-native-html-source-character-runs-v1"
FONT_CONTOUR_SCHEMA = "template-native-html-admitted-font-contours-v1"
GLYPH_STYLE_SCRIPT = r"""
 globalThis.__native_glyph_text_nodes=textNodes;
 for(const [i,n] of textNodes.entries()){
  const p=n.parentElement,s=getComputedStyle(p),ancestors=[];
  for(let a=p;a;a=a.parentElement)ancestors.push(a);
  rows[i].glyph_style={font_family:s.fontFamily,font_size:s.fontSize,font_weight:s.fontWeight,font_style:s.fontStyle,
   font_stretch:s.fontStretch,font_kerning:s.fontKerning,font_ligatures:s.fontVariantLigatures,
   font_features:s.fontFeatureSettings,font_variations:s.fontVariationSettings,font_synthesis:s.fontSynthesis,
   letter_spacing:s.letterSpacing,word_spacing:s.wordSpacing,text_transform:s.textTransform,text_shadow:s.textShadow,
   text_decoration:s.textDecorationLine,color:s.color,direction:s.direction,writing_mode:s.writingMode,
   effects:ancestors.map(a=>{const z=getComputedStyle(a);
    return {opacity:z.opacity,filter:z.filter,transform:z.transform,
    mix_blend_mode:z.mixBlendMode,mask_image:z.maskImage,clip_path:z.clipPath,
    background_image:z.backgroundImage,background_color:z.backgroundColor};})};
  const title=p.closest('header#title-block-header .title'),
   subtitle=p.closest('header#title-block-header .subtitle'),author=p.closest('header#title-block-header .author');
  rows[i].glyph_flow=title?'meta:title':subtitle?'meta:subtitle':author?'meta:author:'+
   ([...document.querySelectorAll('header#title-block-header .author')].indexOf(author)+1):null;
 }
"""


def compile_source_character_runs(
    ast_bytes: bytes,
    metadata_source: dict[str, Any] | None = None,
    *,
    source_styles: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Keep exact visible source codepoints; unknown projections stay obligated.

    Caller supplies the current independently parsed admitted source AST, never
    an AST reconstructed from candidate DOM or pixels. Original-survival and
    other semantic obligations remain owned by the enclosing source reader.
    """
    from infrastructure.reporting.native_format_html_image_alt import figure_caption_image_aliases

    aliases = figure_caption_image_aliases(ast_bytes)
    document = json_object_from_bytes(ast_bytes)
    runs: list[dict[str, Any]] = []
    blockers: list[str] = []
    notes: list[tuple[Any, str]] = []
    count = 0

    def add(text: str, path: str, flow: str, ancestry: list[str] | None = None) -> None:
        nonlocal count
        count += len(text)
        if count > 200000:
            raise ValueError("complete source character occurrences exceed the existing finite bound")
        style = expected_source_text_style(source_styles, ancestry or []) if source_styles is not None else None
        if style is not None:
            blockers.extend(style["blockers"])
        runs.append(
            {
                "source_id": "glyph-source:" + path,
                "flow": flow,
                "text": text,
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                **({"source_style": style} if style is not None else {}),
            }
        )

    def walk(value: Any, path: str, flow: str, depth: int = 0, ancestry: tuple[str, ...] = ()) -> None:
        if depth > 64:
            raise ValueError("source glyph node nesting exceeds the existing bound")
        if isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + "/" + str(index), flow, depth + 1, ancestry)
        elif isinstance(value, dict):
            content: Any
            tag, content = value.get("t"), value.get("c")
            role = "Header:" + str(content[0]) if tag == "Header" else tag
            inherited = (*ancestry, role) if isinstance(role, str) else ancestry
            if tag == "Str" and isinstance(content, str):
                add(content, path, flow, list(inherited))
            elif tag in {"Code", "CodeBlock"}:
                add(content[1], path, flow, list(inherited))
            elif tag == "Note":
                notes.append((content, path))
            elif tag == "Math":
                blockers.append(f"{path}: MathJax shaping/contours require an independent source math glyph reference")
            elif tag == "Image" and path in aliases:
                return  # Exact alternative attribute; visible caption has its own traversal.
            elif tag == "Image":
                blockers.append(
                    f"{path}: image caption/alternative glyph placement needs authenticated writer projection"
                )
            elif tag == "Figure":
                if (
                    not isinstance(content, list)
                    or len(content) != 3
                    or not isinstance(content[1], list)
                    or len(content[1]) != 2
                    or not isinstance(content[1][1], list)
                    or not isinstance(content[2], list)
                ):
                    raise ValueError("Source Figure glyph projection requires the actual modern caption/body shape")
                if content[1][0] is not None:
                    blockers.append(f"{path}: figure short-caption glyph placement needs a specific writer model")
                # Actual painted caption and Image alternative remain distinct
                # Source roles. Traverse both body and visible caption; Image's
                # existing alternative-placement refusal is retained unchanged.
                walk(content[1][1], path + "/c/1/1", flow, depth + 1, inherited)
                walk(content[2], path + "/c/2", flow, depth + 1, inherited)
            elif tag in {"Space", "SoftBreak", "LineBreak", "HorizontalRule", "Null"}:
                if source_styles is not None and tag in {
                    "Space",
                    "SoftBreak",
                    "LineBreak",
                }:
                    add("\n" if tag == "LineBreak" else " ", path, flow, list(ancestry))
                return
            elif tag == "Quoted":
                double = content[0].get("t") == "DoubleQuote"
                add(
                    "“" if double else "‘",
                    path + "/opening-quote",
                    flow,
                    list(inherited),
                )
                walk(content[1], path + "/c/1", flow, depth + 1, inherited)
                add(
                    "”" if double else "’",
                    path + "/closing-quote",
                    flow,
                    list(inherited),
                )
            elif tag in {"Link", "Span", "Cite"}:
                if tag == "Cite":
                    blockers.append(
                        f"{path}: citation glyph expansion needs original-to-projected source occurrence proof"
                    )
                walk(content[1], path + "/c/1", flow, depth + 1, inherited)
            elif tag == "Header":
                walk(content[2], path + "/c/2", flow, depth + 1, inherited)
            elif tag in {
                "Para",
                "Plain",
                "Emph",
                "Strong",
                "Underline",
                "Strikeout",
                "SmallCaps",
                "Superscript",
                "Subscript",
                "BlockQuote",
                "BulletList",
            }:
                walk(content, path + "/c", flow, depth + 1, inherited)
            elif tag == "OrderedList":
                walk(content[1], path + "/c/1", flow, depth + 1, inherited)
            elif tag == "Div":
                walk(content[1], path + "/c/1", flow, depth + 1, inherited)
            elif tag == "Table":
                if not isinstance(content, list) or len(content) != 6:
                    blockers.append(f"{path}: legacy table glyph order requires specific source projection")
                    return
                if content[1][0]:
                    blockers.append(f"{path}: table short-caption glyph placement needs a specific writer model")
                walk(content[1][1], path + "/c/1/1", flow, depth + 1, inherited)

                def table_rows(
                    rows: Any, section_path: str, *, all_headers: bool = False, row_head_columns: int = 0
                ) -> None:
                    for index, row in enumerate(rows):
                        for column, cell in enumerate(row[1]):
                            walk(
                                cell[4],
                                section_path + f"/{index}/1/{column}/4",
                                flow,
                                depth + 1,
                                (*inherited, "TableHead")
                                if all_headers
                                else (*inherited, "TableRowHead")
                                if column < row_head_columns
                                else inherited,
                            )

                table_rows(content[3][1], path + "/c/3/1", all_headers=True)
                for index, body in enumerate(content[4]):
                    for offset in (2, 3):
                        table_rows(
                            body[offset],
                            path + f"/c/4/{index}/{offset}",
                            all_headers=offset == 2,
                            row_head_columns=body[1] if offset == 3 else 0,
                        )
                table_rows(content[5][1], path + "/c/5/1")
            elif tag is None:
                for key, child in value.items():
                    walk(child, path + "/" + key, flow, depth + 1, inherited)
            else:
                blockers.append(f"{path}: source glyph projection of {tag} requires a specific independent model")

    walk(document.get("blocks"), "blocks", "body")
    cursor = 0
    while cursor < len(notes):
        content, path = notes[cursor]
        cursor += 1
        walk(content, path + "/c", "note:" + str(cursor))
    if metadata_source is not None:
        if metadata_source.get("digest") != canonical_digest(
            {key: value for key, value in metadata_source.items() if key != "digest"}
        ):
            raise ValueError("authenticated separate source metadata digest changed")
        authors = 0
        for row in metadata_source["records"]:
            if row["native"] not in {"title_block", "subtitle", "author"}:
                continue
            if "native_text" not in row:
                blockers.append(row["source_id"] + ": metadata glyphs need actual source AST placement text")
                continue
            if row["native"] == "author":
                authors += 1
                flow = "meta:author:" + str(authors)
            else:
                flow = "meta:title" if row["native"] == "title_block" else "meta:subtitle"
            add(
                row["native_text"],
                row["source_id"],
                flow,
                ["Header:1"] if row["native"] == "title_block" else ["Para"],
            )
        blockers.extend(metadata_source["blockers"])
    result: dict[str, Any] = {
        "schema_version": GLYPH_SOURCE_SCHEMA,
        "source_ast_sha256": hashlib.sha256(ast_bytes).hexdigest(),
        "metadata_source_digest": metadata_source["digest"] if metadata_source else None,
        "runs": runs,
        "blockers": blockers,
    }
    if source_styles is not None:
        result["source_style_profile"] = source_styles
        result["blockers"].extend(source_styles["blockers"])
    return {**result, "digest": canonical_digest(result)}


def map_source_character_runs(source: dict[str, Any], dom: dict[str, Any]) -> dict[str, Any]:
    """Map every source codepoint to genuine native character coordinates."""
    if source.get("schema_version") != GLYPH_SOURCE_SCHEMA or source.get("digest") != canonical_digest(
        {key: value for key, value in source.items() if key != "digest"}
    ):
        raise ValueError("source glyph character occurrence contract changed")
    streams: dict[str, list[dict[str, Any]]] = {}
    note_ids = {note["id"]: "note:" + str(index + 1) for index, note in enumerate(dom.get("footnotes", []))}
    for index, row in enumerate(dom["text"]):
        if row.get("math_owner"):
            continue
        characters = row.get("characters")
        if not isinstance(characters, list) or "".join(item["character"] for item in characters) != row["text"]:
            raise ValueError("native glyph census omits source text characters")
        flow = row.get("glyph_flow") or note_ids.get(row.get("footnote_id"), "body")
        stream = streams.setdefault(flow, [])
        for offset, item in enumerate(characters):
            if not item["character"].isspace():
                stream.append({"text_index": index, "character_index": offset, **item})
    positions: dict[str, int] = {}
    consumed: dict[str, set[int]] = {}
    mapped = []
    findings = []
    blockers = list(source["blockers"])
    for run in source["runs"]:
        expected = [char for char in run["text"] if not char.isspace()]
        nonspace_positions = [index for index, char in enumerate(run["text"]) if not char.isspace()]
        stream = streams.get(run["flow"], [])
        cursor = positions.get(run["flow"], 0)
        position = next(
            (
                i
                for i in range(cursor, len(stream) - len(expected) + 1)
                if [item["character"] for item in stream[i : i + len(expected)]] == expected
            ),
            None,
        )
        if position is None:
            findings.append({"code": "html.glyph.source-character", "source_id": run["source_id"]})
            continue
        positions[run["flow"]] = position + len(expected)
        consumed.setdefault(run["flow"], set()).update(range(position, position + len(expected)))
        for offset, observed in enumerate(stream[position : position + len(expected)]):
            character = observed["character"]
            identity = run["source_id"] + ":character:" + str(offset)
            boxes = observed["boxes"]
            if source.get("source_style_profile") is None and (
                unicodedata.combining(character) or ord(character) > 0xFFFF or len(boxes) != 1
            ):
                blockers.append(
                    f"{identity}: combining/fallback/multibox glyph shaping requires an independent run model"
                )
            mapped.append(
                {
                    "source_id": identity,
                    **observed,
                    **(
                        {
                            "source_run_id": run["source_id"],
                            "source_style": run["source_style"],
                            "source_character_offset": nonspace_positions[offset],
                        }
                        if "source_style" in run
                        else {}
                    ),
                }
            )
    for flow, stream in streams.items():
        extra = len(stream) - len(consumed.get(flow, set()))
        if extra:
            blockers.append(
                f"{flow}: {extra} native codepoints lack original source glyph attribution; "
                "generated/duplicate/footnote/citation glyph placements require a specific source model"
            )
    return {
        "source_digest": source["digest"],
        "characters": mapped,
        "findings": findings,
        "blockers": blockers,
    }


def admitted_font_contours(
    font_bytes: bytes,
    face_index: int,
    postscript_name: str,
    characters: str,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Derive complete glyph curves from exact genuine platform font bytes.

    This supports bounded static TrueType outlines. CFF programs, variable or
    color fonts, missing cmap glyphs and shaping substitutions remain blocked.
    It never derives an outline from candidate raster, DOM glyph names or bbox
    contrast. Caller authenticates actual platform font-file consumption and
    before/after OS/font/FontTools custody independently.
    """
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.ttLib import TTFont

    if (
        len(font_bytes) > 32 * 1024 * 1024
        or not font_bytes.startswith((b"\x00\x01\x00\x00", b"ttcf", b"OTTO"))
        or type(face_index) is not int
        or not 0 <= face_index < 256
    ):
        raise ValueError("font contours require bounded exact admitted SFNT font bytes")
    remaining_seconds(deadline)
    if len(characters) > 200000:
        raise ValueError("font contour source/clock bounds exhausted")
    with native_deadline_guard(deadline):
        font = TTFont(BytesIO(font_bytes), fontNumber=face_index, lazy=False)
        try:
            if font["name"].getDebugName(6) != postscript_name:
                raise ValueError("native platform PostScript font identity differs from admitted font bytes")
            blockers = []
            glyphs: list[dict[str, Any]] = []
            if not any(name in font for name in ("glyf", "CFF ")) or any(
                name in font for name in ("fvar", "CFF2", "COLR", "CBDT", "sbix", "SVG ")
            ):
                blockers.append("static SFNT contour model does not support variable/CFF2/color glyph programs")
            else:
                cmap = font.getBestCmap() or {}
                glyph_set = font.getGlyphSet()
                for character in dict.fromkeys(characters):
                    if time.monotonic() >= deadline:
                        raise TimeoutError("source glyph contours exhausted the original caller clock")
                    if character.isspace():
                        continue
                    name = cmap.get(ord(character))
                    if name is None or name == ".notdef":
                        blockers.append(f"U+{ord(character):04X}: source font has no independently mapped glyph")
                        continue
                    pen = DecomposingRecordingPen(glyph_set)
                    glyph_set[name].draw(pen)
                    bounds = BoundsPen(glyph_set)
                    glyph_set[name].draw(bounds)
                    if len(pen.value) > 10000:
                        raise ValueError("source glyph contour operation count exceeds its finite bound")
                    glyphs.append(
                        {
                            "character": character,
                            "glyph_name": name,
                            "glyph_id": font.getGlyphID(name),
                            "advance_units": font["hmtx"][name][0],
                            "bounds_units": list(bounds.bounds) if bounds.bounds else None,
                            "commands": pen.value,
                        }
                    )
            result = {
                "schema_version": FONT_CONTOUR_SCHEMA,
                "font_sha256": hashlib.sha256(font_bytes).hexdigest(),
                "font_bytes": len(font_bytes),
                "face_index": face_index,
                "postscript_name": postscript_name,
                "units_per_em": font["head"].unitsPerEm,
                "weight_class": font["OS/2"].usWeightClass if "OS/2" in font else None,
                "italic": bool(font["head"].macStyle & 2),
                "glyphs": glyphs,
                "blockers": blockers,
            }
        finally:
            font.close()
    result = {**result, "digest": canonical_digest(result)}
    remaining_seconds(deadline)
    return result


def contour_paint_bounds(
    glyph: dict[str, Any], font: dict[str, Any], font_px: float, baseline: list[float]
) -> list[float]:
    """Map independent full source outline extent into native baseline coordinates."""
    if (
        not glyph["bounds_units"]
        or len(baseline) != 2
        or not 0 < font_px <= 128
        or any(not math.isfinite(v) for v in [font_px, *baseline])
    ):
        raise ValueError("source glyph lacks bounded full contour/baseline geometry")
    x0, y0, x1, y1 = glyph["bounds_units"]
    scale = font_px / font["units_per_em"]
    return [
        baseline[0] + x0 * scale,
        baseline[1] - y1 * scale,
        (x1 - x0) * scale,
        (y1 - y0) * scale,
    ]


def admitted_shaped_glyph_contours(
    font_bytes: bytes,
    face_index: int,
    postscript_name: str,
    glyph_ids: list[int],
    *,
    deadline: float,
) -> list[dict[str, Any]]:
    """Decode actual shaped glyph IDs from the complete independently read font.

    A ligature or combining substitution is not reconstructed through cmap or
    candidate glyph names. Static TrueType and CFF outlines use the same actual
    Source FontTools pens; variable and color programs remain unsupported.
    """
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.ttLib import TTFont

    remaining_seconds(deadline)
    if len(font_bytes) > 32 * 1024 * 1024 or len(glyph_ids) > 200000 or not 0 <= face_index < 256:
        raise ValueError("complete shaped Source contours exceed their finite font/face/glyph bound")
    with native_deadline_guard(deadline):
        font = TTFont(BytesIO(font_bytes), fontNumber=face_index, lazy=False)
        try:
            if font["name"].getDebugName(6) != postscript_name:
                raise ValueError("Source shaped outlines selected a different physical font face")
            if not any(name in font for name in ("glyf", "CFF ")) or any(
                name in font for name in ("fvar", "CFF2", "COLR", "CBDT", "sbix", "SVG ")
            ):
                raise ValueError("Source contextual outlines need an independently modeled variable/color program")
            order = font.getGlyphOrder()
            glyph_set = font.getGlyphSet()
            rows = []
            for glyph_id in dict.fromkeys(glyph_ids):
                remaining_seconds(deadline)
                if type(glyph_id) is not int or not 0 < glyph_id < len(order):
                    raise ValueError("Source contextual shaping returned an absent/.notdef glyph")
                name = order[glyph_id]
                pen = DecomposingRecordingPen(glyph_set)
                bounds = BoundsPen(glyph_set)
                glyph_set[name].draw(pen)
                glyph_set[name].draw(bounds)
                if len(pen.value) > 10000:
                    raise ValueError("complete contextual Source outline exceeds the original per-glyph bound")
                rows.append(
                    {
                        "glyph_id": glyph_id,
                        "glyph_name": name,
                        "commands": pen.value,
                        "bounds_units": list(bounds.bounds) if bounds.bounds else None,
                    }
                )
            return rows
        finally:
            font.close()
