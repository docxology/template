"""Zero-glyph source math positions from the actual XeTeX shipout engine."""

from __future__ import annotations

import re
from typing import Any
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams

from infrastructure.reporting.native_format_scientific_math import ScientificMath

_POSITION_PREAMBLE = r"""
\makeatletter
\newcommand\NativeSourceMathPosition[4]{}
\DeclareRobustCommand\NativeSourceMathMark[1]{\pdfsavepos\write\@auxout{\string\NativeSourceMathPosition{#1}{\the\pdflastxpos}{\the\pdflastypos}{\the\c@page}}}
\DeclareRobustCommand\NativeSourceMathBegin[2]{\NativeSourceMathMark{#1-start}\special{pdf:code /Span <</MCID #2>> BDC}}
\DeclareRobustCommand\NativeSourceMathEnd[1]{\special{pdf:code EMC}\NativeSourceMathMark{#1-end}}
\makeatother
"""


def instrument_source_math_positions(
    tex: str, nodes: tuple[ScientificMath, ...]
) -> tuple[str, tuple[dict[str, Any], ...], tuple[str, ...]]:
    """Bind original Math nodes to exact source-owned writer fragments.

    No glyph is added. Unresolved writer transformations remain blockers;
    raw TeX mathematics requires its own complete source-node ledger.
    """
    if len(tex.encode()) > 4 * 1024 * 1024 or len(nodes) > 10_000:
        raise ValueError("source mathematical position inputs exceed their finite budgets")
    if tex.count(r"\begin{document}") != 1 or "NativeSourceMath" in tex:
        raise ValueError("source reference has an ambiguous reserved position boundary")
    bindings = []
    blockers = []
    replacements = []
    cursor = tex.index(r"\begin{document}")
    for ordinal, node in enumerate(nodes):
        candidates = []
        wrapper = (r"\(" + node.source + r"\)") if node.mode == "InlineMath" else (r"\[" + node.source + r"\]")
        for match in re.finditer(re.escape(wrapper), tex):
            if match.start() >= cursor:
                candidates.append((match.start() + 2, match.end() - 2))
        if node.mode == "DisplayMath":
            for match in re.finditer(r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}", tex, re.DOTALL):
                content = match.group(1)
                if match.start() >= cursor and content.count(node.source) == 1:
                    start = match.start(1) + content.index(node.source)
                    candidates.append((start, start + len(node.source)))
        candidates = sorted(set(candidates))
        if not candidates:
            blockers.append(f"{node.identity}: exact independently projected mathematical fragment is unresolved")
            continue
        start, end = candidates[0]
        marker = f"M{ordinal:06d}"
        bindings.append(
            {
                "identity": node.identity,
                "marker": marker,
                "mcid": ordinal,
                "source_start": start,
                "source_end": end,
                "source": node.source,
                "mode": node.mode,
                "context": node.context,
            }
        )
        replacements.extend(
            [
                (start, r"\NativeSourceMathBegin{" + marker + "}{" + str(ordinal) + "}"),
                (end, r"\NativeSourceMathEnd{" + marker + "}"),
            ]
        )
        cursor = end
    for offset, insertion in sorted(replacements, reverse=True):
        tex = tex[:offset] + insertion + tex[offset:]
    tex = tex.replace(r"\begin{document}", _POSITION_PREAMBLE + "\n" + r"\begin{document}", 1)
    return tex, tuple(bindings), tuple(blockers)


def source_math_positions_from_aux(aux: bytes, bindings: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """Read real shipout positions; repeated table headers remain repeated rows."""
    if len(aux) > 8 * 1024 * 1024:
        raise ValueError("source position recorder exceeds its finite byte budget")
    matches = re.findall(
        rb"\\NativeSourceMathPosition\{(M[0-9]{6}-(?:start|end))\}\{(-?[0-9]+)\}\{(-?[0-9]+)\}\{([0-9]+)\}", aux
    )
    admitted = {row["marker"]: row for row in bindings}
    pending: dict[str, tuple[int, int, int]] = {}
    rows = []
    for raw_marker, raw_x, raw_y, raw_page in matches:
        marker, side = raw_marker.decode().rsplit("-", 1)
        if marker not in admitted:
            raise ValueError("native source recorder contains an undeclared mathematical occurrence")
        position = int(raw_x), int(raw_y), int(raw_page)
        if position[2] < 1 or position[2] > 500:
            raise ValueError("native source position exceeds its page budget")
        if side == "start":
            if marker in pending:
                raise ValueError("native source mathematical starts overlap")
            pending[marker] = position
        else:
            start = pending.pop(marker, None)
            if start is None:
                raise ValueError("native source mathematical end has no original start")
            rows.append(
                {
                    "identity": admitted[marker]["identity"],
                    "marker": marker,
                    "mcid": admitted[marker]["mcid"],
                    "start_sp": list(start),
                    "end_sp": list(position),
                }
            )
    if pending or {row["marker"] for row in rows} != set(admitted):
        raise ValueError("actual native shipout lost a source mathematical occurrence")
    if len(rows) > 100_000:
        raise ValueError("native source mathematical repetition budget exceeded")
    return tuple(rows)


def source_math_paint_from_pdf(
    pdf_bytes: bytes, bindings: tuple[dict[str, Any], ...], *, deadline: float
) -> tuple[dict[str, Any], ...]:
    """Read actual glyphs and vector paint tagged by zero-glyph source markers."""
    from io import BytesIO
    import time
    import pdfplumber

    if len(pdf_bytes) > 64 * 1024 * 1024 or len(bindings) > 10_000:
        raise ValueError("mathematical source paint inputs exceed their finite budgets")
    preflight_pdf_streams(pdf_bytes, deadline=deadline, max_objects=4_000_000)
    admitted = {row["mcid"]: row for row in bindings}
    if len(admitted) != len(bindings):
        raise ValueError("source mathematical paint identities are duplicated")
    rows = []
    observed = set()
    total = 0
    with pdfplumber.open(BytesIO(pdf_bytes)) as document:
        if not document.pages or len(document.pages) > 500:
            raise ValueError("source mathematical paint exceeds its native page budget")
        for number, page in enumerate(document.pages, 1):
            if time.monotonic() >= deadline:
                raise TimeoutError("source mathematical paint exhausted its original deadline")
            grouped: dict[int, dict[str, list[Any]]] = {}
            for kind, objects in (("glyphs", page.chars), ("vectors", (*page.lines, *page.rects, *page.curves))):
                total += len(objects)
                if total > 4_000_000:
                    raise ValueError("source mathematical paint exceeds its native object budget")
                for item in objects:
                    identity = item.get("mcid")
                    if identity is None:
                        continue
                    if type(identity) is not int or identity not in admitted or item.get("tag") != "Span":
                        raise ValueError("source reference contains undeclared or ambiguous mathematical paint tags")
                    row = grouped.setdefault(identity, {"glyphs": [], "vectors": []})
                    keys = (
                        (
                            "text",
                            "fontname",
                            "size",
                            "x0",
                            "x1",
                            "top",
                            "bottom",
                            "non_stroking_color",
                            "stroking_color",
                        )
                        if kind == "glyphs"
                        else (
                            "object_type",
                            "x0",
                            "x1",
                            "top",
                            "bottom",
                            "linewidth",
                            "fill",
                            "stroke",
                            "path",
                            "non_stroking_color",
                            "stroking_color",
                        )
                    )
                    row[kind].append({key: item.get(key) for key in keys})
            for identity, paint in sorted(grouped.items()):
                observed.add(identity)
                rows.append(
                    {
                        "identity": admitted[identity]["identity"],
                        "mcid": identity,
                        "page": number,
                        "width_pt": page.width,
                        "height_pt": page.height,
                        **paint,
                    }
                )
    if observed != set(admitted):
        raise ValueError("native source reference lost an original mathematical paint occurrence")
    return tuple(rows)
