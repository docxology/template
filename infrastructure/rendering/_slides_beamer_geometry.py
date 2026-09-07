"""Rendered safe-area validation for the accessible Beamer derivative."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import (
    ACCESSIBLE_BEAMER_MIN_BOTTOM_CLEARANCE_PT,
    ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT,
)
from infrastructure.rendering.latex_log_quality import parse_latex_log_findings


_GEOMETRY_TOLERANCE_PT = 0.25
_HORIZONTAL_RULE_TOLERANCE_PT = 0.75
_MINIMUM_RULE_LENGTH_PT = 2.0


def reject_accessible_beamer_overflow(log_file: Path, compiled_pdf: Path) -> None:
    """Discard a Beamer derivative whose fixed accessible layout overflowed."""

    blocked = {r"Overfull \hbox", r"Overfull \vbox"}
    findings = [
        finding
        for finding in parse_latex_log_findings(log_file, blocked_layout_kinds=blocked)
        if finding.kind in blocked
    ]
    if not findings:
        return
    compiled_pdf.unlink(missing_ok=True)
    examples = [f"{finding.kind} at line {finding.line_number}: {finding.message}" for finding in findings[:5]]
    raise RenderingError(
        "[slides.density.beamer-overflow] Accessible Beamer content exceeds its fixed frame geometry",
        context={
            "diagnostic_code": "slides.density.beamer-overflow",
            "log_file": str(log_file),
            "finding_count": len(findings),
            "examples": examples,
        },
        suggestions=[
            "Split the source at a semantic block boundary or shorten the projected excerpt.",
            "Keep complete prose, captions, and tables in the linked canonical HTML manuscript.",
        ],
    )


def _numeric(item: dict[str, Any], key: str) -> float:
    value = item.get(key)
    if value is None or isinstance(value, bool):
        raise ValueError(f"invalid coordinate {key}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite coordinate {key}")
    return number


def _accessible_beamer_geometry_issues(compiled_pdf: Path) -> tuple[dict[str, object], ...]:
    """Return bounded glyph/rule safe-area violations from a compiled deck."""

    try:
        import pdfplumber
    except ImportError as exc:
        raise RenderingError(
            "[slides.capability.pdf-geometry-required] Accessible Beamer validation requires pdfplumber",
            context={
                "diagnostic_code": "slides.capability.pdf-geometry-required",
                "required_extra": "rendering",
            },
            suggestions=[
                "Install the rendering extra before producing accessible Beamer slides.",
                "Use the archive profile only when the accessible publication contract is not required.",
            ],
        ) from exc

    issues: list[dict[str, object]] = []
    try:
        with pdfplumber.open(compiled_pdf) as document:
            for page_number, page in enumerate(document.pages, start=1):
                page_width = float(page.width)
                page_height = float(page.height)
                if (
                    not math.isfinite(page_width)
                    or not math.isfinite(page_height)
                    or page_width <= 2 * ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT
                    or page_height <= ACCESSIBLE_BEAMER_MIN_BOTTOM_CLEARANCE_PT
                ):
                    issues.append(
                        {
                            "kind": "page-box",
                            "page": page_number,
                            "page_width_pt": page_width,
                            "page_height_pt": page_height,
                        }
                    )
                    continue

                for word in page.extract_words() or ():
                    text = str(word.get("text", "")).strip()
                    if not text:
                        continue
                    x0 = _numeric(word, "x0")
                    x1 = _numeric(word, "x1")
                    bottom = _numeric(word, "bottom")
                    if (
                        x0 < ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT - _GEOMETRY_TOLERANCE_PT
                        or x1 > page_width - ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT + _GEOMETRY_TOLERANCE_PT
                    ):
                        issues.append(
                            {
                                "kind": "glyph-side-clearance",
                                "page": page_number,
                                "text": text[:80],
                                "x0_pt": x0,
                                "x1_pt": x1,
                                "page_width_pt": page_width,
                            }
                        )
                    if bottom > page_height - ACCESSIBLE_BEAMER_MIN_BOTTOM_CLEARANCE_PT + _GEOMETRY_TOLERANCE_PT:
                        issues.append(
                            {
                                "kind": "glyph-bottom-clearance",
                                "page": page_number,
                                "text": text[:80],
                                "bottom_pt": bottom,
                                "page_height_pt": page_height,
                            }
                        )

                for line in page.lines or ():
                    x0 = _numeric(line, "x0")
                    x1 = _numeric(line, "x1")
                    top = _numeric(line, "top")
                    bottom = _numeric(line, "bottom")
                    if abs(bottom - top) > _HORIZONTAL_RULE_TOLERANCE_PT or x1 - x0 < _MINIMUM_RULE_LENGTH_PT:
                        continue
                    if (
                        x0 < ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT - _GEOMETRY_TOLERANCE_PT
                        or x1 > page_width - ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT + _GEOMETRY_TOLERANCE_PT
                    ):
                        issues.append(
                            {
                                "kind": "rule-side-clearance",
                                "page": page_number,
                                "x0_pt": x0,
                                "x1_pt": x1,
                                "y_pt": (top + bottom) / 2,
                                "page_width_pt": page_width,
                            }
                        )
    except RenderingError:
        raise
    except Exception as exc:  # noqa: BLE001 - backend exceptions vary by PDF structure
        raise RenderingError(
            "[slides.geometry.beamer-unreadable] Accessible Beamer geometry could not be inspected",
            context={
                "diagnostic_code": "slides.geometry.beamer-unreadable",
                "output": str(compiled_pdf),
                "error": str(exc),
            },
            suggestions=[
                "Inspect the compiled PDF and ensure the rendering extra is current.",
                "Regenerate the derivative from the source-owned accessible profile.",
            ],
        ) from exc
    return tuple(issues)


def reject_unsafe_accessible_beamer_geometry(compiled_pdf: Path) -> None:
    """Delete and reject a deck with clipped footer or edge-touching content."""

    try:
        issues = _accessible_beamer_geometry_issues(compiled_pdf)
    except RenderingError:
        compiled_pdf.unlink(missing_ok=True)
        raise
    if not issues:
        return
    compiled_pdf.unlink(missing_ok=True)
    raise RenderingError(
        "[slides.geometry.beamer-safe-area] Accessible Beamer content enters a protected page-edge clearance",
        context={
            "diagnostic_code": "slides.geometry.beamer-safe-area",
            "output": str(compiled_pdf),
            "minimum_side_clearance_pt": ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT,
            "minimum_bottom_clearance_pt": ACCESSIBLE_BEAMER_MIN_BOTTOM_CLEARANCE_PT,
            "finding_count": len(issues),
            "examples": list(issues[:8]),
        },
        suggestions=[
            "Keep tables inside the accessible frame-body width and preserve the declared footer bottom skip.",
            "Split or recompose the source at a semantic boundary rather than shrinking accessible typography.",
        ],
    )


__all__ = ["reject_accessible_beamer_overflow", "reject_unsafe_accessible_beamer_geometry"]
