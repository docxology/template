"""Exact Source Code/Link roles in existing complete PDF native observations."""

from __future__ import annotations

import math
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_pdf_semantic_plan import PDFSemanticPlan


def _box(row: dict[str, Any]) -> list[float]:
    box = row["box_pt"]
    if (
        type(box) is not list
        or len(box) != 4
        or any(type(value) not in (int, float) or not math.isfinite(value) for value in box)
        or box[0] >= box[2]
        or box[1] >= box[3]
    ):
        raise ValueError("PDF literal role has no finite positive actual native box")
    return box


def _index(component: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[int, dict[str, Any]]]:
    matches = {row["block_id"]: row for row in component["matches"]}
    words = {row["word_index"]: row for row in component["supported_words"]}
    if len(matches) != len(component["matches"]) or len(words) != len(component["supported_words"]):
        raise ValueError("PDF literal role complete native census repeated an identity")
    return matches, words


def _words(
    indexed: tuple[dict[str, dict[str, Any]], dict[int, dict[str, Any]]],
    member: dict[str, Any],
    span: dict[str, Any],
) -> list[dict[str, Any]]:
    matches, words = indexed
    match = matches.get(member["block_id"])
    if match is None:
        return []
    token_words = match["token_word_indices"]
    first, last = span["token_span"]
    if (
        type(first) is not int
        or type(last) is not int
        or not 0 <= first < last <= len(token_words)
        or len(token_words) != match["token_span"][1] - match["token_span"][0]
    ):
        raise ValueError("PDF literal role escaped its exact complete Source token partition")
    indices = sorted(set(token_words[first:last]))
    if any(index not in words for index in indices):
        return []
    return [words[index] for index in indices]


def _same_position(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left["page"] == right["page"] and all(
        abs(a - b) <= 0.05 for a, b in zip(_box(left), _box(right), strict=True)
    )


def _annotations(
    words: list[dict[str, Any]], links: list[dict[str, Any]], uri: str, *, deadline: float
) -> list[dict[str, Any]]:
    selected = []
    for word in words:
        remaining(deadline)
        box = _box(word)
        candidates = []
        for link in links:
            remaining(deadline)
            if link["page"] != word["page"]:
                continue
            annotation = _box(link)
            if (
                annotation[0] <= box[0] + 1
                and annotation[1] <= box[1] + 1
                and annotation[2] >= box[2] - 1
                and annotation[3] >= box[3] - 1
            ):
                candidates.append(link)
        # Source identity + exact actual containing annotation chooses the
        # endpoint. A nearby annotation or repeated ambiguous box cannot.
        if len(candidates) != 1 or candidates[0]["uri"] != uri:
            return []
        if candidates[0] not in selected:
            selected.append(candidates[0])
    return selected


def inspect_pdf_literal_roles(
    plan: PDFSemanticPlan,
    literal: dict[str, Any],
    reference_literal: dict[str, Any] | None,
    whole_page_parity: dict[str, Any] | None,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Use exact complete Source partitions and existing whole-page witnesses.

    Whole source/reference custody, original/current controls and independent
    scientific roles remain the enclosing caller's obligations. No status bit
    replaces complete words, annotation identities or actual native parity.
    """
    remaining(deadline)
    observations, findings, blockers = [], [], []
    spans_by_identity: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for member in plan.literal_members:
        remaining(deadline)
        if member["context"] != "footnote":
            for span in member["occurrence_token_spans"]:
                spans_by_identity.setdefault(span["identity"], []).append((member, span))
    native_index = _index(literal)
    source_index = _index(reference_literal) if reference_literal is not None else None
    qualified = bool(
        reference_literal is not None
        and whole_page_parity is not None
        and not literal["findings"]
        and not literal["blockers"]
        and not reference_literal["findings"]
        and not reference_literal["blockers"]
        and not whole_page_parity["findings"]
        and whole_page_parity["pages"]
        and all(
            page["glyphs_match"] and page["vectors_match"] and page["pixels_match"]
            for page in whole_page_parity["pages"]
        )
    )
    for occurrence in plan.occurrences:
        remaining(deadline)
        kind, identity = occurrence["kind"], occurrence["identity"]
        if kind not in {"Code", "CodeBlock", "Link"}:
            continue
        spans = [(member, span) for member, span in spans_by_identity.get(identity, []) if span["kind"] == kind]
        if len(spans) != 1:
            blockers.append(f"{identity}: Source {kind} lacks one exact separable literal token interval")
            continue
        member, span = spans[0]
        actual = _words(native_index, member, span)
        expected = _words(source_index, member, span) if source_index is not None else []
        if not actual or not expected or reference_literal is None:
            blockers.append(f"{identity}: Source {kind} lacks complete actual/reference native words")
            continue
        same = len(actual) == len(expected) and all(
            _same_position(left, right)
            and left["fonts"] == right["fonts"]
            and left["min_font_pt"] == right["min_font_pt"]
            and "roi_px" in left
            and "roi_px" in right
            for left, right in zip(actual, expected, strict=True)
        )
        if not same:
            findings.append({"code": "pdf.literal.role.position", "identity": identity})
        annotations, source_annotations = [], []
        if kind == "Link":
            uri = occurrence["content"][2][0]
            if not isinstance(uri, str) or not uri or uri.startswith("#"):
                blockers.append(f"{identity}: Source Link destination requires an explicit native destination witness")
                continue
            annotations = _annotations(actual, literal["links"], uri, deadline=deadline)
            source_annotations = _annotations(expected, reference_literal["links"], uri, deadline=deadline)
            if (
                not annotations
                or len(annotations) != len(source_annotations)
                or any(
                    left["uri"] != right["uri"] or not _same_position(left, right)
                    for left, right in zip(annotations, source_annotations, strict=True)
                )
            ):
                findings.append({"code": "pdf.link.target", "identity": identity})
                continue
        if not qualified:
            blockers.append(
                f"{identity}: Source {kind} requires complete original native glyph/font/vector/pixel parity"
            )
        if qualified and same:
            observations.append(
                {
                    "identity": identity,
                    "kind": kind,
                    "block_id": member["block_id"],
                    "source_token_span": span["token_span"],
                    "words": actual,
                    "source_words": expected,
                    "annotations": annotations,
                    "source_annotations": source_annotations,
                }
            )
    remaining(deadline)
    return {"observations": observations, "findings": findings, "blockers": blockers}
