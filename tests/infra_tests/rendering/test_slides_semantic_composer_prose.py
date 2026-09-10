"""Semantic composer prose-splitting and title/separator structure tests (split from test_slides_accessibility.py)."""

from __future__ import annotations

from typing import Any
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    compose_accessible_pandoc_document,
)
from infrastructure.rendering._slides_accessibility_contracts import proportional_text_width_units
from ._slides_accessibility_helpers import (
    _header,
    _paragraph,
    _hard_line_paragraph,
    _document,
    _visible_text,
    _classed_headers,
)


def test_semantic_composer_splits_only_between_prose_blocks() -> None:
    first = _paragraph(" ".join(f"alpha{index}" for index in range(35)))
    second = _paragraph(" ".join(f"beta{index}" for index in range(35)))

    composition = compose_accessible_pandoc_document(
        _document([_header("Bounded evidence"), first, second]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    headers = _classed_headers(composition.document)
    assert composition.frame_count == 2
    assert [classes for _title, classes in headers] == [{"prose-slide"}, {"prose-slide"}]
    assert "part 2" in headers[1][0]
    assert composition.document["blocks"][1] == first
    assert composition.document["blocks"][3] == second


def test_continuation_title_keeps_headroom_below_real_beamer_wrap_boundary() -> None:
    authored_title = "Publication-facing interpretation"
    first = _paragraph(" ".join(f"alpha{index}" for index in range(35)))
    second = _paragraph(" ".join(f"beta{index}" for index in range(35)))

    composition = compose_accessible_pandoc_document(
        _document([_header(authored_title), first, second]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/formalism.md",
    )

    headers = [block for block in composition.document["blocks"] if block["t"] == "Header"]
    continuation = headers[1]
    visible_title = " ".join(_visible_text(continuation["c"][2]).split())
    assert proportional_text_width_units(visible_title) <= 35
    assert visible_title != f"{authored_title} (part 2)"
    assert ["aria-label", f"{authored_title}, part 2"] in continuation["c"][1][2]


def test_wrapping_first_title_uses_divider_before_six_line_body() -> None:
    authored_title = "Contamination sweep: regime-dependent server behavior under declared attacks"

    composition = compose_accessible_pandoc_document(
        _document([_header(authored_title), _hard_line_paragraph(6)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    headers = _classed_headers(composition.document)
    assert composition.section_divider_count == 1
    assert "section-divider" in headers[0][1]
    assert "part 2" in headers[1][0]


def test_semantic_composer_splits_long_paragraph_only_at_written_clause_boundary() -> None:
    first_sentence = " ".join(f"alpha{index}" for index in range(35)) + "."
    second_sentence = " ".join(f"beta{index}" for index in range(35)) + "."

    composition = compose_accessible_pandoc_document(
        _document([_header("Projection geometry"), _paragraph(first_sentence + " " + second_sentence)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    prose = [block for block in composition.document["blocks"] if block["t"] == "Para"]
    assert composition.frame_count == 2
    assert len(prose) == 2
    assert " ".join(_visible_text(prose[0]).split()).endswith("alpha34.")
    assert " ".join(_visible_text(prose[1]).split()).endswith("beta34.")


def test_semantic_composer_uses_comma_only_before_clause_coordinator() -> None:
    prefix = " ".join(f"alpha{index}" for index in range(32)) + ","
    suffix = "while " + " ".join(f"beta{index}" for index in range(28)) + "."

    composition = compose_accessible_pandoc_document(
        _document([_header("Projection geometry"), _paragraph(prefix + " " + suffix)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    prose = [block for block in composition.document["blocks"] if block["t"] == "Para"]
    assert composition.frame_count == 2
    assert " ".join(_visible_text(prose[0]).split()).endswith("alpha31,")
    assert " ".join(_visible_text(prose[1]).split()).startswith("while beta0")


def test_semantic_composer_rejects_geometry_overflow_without_written_boundary() -> None:
    dense = _paragraph(" ".join(f"longword{index}" for index in range(45)))

    with pytest.raises(RenderingError, match=r"one prose sentence or strong clause cannot fit") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Projection geometry"), dense]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["maximum_lines"] == 7


def test_semantic_composer_counts_authored_hard_lines_at_the_physical_boundary() -> None:
    composition = compose_accessible_pandoc_document(
        _document([_header("Hard lines"), _hard_line_paragraph(7)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/hard-lines.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Hard lines"), _hard_line_paragraph(8)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/hard-lines.md",
        )

    assert exc_info.value.context["estimated_lines"] == 8
    assert exc_info.value.context["maximum_lines"] == 7


def test_semantic_composer_rejects_accidental_title_only_but_accepts_section_divider() -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.structure\.title-only\]"):
        compose_accessible_pandoc_document(
            _document([_header("Orphan heading")]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/empty.md",
        )

    composition = compose_accessible_pandoc_document(
        _document([_header("Methods", level=1)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/methods.md",
    )
    assert composition.frame_count == 1
    assert composition.section_divider_count == 1


def test_semantic_composer_validates_title_only_divider_geometry() -> None:
    title = "W" * 23

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-title-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header(title, level=1)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/divider.md",
        )

    assert exc_info.value.context["first_offending_token"] == title


@pytest.mark.parametrize(
    "separator",
    [
        {"t": "HorizontalRule"},
        {"t": "RawBlock", "c": ["tex", r"\pagebreak"]},
    ],
)
def test_semantic_composer_does_not_lose_separator_only_headings(separator: dict[str, Any]) -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.structure\.title-only\]"):
        compose_accessible_pandoc_document(
            _document([_header("Orphan heading"), separator]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/orphan.md",
        )

    composition = compose_accessible_pandoc_document(
        _document([_header("Methods", level=1), separator]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/methods.md",
    )
    assert composition.frame_count == 1
    assert composition.section_divider_count == 1
