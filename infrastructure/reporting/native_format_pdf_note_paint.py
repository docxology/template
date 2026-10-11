"""Original literal Note bodies, source-only counters and actual anchor paint.

The caller admits the original whole-source SDK/FLS/hydration/process custody.
This leaf rebuilds source instrumentation, understands literal Note text and
checks both native anchor and body glyphs at independently admitted positions.
"""

from __future__ import annotations

import hashlib
import math
import re
import time
from collections.abc import Callable
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_content_contracts import text_tokens
from infrastructure.reporting.native_format_pdf_positions import source_math_paint_from_pdf
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_format_pdf_semantic_plan import PDFSemanticPlan
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams

SCHEMA = "template-native-pdf-independent-note-paint-v1"
PREAMBLE = r"""
\makeatletter
\DeclareRobustCommand\NativeSourceNoteAnchorBegin[1]{\special{pdf:code /Span <</MCID #1>> BDC}}
\DeclareRobustCommand\NativeSourceNoteBodyBegin[2]{%
\special{pdf:code /Span <</MCID #2>> BDC}%
\immediate\write\@auxout{\string\NativeSourceNoteNumber{#1}{\thefootnote}}}
\DeclareRobustCommand\NativeSourceNoteEnd{\special{pdf:code EMC}}
\newcommand\NativeSourceNoteNumber[2]{}
\makeatother
"""


def _literal_tex(body: str) -> str:
    """Refuse macro/math/formatting behavior outside the current literal Note."""
    result = []
    index = 0
    while index < len(body):
        char = body[index]
        if char == "\\":
            if body[index + 1 : index + 2] not in {"%", "&", "#", "_", "{", "}", "$"}:
                raise ValueError("original Note body requires additional native scientific/macro interpretation")
            result.append(body[index + 1])
            index += 2
        else:
            if char in {"{", "}", "$", "%", "^", "~"}:
                raise ValueError("original Note body is not independently literal TeX")
            result.append(char)
            index += 1
    return "".join(result)


def instrument_original_source_notes(tex: str, plan: PDFSemanticPlan) -> tuple[str, tuple[dict[str, Any], ...]]:
    """Bind every current literal original Note to a direct source footnote."""
    if len(tex.encode()) > 4 * 1024 * 1024 or "NativeSourceNote" in tex or tex.count(r"\begin{document}") != 1:
        raise ValueError("original Note source is unbounded or has a reserved/ambiguous boundary")
    notes = [row for row in plan.occurrences if row["kind"] == "Note"]
    if len(notes) > 1000:
        raise ValueError("original Note occurrence bound exceeded")
    start = tex.index(r"\begin{document}") + len(r"\begin{document}")
    body = tex[start:]
    if re.search(r"\\footnote(?:mark|text)|\\footnote\s*\[", body):
        raise ValueError("split/explicit-number source footnotes require separate original interpretation")
    matches = list(re.finditer(r"\\footnote\s*\{", body))
    if len(matches) != len(notes):
        raise ValueError("original source TeX footnote and Note identities differ")
    bindings = []
    replacements = []
    for ordinal, (note, match) in enumerate(zip(notes, matches, strict=True)):
        prefix = body[body.rfind("\n", 0, match.start()) + 1 : match.start()]
        if re.search(r"(?<!\\)%", prefix):
            raise ValueError("original Note locator encountered ambiguous commented TeX")
        begin = start + match.end()
        end = begin
        depth = 1
        while end < len(tex) and depth:
            if tex[end] == "\\":
                end += 2
                continue
            depth += (tex[end] == "{") - (tex[end] == "}")
            end += 1
        if depth or end - begin > 64 * 1024:
            raise ValueError("original Note body has an unbalanced/unbounded group")
        content = tex[begin : end - 1]
        token_groups = [block.tokens for block in plan.notes if block.id.startswith(note["identity"] + "/")]
        source_tokens = tuple(token for group in token_groups for token in group)
        if not source_tokens or text_tokens(_literal_tex(content)) != source_tokens:
            raise ValueError("original source footnote differs from independently interpreted Note text")
        marker = f"N{ordinal:06d}"
        anchor_mcid, body_mcid = 100000 + ordinal * 2, 100001 + ordinal * 2
        bindings.append(
            {
                "identity": note["identity"],
                "marker": marker,
                "anchor_mcid": anchor_mcid,
                "body_mcid": body_mcid,
                "source_tokens": list(source_tokens),
                "source_tex_body_sha256": hashlib.sha256(content.encode()).hexdigest(),
            }
        )
        replacements.extend(
            [
                (start + match.start(), r"\NativeSourceNoteAnchorBegin{" + str(anchor_mcid) + "}"),
                (begin, r"\NativeSourceNoteBodyBegin{" + marker + "}{" + str(body_mcid) + "}"),
                (end - 1, r"\NativeSourceNoteEnd"),
                (end, r"\NativeSourceNoteEnd"),
            ]
        )
    for offset, insertion in sorted(replacements, reverse=True):
        tex = tex[:offset] + insertion + tex[offset:]
    return tex.replace(r"\begin{document}", PREAMBLE + "\n" + r"\begin{document}", 1), tuple(bindings)


def _native_tokens(glyphs: list[dict[str, Any]]) -> tuple[str, ...]:
    parts = []
    previous = None
    for glyph in glyphs:
        if previous is not None and (
            abs(float(glyph["top"]) - float(previous["top"])) > 1
            or float(glyph["x0"]) - float(previous["x1"]) > min(float(glyph["size"]), float(previous["size"])) * 0.12
        ):
            parts.append(" ")
        parts.append(str(glyph["text"]))
        previous = glyph
    return tuple(text_tokens("".join(parts)))


def _font(glyph: dict[str, Any]) -> str:
    return re.sub(r"^[A-Z]{6}\+", "", str(glyph["fontname"]))


def inspect_pdf_original_note_paint(
    pdf: bytes,
    rasters: tuple[bytes, ...],
    plan: PDFSemanticPlan,
    *,
    source_tex: bytes,
    source_marked_tex: bytes,
    source_marked_pdf: bytes,
    source_marked_aux: bytes,
    source_marked_rasters: tuple[bytes, ...],
    original_reference_pdf: bytes,
    original_reference_rasters: tuple[bytes, ...],
    deadline: float,
    additional_paint_bindings: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """Recompute source identity, native counters, anchor/body glyphs and parity."""
    import pdfplumber

    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("original Note observer requires a finite current deadline")
    if sum(map(len, (*rasters, *source_marked_rasters, *original_reference_rasters))) > 256 * 1024 * 1024:
        raise ValueError("original Note aggregate raster byte bound exceeded")
    expected, bindings = instrument_original_source_notes(source_tex.decode(), plan)
    if source_marked_tex != expected.encode():
        raise ValueError("original source Note instrumentation bytes differ")
    if len(source_marked_aux) > 8 * 1024 * 1024:
        raise ValueError("original Note source counter recorder exceeds finite bound")
    counters = {}
    for line in source_marked_aux.decode().splitlines():
        if not line.startswith(r"\NativeSourceNoteNumber"):
            continue
        match = re.fullmatch(r"\\NativeSourceNoteNumber\{(N[0-9]{6})\}\{([1-9][0-9]{0,5})\}", line)
        if match is None or match[1] in counters:
            raise ValueError("original Note source counter is duplicate/nonliteral")
        counters[match[1]] = match[2]
    if set(counters) != {row["marker"] for row in bindings}:
        raise ValueError("original Note source counter identity differs")
    paint_bindings = tuple(
        {"identity": row["identity"] + "/" + kind, "mcid": row[kind + "_mcid"]}
        for row in bindings
        for kind in ("anchor", "body")
    )
    paint = source_math_paint_from_pdf(
        source_marked_pdf, (*paint_bindings, *additional_paint_bindings), deadline=deadline
    )
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in paint:
        groups.setdefault(row["identity"], []).append(row)
    noninterference = inspect_pdf_reference_parity(
        original_reference_pdf,
        source_marked_pdf,
        original_reference_rasters,
        source_marked_rasters,
        deadline=deadline,
    )
    parity = inspect_pdf_reference_parity(
        pdf, original_reference_pdf, rasters, original_reference_rasters, deadline=deadline
    )
    preflight_pdf_streams(pdf, deadline=deadline, max_objects=4_000_000)
    findings = [*noninterference["findings"], *parity["findings"]]
    blockers = []
    observations = []
    consumed = set()
    glyph_indexes: dict[int, dict[tuple[Any, ...], list[tuple[int, dict[str, Any]]]]] = {}
    with pdfplumber.open(BytesIO(pdf)) as document:
        if not document.pages or len(document.pages) > 500 or len(document.pages) != len(rasters):
            raise ValueError("original Note observer requires bounded every-page native rasters")
        if sum(len(page.chars) for page in document.pages) > 2_000_000:
            raise ValueError("original Note native glyph bound exceeded")
        for binding in bindings:
            for kind in ("anchor", "body"):
                rows = groups.get(binding["identity"] + "/" + kind, [])
                if len(rows) != 1 or not rows[0]["glyphs"] or rows[0]["vectors"]:
                    blockers.append(
                        f"{binding['identity']}: split/empty/vector Note {kind} requires independent interpretation"
                    )
                    continue
                row = rows[0]
                wanted_tokens = (counters[binding["marker"]],) if kind == "anchor" else tuple(binding["source_tokens"])
                if _native_tokens(row["glyphs"]) != wanted_tokens:
                    findings.append({"code": "pdf.note.source.literal", "identity": binding["identity"], "kind": kind})
                    continue
                page = document.pages[row["page"] - 1] if 1 <= row["page"] <= len(document.pages) else None
                if page is None or page.rotation or page.mediabox[:2] != (0, 0):
                    blockers.append(f"{binding['identity']}: Note page/origin requires independent interpretation")
                    continue
                if row["page"] not in glyph_indexes:
                    glyph_index: dict[tuple[Any, ...], list[tuple[int, dict[str, Any]]]] = {}
                    for index, actual in enumerate(page.chars):
                        if index % 1024 == 0 and time.monotonic() >= deadline:
                            raise TimeoutError("original Note native glyph index deadline exhausted")
                        key = (
                            actual["text"],
                            _font(actual),
                            round(float(actual["x0"]) * 10),
                            round(float(actual["top"]) * 10),
                        )
                        glyph_index.setdefault(key, []).append((index, actual))
                    glyph_indexes[row["page"]] = glyph_index
                indices = []
                for wanted in row["glyphs"]:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("original Note native matching deadline exhausted")
                    if not str(wanted["text"]).strip():
                        continue
                    xkey, ykey = round(float(wanted["x0"]) * 10), round(float(wanted["top"]) * 10)
                    nearby = [
                        candidate
                        for dx in (-1, 0, 1)
                        for dy in (-1, 0, 1)
                        for candidate in glyph_indexes[row["page"]].get(
                            (wanted["text"], _font(wanted), xkey + dx, ykey + dy), []
                        )
                    ]
                    candidates = [
                        index
                        for index, actual in nearby
                        if actual["text"] == wanted["text"]
                        and _font(actual) == _font(wanted)
                        and all(
                            abs(float(actual[key]) - float(wanted[key])) <= 0.05
                            for key in ("x0", "x1", "top", "bottom", "size")
                        )
                    ]
                    if len(candidates) != 1 or (row["page"], candidates[0]) in consumed:
                        findings.append(
                            {"code": "pdf.note.native.position", "identity": binding["identity"], "kind": kind}
                        )
                        break
                    consumed.add((row["page"], candidates[0]))
                    indices.append(candidates[0])
                else:
                    observations.append(
                        {
                            "identity": binding["identity"],
                            "kind": kind,
                            "page": row["page"],
                            "native_glyph_indices": indices,
                            "source_counter": counters[binding["marker"]],
                        }
                    )
    return {
        "schema_version": SCHEMA,
        "source_plan_digest": plan.digest,
        "observations": observations,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def replay_pdf_original_note_paint(
    original: dict[str, Any],
    plan: PDFSemanticPlan,
    bindings: dict[str, Any],
    *,
    read_artifact: Callable[[dict[str, Any]], bytes],
    deadline: float,
) -> dict[str, Any]:
    """Recompute retained byte predicates without reading any producer path.

    read_artifact must be the enclosing reader's admitted custody callback.
    Its source/SDK/FLS/hydration/process approval is not minted by this leaf.
    """
    single = {
        "pdf",
        "source_tex",
        "source_marked_tex",
        "source_marked_pdf",
        "source_marked_aux",
        "original_reference_pdf",
    }
    multiple = {"rasters", "source_marked_rasters", "original_reference_rasters"}
    if set(bindings) != single | multiple or original.get("schema_version") != SCHEMA:
        raise ValueError("portable Note source/native binding closure differs")
    if original.get("source_plan_digest") != plan.digest:
        raise ValueError("portable Note source plan differs from rebuilt original inputs")

    def retained(binding: dict[str, Any]) -> bytes:
        if not math.isfinite(deadline) or time.monotonic() >= deadline:
            raise TimeoutError("portable Note replay exhausted its original finite deadline")
        if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
            raise ValueError("portable Note binding fields differ")
        path = PurePosixPath(binding["path"])
        if (
            path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or re.fullmatch(r"[a-f0-9]{64}", binding["sha256"]) is None
        ):
            raise ValueError("portable Note original binding is unconfined/invalid")
        content = read_artifact(binding)
        if len(content) > 64 * 1024 * 1024 or hashlib.sha256(content).hexdigest() != binding["sha256"]:
            raise ValueError("portable Note admitted original artifact bytes differ")
        return content

    payload: dict[str, Any] = {name: retained(bindings[name]) for name in single}
    for name in multiple:
        if not isinstance(bindings[name], (list, tuple)) or not 1 <= len(bindings[name]) <= 500:
            raise ValueError("portable Note raster closure is empty/unbounded")
        payload[name] = tuple(retained(binding) for binding in bindings[name])
    actual = inspect_pdf_original_note_paint(plan=plan, deadline=deadline, **payload)
    if canonical_digest(actual) != canonical_digest(original):
        raise ValueError("portable Note semantic/native predicates differ from original observed claims")
    return actual
