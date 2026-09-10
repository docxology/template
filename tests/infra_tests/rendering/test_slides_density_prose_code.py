"""Semantic composer prose, list, code-token, and citation density pricing (split from test_slides_accessibility.py)."""

from __future__ import annotations

import json
import re
from typing import Any
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    _estimated_visible_characters,
    compose_accessible_pandoc_document,
)
from infrastructure.rendering._slides_accessibility_contracts import proportional_text_width_units
from infrastructure.rendering._slides_accessibility_text_geometry import _plain_text
from ._slides_accessibility_helpers import (
    _inlines,
    _header,
    _paragraph,
    _citation,
    _paragraph_with_citations,
    _document,
)


def test_semantic_composer_prices_list_indent_and_nested_item_lines() -> None:
    passing_width = {"t": "BulletList", "c": [[_paragraph("a" * 40)]]}
    composition = compose_accessible_pandoc_document(
        _document([_header("List width"), passing_width]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/lists.md",
    )
    assert composition.frame_count == 1

    failing_width = {"t": "BulletList", "c": [[_paragraph("a" * 42)]]}
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as width_error:
        compose_accessible_pandoc_document(
            _document([_header("List width"), failing_width]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/lists.md",
        )
    assert width_error.value.context["first_offending_token"] == "a" * 42

    def nested(child_count: int) -> dict[str, Any]:
        children = {"t": "BulletList", "c": [[_paragraph(f"child {index}")] for index in range(child_count)]}
        return {"t": "BulletList", "c": [[_paragraph("parent"), children]]}

    nested_composition = compose_accessible_pandoc_document(
        _document([_header("Nested list"), nested(6)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/lists.md",
    )
    assert nested_composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-list\]") as height_error:
        compose_accessible_pandoc_document(
            _document([_header("Nested list"), nested(7)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/lists.md",
        )
    assert height_error.value.context["estimated_lines"] == 8


def test_semantic_composer_models_definition_list_entry_geometry() -> None:
    def definition_list(entry_count: int) -> dict[str, Any]:
        return {
            "t": "DefinitionList",
            "c": [[_inlines(f"term{index}"), [[_paragraph("x")]]] for index in range(entry_count)],
        }

    composition = compose_accessible_pandoc_document(
        _document([_header("Definitions"), definition_list(7)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/definitions.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-definition-list\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Definitions"), definition_list(8)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/definitions.md",
        )
    assert exc_info.value.context["estimated_lines"] == 8


def test_semantic_composer_recursively_prices_one_definition_with_many_paragraphs() -> None:
    def definition_list(paragraph_count: int) -> dict[str, Any]:
        return {
            "t": "DefinitionList",
            "c": [[_inlines("term"), [[_paragraph("x") for _ in range(paragraph_count)]]]],
        }

    composition = compose_accessible_pandoc_document(
        _document([_header("One definition"), definition_list(7)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/definitions.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-definition-list\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("One definition"), definition_list(8)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/definitions.md",
        )
    assert exc_info.value.context["estimated_lines"] == 8


def test_semantic_composer_prices_loose_list_paragraph_boundaries() -> None:
    def loose_list(paragraph_count: int) -> dict[str, Any]:
        return {"t": "BulletList", "c": [[_paragraph("x") for _ in range(paragraph_count)]]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Loose list"), loose_list(7)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/lists.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-list\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Loose list"), loose_list(8)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/lists.md",
        )
    assert exc_info.value.context["estimated_lines"] == 8


def test_semantic_composer_recursively_prices_evidence_block_paragraphs() -> None:
    def evidence(paragraph_count: int) -> dict[str, Any]:
        return {"t": "BlockQuote", "c": [_paragraph("x") for _ in range(paragraph_count)]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Evidence"), evidence(8)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/evidence.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-evidence\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Evidence"), evidence(9)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/evidence.md",
        )
    assert exc_info.value.context["estimated_lines"] == 8


def test_semantic_composer_preserves_evidence_div_block_geometry() -> None:
    evidence = {
        "t": "Div",
        "c": [["", ["evidence"], []], [_paragraph("x") for _ in range(10)]],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-evidence\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Evidence container"), evidence]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/evidence-div.md",
        )

    assert exc_info.value.context["estimated_lines"] == 19
    assert exc_info.value.context["maximum_lines"] == 7


def test_semantic_composer_fails_on_an_indivisible_dense_block() -> None:
    dense = _paragraph(" ".join(f"word{index}" for index in range(81)))

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Too dense"), dense]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["diagnostic_code"] == "slides.density.indivisible-prose"
    assert exc_info.value.context["maximum_words"] == 80


@pytest.mark.parametrize(
    ("block", "code"),
    [
        (
            {"t": "BulletList", "c": [[_paragraph(" ".join(f"item{index}" for index in range(50)))]]},
            "slides.density.indivisible-list",
        ),
        (
            {
                "t": "RawBlock",
                "c": [
                    "tex",
                    "\\begin{definition}" + " ".join(f"condition{index}" for index in range(90)) + "\\end{definition}",
                ],
            },
            "slides.density.indivisible-raw-block",
        ),
    ],
)
def test_semantic_composer_rejects_oversized_atomic_structures(
    block: dict[str, Any],
    code: str,
) -> None:
    with pytest.raises(RenderingError, match=rf"\[{re.escape(code)}\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Atomic source structure"), block]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["diagnostic_code"] == code
    assert exc_info.value.context["estimated_lines"] > exc_info.value.context["maximum_lines"]


def test_semantic_composer_debits_inline_code_at_the_monospace_width() -> None:
    inlines: list[dict[str, Any]] = []
    for index in range(12):
        if index:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Code", "c": [["", [], []], f"canonical_parameter_name_{index}"]})
    block = {"t": "Para", "c": inlines}

    with pytest.raises(RenderingError, match=r"slides\.density\.indivisible-prose"):
        compose_accessible_pandoc_document(
            _document([_header("Monospace geometry"), block]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_semantic_composer_debits_cross_reference_fallback_at_visible_label_width() -> None:
    bibliography = {"t": "Para", "c": [_citation("mildner2025fedgvi")]}
    section_reference = {"t": "Para", "c": [_citation("sec:results-hierarchical")]}

    assert _estimated_visible_characters(bibliography) == 32
    assert _estimated_visible_characters(section_reference) > _estimated_visible_characters(bibliography)


def test_semantic_composer_prices_citation_prefix_and_suffix_before_citeproc() -> None:
    citation = {
        "t": "Para",
        "c": [
            _citation(
                "bissiri2016",
                prefix="compare the detailed construction in",
                suffix="especially chapter twelve and appendix alpha",
            )
        ],
    }

    assert _estimated_visible_characters(citation) == proportional_text_width_units(
        "compare the detailed construction in " + "a" * 32 + " especially chapter twelve and appendix alpha"
    )


def test_semantic_composer_uses_resolved_citeproc_text_and_rejects_one_overwide_family_name() -> None:
    long_family = "W" * 24
    citation = _citation(
        "longfamily2026",
        rendered_text=f"({long_family} 2026)",
    )
    paragraph = {"t": "Para", "c": [*_inlines("The source is"), {"t": "Space"}, citation]}

    assert _estimated_visible_characters(paragraph) == proportional_text_width_units(
        f"The source is ({long_family} 2026)"
    )
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Resolved citation geometry"), paragraph]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/discussion.md",
        )

    assert long_family in exc_info.value.context["first_offending_token"]
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]


def test_resolved_mixed_citation_prices_one_cross_reference_rendition() -> None:
    cite = {
        "t": "Cite",
        "c": [
            [
                {
                    "citationId": "smith2026",
                    "citationPrefix": [{"t": "Str", "c": "see"}],
                    "citationSuffix": [],
                    "citationMode": {"t": "NormalCitation"},
                    "citationNoteNum": 1,
                    "citationHash": 0,
                },
                {
                    "citationId": "eq:model",
                    "citationPrefix": [],
                    "citationSuffix": [],
                    "citationMode": {"t": "NormalCitation"},
                    "citationNoteNum": 1,
                    "citationHash": 0,
                },
            ],
            [
                {"t": "Str", "c": "(see"},
                {"t": "Space"},
                {"t": "Str", "c": "Smith"},
                {"t": "Space"},
                {"t": "Str", "c": "2026;"},
                {"t": "Space"},
                {"t": "Strong", "c": [{"t": "Str", "c": "eq:model?"}]},
                {"t": "Str", "c": ")"},
            ],
        ],
    }

    normalized = " ".join(_plain_text(cite).split())

    assert normalized == "(see Smith 2026; eq. eq:model )"
    assert normalized.count("eq:model") == 1
    assert _estimated_visible_characters({"t": "Para", "c": [cite]}) < proportional_text_width_units(
        normalized + " eq. eq:model"
    )


@pytest.mark.parametrize(("glyph", "count"), [("W", 23), ("A", 32), ("m", 28)])
def test_semantic_composer_rejects_overwide_ordinary_prose_tokens(glyph: str, count: int) -> None:
    token = glyph * count

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Physical token"), _paragraph(token)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/discussion.md",
        )

    assert exc_info.value.context["first_offending_token"] == token
    assert exc_info.value.context["required_width_units"] > 43


def test_semantic_composer_prices_aggregate_proportional_prose_width() -> None:
    passing = _paragraph(" ".join(["WW"] * 63))
    failing = _paragraph(" ".join(["WW"] * 64))

    composition = compose_accessible_pandoc_document(
        _document([_header("Wide prose pass"), passing]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/discussion.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Wide prose fail"), failing]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/discussion.md",
        )

    assert exc_info.value.context["estimated_lines"] == 8
    assert exc_info.value.context["maximum_lines"] == 7


@pytest.mark.parametrize("literal", ["'", "[", "{"])
def test_semantic_composer_rejects_every_overwide_indivisible_code_token(literal: str) -> None:
    code = "a" * 80 + literal
    paragraph = {"t": "Para", "c": [{"t": "Code", "c": [["", [], []], code]}]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Code token"), paragraph]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/discussion.md",
        )

    assert exc_info.value.context["first_offending_token"] == code
    assert exc_info.value.context["required_width_units"] > 43


@pytest.mark.parametrize(("surface", "length", "capacity"), [("body", 34, 43), ("title", 27, 35)])
def test_code_token_guard_owns_the_exact_safety_debit_boundary(
    surface: str,
    length: int,
    capacity: int,
) -> None:
    code = "a" * length
    code_node = {"t": "Code", "c": [["", [], []], code]}
    header = {
        "t": "Header",
        "c": [2, ["code-boundary", [], []], [code_node] if surface == "title" else _inlines("Code boundary")],
    }
    blocks = [header]
    if surface == "body":
        blocks.append({"t": "Para", "c": [code_node]})

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(blocks),
            policy=AccessibleSlidePolicy(),
            source="manuscript/discussion.md",
        )

    assert exc_info.value.context["first_offending_token"] == code
    assert exc_info.value.context["available_width_units"] == capacity
    assert exc_info.value.context["required_width_units"] == capacity + 1


def test_semantic_composer_splits_before_unresolved_crossrefs_overflow_beamer() -> None:
    paragraph = _paragraph_with_citations(
        "Five structural extension studies (Studies 5–9, Supplementary sections) build on the same POMDP "
        "substrate and are described there: the moving disjoint-FOV sentinel ( REF0 ), the 2-level hierarchical "
        "POMDP ( REF1 ), the N-level extension ( REF2 ), the 2-D sensitivity sweep ( REF3 ), and parameter "
        "recovery ( REF4 ).",
        [
            "sec:results-moving",
            "sec:results-hierarchical",
            "sec:results-3level",
            "sec:results-sensitivity",
            "sec:results-parameter-recovery",
        ],
    )

    composition = compose_accessible_pandoc_document(
        _document([_header("Server robustness setting"), paragraph]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/12_methods_experimental_design.md",
    )

    prose = [block for block in composition.document["blocks"] if block["t"] == "Para"]
    assert composition.frame_count == 2
    assert len(prose) == 2
    assert "sec:results-hierarchical" in json.dumps(prose[0])
    assert "sec:results-3level" not in json.dumps(prose[0])
    assert "sec:results-3level" in json.dumps(prose[1])
    assert "sec:results-sensitivity" in json.dumps(prose[1])
    assert "sec:results-parameter-recovery" in json.dumps(prose[1])


def test_semantic_composer_prices_citeproc_author_year_expansion_before_split() -> None:
    paragraph = _paragraph_with_citations(
        "The first bounded synthesis relates REF0 REF1 REF2 and REF3 while preserving each source claim. "
        "The second bounded synthesis relates REF4 REF5 REF6 and REF7 while preserving each evidence class.",
        [f"long-surname-source-{index}" for index in range(8)],
    )

    composition = compose_accessible_pandoc_document(
        _document([_header("Citation-rich synthesis"), paragraph]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/discussion.md",
    )

    prose = [block for block in composition.document["blocks"] if block["t"] == "Para"]
    assert composition.frame_count == 2
    assert len(prose) == 2
    assert "long-surname-source-3" in json.dumps(prose[0])
    assert "long-surname-source-4" not in json.dumps(prose[0])
    assert "long-surname-source-4" in json.dumps(prose[1])
