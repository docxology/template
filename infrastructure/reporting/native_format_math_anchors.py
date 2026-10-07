"""Exact source prose anchors for independently observed mathematical occurrences."""

from __future__ import annotations

import time
from io import BytesIO
from typing import Any

from infrastructure.reporting.native_format_scientific_math import ScientificMath


def _compact(text: str) -> str:
    return "".join(character for character in text if not character.isspace())


def inspect_math_source_anchors(
    pdf_bytes: bytes,
    nodes: tuple[ScientificMath, ...],
    observations: tuple[dict[str, Any], ...],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Bind native equation intervals to adjacent original source prose.

    Complex source expansions require an independently reconstructed prose
    projection. This finite seam refuses absent anchors rather than inferring
    source placement from an equation's glyph identity alone.
    """
    import pdfplumber

    if len(pdf_bytes) > 64 * 1024 * 1024 or len(nodes) > 10_000:
        raise ValueError("source anchor inputs exceed their finite budgets")
    by_identity = {row["identity"]: row for row in observations}
    if len(by_identity) != len(observations):
        raise ValueError("native mathematical occurrence identities are duplicated")
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    retained: list[dict[str, Any]] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as document:
        if not document.pages or len(document.pages) > 500:
            raise ValueError("source anchor readback exceeds its native page budget")
        pages = [[glyph for glyph in page.chars if glyph["text"].strip()] for page in document.pages]
        if sum(map(len, pages)) > 2_000_000:
            raise ValueError("source anchor readback exceeds its native glyph budget")
        for node in nodes:
            if time.monotonic() >= deadline:
                raise TimeoutError("source mathematical anchor deadline exhausted")
            row = by_identity.get(node.identity)
            if row is None:
                findings.append({"code": "pdf.math.anchor", "identity": node.identity, "reason": "missing occurrence"})
                continue
            left, right = _compact(node.before)[-48:], _compact(node.after)[:48]
            if not left or not right:
                blockers.append(f"{node.identity}: both adjacent source prose anchors are required")
                continue
            page_number, start, count = row["page"], row["glyph_start"], row["glyph_count"]
            if (
                type(page_number) is not int
                or type(start) is not int
                or type(count) is not int
                or page_number < 1
                or page_number > len(pages)
                or start < 0
                or count < 1
                or start + count > len(pages[page_number - 1])
            ):
                raise ValueError("native equation source interval is invalid")
            glyphs = pages[page_number - 1]
            actual_left = _compact("".join(glyph["text"] for glyph in glyphs[:start]))[-len(left) :]
            actual_right = _compact("".join(glyph["text"] for glyph in glyphs[start + count :]))[: len(right)]
            matched = actual_left == left and actual_right == right
            if not matched:
                findings.append(
                    {"code": "pdf.math.anchor", "identity": node.identity, "reason": "source prose differs"}
                )
            retained.append(
                {
                    "identity": node.identity,
                    "expected_before": left,
                    "expected_after": right,
                    "actual_before": actual_left,
                    "actual_after": actual_right,
                    "matched": matched,
                }
            )
    return {
        "schema_version": "template-native-source-math-anchors-v1",
        "observations": retained,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings or blockers else "pass",
    }
