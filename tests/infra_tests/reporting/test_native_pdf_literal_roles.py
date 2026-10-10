"""Finite literal/caption DATA predicates; no fixture supplies Source custody."""

from __future__ import annotations

import copy
import json
import time
from typing import Any

import pytest

from infrastructure.reporting.native_format_pdf_figure_positions import bind_pdf_figure_positions
from infrastructure.reporting.native_format_pdf_semantic_plan import (
    compile_pdf_semantic_plan,
    exact_figure_caption_alias,
)
from infrastructure.reporting.native_format_scientific_math import scientific_math_from_ast
from infrastructure.reporting.native_pdf_literal_roles import inspect_pdf_literal_roles
from infrastructure.reporting.native_pdf_whole_controls import compile_whole_pdf_control_requirements


def _ast(blocks: list[dict[str, Any]]) -> bytes:
    return json.dumps({"pandoc-api-version": [1, 23, 1], "meta": {}, "blocks": blocks}).encode()


def _word(index: int, left: int) -> dict[str, Any]:
    return {
        "word_index": index,
        "page": 1,
        "box_pt": [left, 10, left + 4, 15],
        "fonts": ["actual-source-font"],
        "min_font_pt": 10,
        "roi_px": [1, 2, 3, 4],
    }


def _parity() -> dict[str, Any]:
    return {"findings": [], "pages": [{"glyphs_match": True, "vectors_match": True, "pixels_match": True}]}


def _literal(plan: Any) -> dict[str, Any]:
    return {
        "findings": [],
        "blockers": [],
        "pages": [{"page": 1}],
        "matches": [
            {
                "block_id": plan.text[0].id,
                "token_span": [0, 3],
                "word_indices": [0, 1, 2],
                "token_word_indices": [0, 1, 2],
            }
        ],
        "supported_words": [_word(0, 1), _word(1, 11), _word(2, 21)],
        "links": [],
    }


def _code_plan() -> Any:
    ast = _ast(
        [
            {
                "t": "Para",
                "c": [
                    {"t": "Str", "c": "12"},
                    {"t": "Space"},
                    {"t": "Code", "c": [["", [], []], "12"]},
                    {"t": "Space"},
                    {"t": "Str", "c": "12"},
                ],
            }
        ]
    )
    return compile_pdf_semantic_plan("manuscript:pdf", (("actual.md", b"12 `12` 12"),), ast)


def test_inline_code_uses_exact_source_partition_among_equal_numbers() -> None:
    plan = _code_plan()
    actual = _literal(plan)
    result = inspect_pdf_literal_roles(plan, actual, copy.deepcopy(actual), _parity(), deadline=time.monotonic() + 60)
    assert not result["findings"] and not result["blockers"]
    assert result["observations"][0]["source_token_span"] == [1, 2]
    assert [row["word_index"] for row in result["observations"][0]["words"]] == [1]


@pytest.mark.parametrize("change", ["source-span", "missing-word", "font", "position", "page-parity"])
def test_code_cannot_borrow_another_role_or_failed_native_reference(change: str) -> None:
    plan = _code_plan()
    actual, expected, parity = _literal(plan), _literal(plan), _parity()
    if change == "source-span":
        plan.literal_members[0]["occurrence_token_spans"].clear()
    elif change == "missing-word":
        actual["supported_words"].pop(1)
    elif change == "font":
        actual["supported_words"][1]["fonts"] = ["other-font"]
    elif change == "position":
        actual["supported_words"][1]["box_pt"][0] += 2
    else:
        parity["pages"][0]["pixels_match"] = False
    result = inspect_pdf_literal_roles(plan, actual, expected, parity, deadline=time.monotonic() + 60)
    assert not result["observations"]
    assert result["findings"] or result["blockers"]


def test_unseparable_inline_word_stays_unsupported() -> None:
    ast = _ast([{"t": "Para", "c": [{"t": "Str", "c": "ab"}, {"t": "Code", "c": [["", [], []], "cd"]}]}])
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("actual.md", b"ab`cd`"),), ast)
    assert plan.literal_members[0]["occurrence_token_spans"] == []


@pytest.mark.parametrize("change", ["none", "target", "missing", "ambiguous", "reference-target"])
def test_link_requires_exact_own_source_and_native_annotation(change: str) -> None:
    uri = "https://example.org/source"
    ast = _ast(
        [{"t": "Para", "c": [{"t": "Link", "c": [["", [], []], [{"t": "Str", "c": "actual link label"}], [uri, ""]]}]}]
    )
    plan = compile_pdf_semantic_plan(
        "manuscript:pdf", (("actual.md", b"[actual link label](https://example.org/source)"),), ast
    )
    actual, expected = _literal(plan), _literal(plan)
    link = {"page": 1, "annotation_index": 0, "uri": uri, "box_pt": [0, 9, 26, 16]}
    actual["links"], expected["links"] = [copy.deepcopy(link)], [copy.deepcopy(link)]
    if change == "target":
        actual["links"][0]["uri"] = "https://example.org/other"
    elif change == "missing":
        actual["links"] = []
    elif change == "ambiguous":
        actual["links"].append(copy.deepcopy(link))
    elif change == "reference-target":
        expected["links"][0]["uri"] = "https://example.org/other"
    result = inspect_pdf_literal_roles(plan, actual, expected, _parity(), deadline=time.monotonic() + 60)
    assert bool(result["observations"]) == (change == "none")
    assert bool(result["findings"]) == (change != "none")


def test_exact_literal_role_feeds_existing_full_occurrence_paint_control() -> None:
    plan = _code_plan()
    literal = _literal(plan)
    roles = inspect_pdf_literal_roles(plan, literal, copy.deepcopy(literal), _parity(), deadline=time.monotonic() + 60)
    witness = {
        "source_plan_digest": plan.digest,
        "pdf_sha256": "a" * 64,
        "literal": literal,
        "notes": None,
        "figures": {"figures": []},
        "equations": None,
        "citations": None,
        "tables": {"rows": []},
        "literal_roles": roles,
    }
    controls = compile_whole_pdf_control_requirements(plan, witness, deadline=time.monotonic() + 60)
    row = next(row for row in controls["controls"] if row["source_identity"] == "blocks/0/c/2")
    assert row["unsupported"] is None
    assert row["target"] == [{"page": 1, "box_pt": [11.0, 10.0, 15.0, 15.0]}]


def _figure() -> dict[str, Any]:
    caption = [{"t": "Str", "c": "measured"}, {"t": "Space"}, {"t": "Math", "c": [{"t": "InlineMath"}, "x=12"]}]
    return {
        "t": "Figure",
        "c": [
            ["figure", [], []],
            [None, [{"t": "Plain", "c": caption}]],
            [{"t": "Plain", "c": [{"t": "Image", "c": [["", [], []], copy.deepcopy(caption), ["actual.png", ""]]}]}],
        ],
    }


def test_exact_rich_caption_alias_retains_primary_math_and_original_paths() -> None:
    figure = _figure()
    ast = _ast([figure])
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("actual.md", b"![measured $x=12$](actual.png)"),), ast)
    math_rows = [row for row in plan.occurrences if row["kind"] == "Math"]
    assert [row.identity for row in scientific_math_from_ast(ast)] == [math_rows[0]["identity"]]
    image = next(row for row in plan.occurrences if row["kind"] == "Image")
    assert image["exact_caption_ast_alias"]["visible"] == "blocks/0/c/1/1/0/c"
    assert image["exact_caption_ast_alias"]["alternative"] == "blocks/0/c/2/0/c/0/c/1"
    assert image["rendered_caption_occurrence_ids"] == [math_rows[0]["identity"]]
    assert not plan.blockers


@pytest.mark.parametrize("change", ["different-math", "short-caption", "extra-body", "bad-caption", "bad-image"])
def test_unmatched_or_malformed_figure_never_gets_exact_alias(change: str) -> None:
    figure = _figure()
    if change == "different-math":
        figure["c"][2][0]["c"][0]["c"][1][2]["c"][1] = "x=13"
    elif change == "short-caption":
        figure["c"][1][0] = [{"t": "Str", "c": "override"}]
    elif change == "extra-body":
        figure["c"][2].append({"t": "Para", "c": []})
    elif change == "bad-caption":
        figure["c"][1][1][0] = "malformed"
    else:
        figure["c"][2][0]["c"][0]["c"] = []
    assert exact_figure_caption_alias(figure) is None


def test_rich_caption_math_needs_actual_independent_native_position() -> None:
    ast = _ast([_figure()])
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("actual.md", b"figure"),), ast)
    image = next(row for row in plan.occurrences if row["kind"] == "Image")
    literal = {
        "findings": [],
        "blockers": [],
        "matches": [{"block_id": plan.text[0].id, "word_indices": [0]}],
        "supported_words": [_word(0, 1)],
    }
    native = {"identity": image["identity"], "covered": True, "page": 1, "box_pt": [0, 1, 20, 8]}
    figures = {"figures": [copy.deepcopy(native)], "findings": [], "blockers": []}
    parameters = {
        "reference_literal": literal,
        "reference_figures": {"figures": [native], "findings": [], "blockers": []},
        "whole_page_parity": _parity(),
        "deadline": time.monotonic() + 60,
    }
    missing = bind_pdf_figure_positions(plan, literal, figures, **parameters)
    assert missing["blockers"] and not missing["positions"]
    equation = {"identity": image["rendered_caption_occurrence_ids"][0], "page": 1, "box_pt": [8, 10, 18, 15]}
    checked = bind_pdf_figure_positions(plan, literal, figures, equations={"observations": [equation]}, **parameters)
    assert not checked["blockers"] and checked["positions"][0]["covered"]
