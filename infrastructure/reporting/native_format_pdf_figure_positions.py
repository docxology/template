"""Bind original caption identities and figure positions to source-only output.

The enclosing reader admits the original reference source/compiler/FLS/SDK
closure. Pixel equality and a receipt's claimed status alone grant no coverage.
"""

from __future__ import annotations

import time
from typing import Any

from infrastructure.reporting.native_format_pdf_semantic_plan import PDFSemanticPlan


def _caption(
    text: dict[str, Any], identities: list[str], mathematical: list[dict[str, Any]] | None = None
) -> dict[str, Any] | None:
    matches = {row["block_id"]: row["word_indices"] for row in text["matches"]}
    words = {row["word_index"]: row for row in text["supported_words"]}
    if (not identities and not mathematical) or any(identity not in matches for identity in identities):
        return None
    selected = [words[index] for identity in identities for index in matches[identity]] + list(mathematical or [])
    pages = {word["page"] for word in selected}
    if not selected or len(pages) != 1:
        return None
    boxes = [word["box_pt"] for word in selected]
    return {
        "text_ids": identities,
        "mathematical_ids": [row["identity"] for row in mathematical or []],
        "page": next(iter(pages)),
        "box_pt": [
            min(box[0] for box in boxes),
            min(box[1] for box in boxes),
            max(box[2] for box in boxes),
            max(box[3] for box in boxes),
        ],
    }


def _position(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    return actual["page"] == expected["page"] and all(
        abs(left - right) <= 0.05 for left, right in zip(actual["box_pt"], expected["box_pt"], strict=True)
    )


def bind_pdf_figure_positions(
    plan: PDFSemanticPlan,
    literal: dict[str, Any],
    figures: dict[str, Any],
    *,
    reference_literal: dict[str, Any] | None,
    reference_figures: dict[str, Any] | None,
    whole_page_parity: dict[str, Any] | None,
    deadline: float,
    equations: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Require each exact source caption and image at source-reference positions.

    A unique decoded source image identifies its original occurrence; repeated
    ambiguous images remain refused by the independent decoded-pixel observer.
    Caption identity comes from the original source plan's visible alias ledger,
    never from proximity or an arbitrary nearest caption in the candidate PDF.
    """
    findings: list[dict[str, Any]] = []
    blockers: list[str] = []
    positions: list[dict[str, Any]] = []
    expected_images = {row["identity"]: row for row in plan.occurrences if row["kind"] == "Image"}
    source_images = {row["identity"]: row for row in (reference_figures or {}).get("figures", [])}
    reference_valid = bool(
        reference_literal is not None
        and reference_figures is not None
        and whole_page_parity is not None
        and not reference_literal["findings"]
        and not reference_literal["blockers"]
        and not reference_figures["findings"]
        and not reference_figures["blockers"]
        and not whole_page_parity["findings"]
        and whole_page_parity["pages"]
        and all(
            page["glyphs_match"] and page["vectors_match"] and page["pixels_match"]
            for page in whole_page_parity["pages"]
        )
    )
    math_positions = {row["identity"]: row for row in (equations or {}).get("observations", [])}
    for image in figures["figures"]:
        if time.monotonic() >= deadline:
            raise TimeoutError("original figure/caption position witness exhausted its finite deadline")
        identity = image["identity"]
        image["covered"] = False
        caption_ids = expected_images[identity].get("rendered_caption_text_ids", [])
        scientific_ids = expected_images[identity].get("rendered_caption_occurrence_ids", [])
        scientific_rows = [math_positions[item] for item in scientific_ids if item in math_positions]
        if any(item not in math_positions for item in scientific_ids):
            blockers.append(
                f"{identity}: exact rich caption descendant lacks its independent native mathematical witness"
            )
            continue
        caption = _caption(literal, caption_ids, scientific_rows)
        if caption is None:
            blockers.append(f"{identity}: original rendered caption identity lacks native placement")
            continue
        expected_image = source_images.get(identity)
        # The actual independent Math interpreter binds original Source paint
        # to these exact glyph boxes. Complete every-page parity independently
        # binds those positions to the uninstrumented Source reference.
        expected_caption = (
            _caption(reference_literal, caption_ids, scientific_rows) if reference_literal is not None else None
        )
        if expected_image is None or expected_caption is None:
            blockers.append(f"{identity}: independently admitted source figure/caption positions are required")
            continue
        if expected_image["page"] != expected_caption["page"]:
            blockers.append(f"{identity}: split source figure/caption requires original structural position markers")
            continue
        if not _position(image, expected_image) or not _position(caption, expected_caption):
            findings.append({"code": "pdf.figure.caption.position", "identity": identity})
        if not reference_valid:
            blockers.append(f"{identity}: every-page original source glyph/vector/pixel parity is required")
        image["covered"] = reference_valid and _position(image, expected_image) and _position(caption, expected_caption)
        positions.append(
            {
                "identity": identity,
                "caption": caption,
                "source_caption": expected_caption,
                "source_image": {"page": expected_image["page"], "box_pt": expected_image["box_pt"]},
                "covered": image["covered"],
            }
        )
    return {"positions": positions, "findings": findings, "blockers": blockers}
