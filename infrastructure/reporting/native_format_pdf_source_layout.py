"""Independent source page-break commands against actual literal glyph anchors."""

from __future__ import annotations

import math
import re
import time
from typing import Any

from infrastructure.reporting.native_format_pdf_semantic_plan import PDFSemanticPlan


def inspect_pdf_source_pagebreaks(plan: PDFSemanticPlan, literal: dict[str, Any], *, deadline: float) -> dict[str, Any]:
    """Interpret exact newpage/clearpage raw nodes and observe surrounding pages.

    No arbitrary TeX layout command is waived. Unanchored, inline-footnote,
    dimensioned or compound raw nodes retain their independent obligations.
    """
    if type(deadline) not in {int, float} or not math.isfinite(deadline):
        raise ValueError("source pagebreak witness requires a finite deadline")
    matches = {row["block_id"]: row["word_indices"] for row in literal["matches"]}
    words = {row["word_index"]: row for row in literal["supported_words"]}
    observations = []
    findings = []
    blockers = []
    for row in plan.occurrences:
        if row["kind"] not in {"RawBlock", "RawInline"}:
            continue
        if time.monotonic() >= deadline:
            raise TimeoutError("source pagebreak witness exhausted its original deadline")
        form, source = row["content"]
        command = re.fullmatch(r"\s*\\(newpage|clearpage)\s*", source)
        if form not in {"latex", "tex"} or command is None:
            continue
        cursor = row["text_cursor"]
        if row["context"] == "footnote" or not 0 < cursor < len(plan.text):
            blockers.append(
                f"{row['identity']}: original source pagebreak lacks independently matched surrounding prose"
            )
            continue
        previous, following = plan.text[cursor - 1].id, plan.text[cursor].id
        if previous not in matches or following not in matches:
            blockers.append(f"{row['identity']}: original source pagebreak anchors are incomplete")
            continue
        previous_pages = {words[index]["page"] for index in matches[previous]}
        following_pages = {words[index]["page"] for index in matches[following]}
        if min(following_pages) <= max(previous_pages):
            findings.append({"code": "pdf.layout.source.pagebreak", "identity": row["identity"]})
        observations.append(
            {
                "identity": row["identity"],
                "command": command[1],
                "preceding_block": previous,
                "following_block": following,
                "preceding_pages": sorted(previous_pages),
                "following_pages": sorted(following_pages),
            }
        )
    return {"observations": observations, "findings": findings, "blockers": blockers}
