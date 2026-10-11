"""Finite AST/native DATA joins; no fixture creates Source/OS authority."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from infrastructure.reporting.native_code_native_endpoints import pdf_native_endpoints, selected_ast_roles
from infrastructure.reporting.native_format_pdf_semantic_plan import compile_pdf_semantic_plan
from infrastructure.reporting.native_office_ordered_blocks import ordered_office_block_correspondence
from infrastructure.reporting.native_oracle_selected_lineage import selected_value_lineage_residuals


def _ast(blocks: list[dict[str, Any]]) -> bytes:
    return json.dumps({"pandoc-api-version": [1, 23, 1], "meta": {}, "blocks": blocks}).encode()


def _para(text: str) -> dict[str, Any]:
    return {"t": "Para", "c": [{"t": "Str", "c": text}]}


def _mapping(index: int, first: int = 0, last: int = 2) -> dict[str, Any]:
    path = ["blocks", index, "c", 0, "c"]
    return {
        "boundary_kind": "exact-occurrence",
        "container_ast_path": None,
        "start": {"ast_path": path, "offset": first, "kind": "literal-codepoint"},
        "end": {"ast_path": path, "offset": last, "kind": "literal-codepoint"},
    }


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return value["c"] if value.get("t") == "Str" else _text(value.get("c", []))
    if isinstance(value, list):
        return " ".join(_text(child) for child in value)
    return ""


def test_equal_numbers_select_actual_ast_block_without_native_text_search() -> None:
    ast = _ast([_para("12"), _para("12")])
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("actual.md", b"12\n\n12"),), ast)
    literal = {
        "matches": [
            {"block_id": plan.text[0].id, "word_indices": [3]},
            {"block_id": plan.text[1].id, "word_indices": [9]},
        ],
        "supported_words": [
            {"word_index": 3, "page": 1, "box_pt": [1, 2, 3, 4]},
            {"word_index": 9, "page": 2, "box_pt": [5, 6, 7, 8]},
        ],
    }
    predicates = {
        "source_plan": plan.to_dict(),
        "findings": [],
        "witness": {"findings": [], "literal": literal, "tables": {"rows": []}, "equations": None},
    }
    result = pdf_native_endpoints(ast, _mapping(1), predicates)
    assert result["residuals"] == []
    assert result["roles"][0]["ast_path"] == ["blocks", 1, "c", 0]
    assert result["roles"][0]["endpoints"][0]["words"][0]["word_index"] == 9
    literal["matches"].pop()
    assert pdf_native_endpoints(ast, _mapping(1), predicates)["residuals"]


def test_complete_literal_members_keep_code_and_nested_link_identity() -> None:
    ast = _ast(
        [
            {
                "t": "Para",
                "c": [
                    {"t": "Code", "c": [["", [], []], "12"]},
                    {"t": "Space"},
                    {"t": "Link", "c": [["", [], []], [{"t": "Str", "c": "12"}], ["x", ""]]},
                ],
            }
        ]
    )
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("actual.md", b"`12` [12](x)"),), ast)
    members = plan.literal_members[0]["ast_paths"]
    assert "blocks/0/c/0" in members
    assert "blocks/0/c/2/c/1/0" in members
    assert {row["kind"] for row in plan.occurrences} >= {"Code", "Link"}


@pytest.mark.parametrize("change", ["extra", "missing", "reordered", "changed"])
def test_complete_office_native_block_disagreements_cannot_grant_endpoint(change: str) -> None:
    source = _ast([_para("first"), _para("second")])
    native = [_para("first"), _para("second")]
    if change == "extra":
        native.append(_para("extra"))
    elif change == "missing":
        native.pop()
    elif change == "reordered":
        native.reverse()
    else:
        native[1] = _para("changed")
    result = ordered_office_block_correspondence(source, source, _ast(native), text=_text)
    assert result["findings"] and result["witnesses"] == []


def test_repeated_office_prose_retains_true_ordered_paths() -> None:
    ast = _ast([_para("12"), _para("12")])
    result = ordered_office_block_correspondence(ast, ast, ast, text=_text)
    assert result["findings"] == []
    assert [row["native"]["ast_path"] for row in result["witnesses"]] == [["blocks", 0], ["blocks", 1]]


def test_filtered_own_source_is_separate_from_unfiltered_coverage_identity() -> None:
    source, filtered = _ast([_para("@author")]), _ast([_para("Author (2026)")])
    result = ordered_office_block_correspondence(source, filtered, filtered, text=_text)
    assert result["source_ast_sha256"] != result["filtered_ast_sha256"]
    assert result["witnesses"][0]["filtered"]["text"] == "Author (2026)"
    assert "source" not in result["witnesses"][0]


def test_multiblock_payload_keeps_all_ordered_literal_roles() -> None:
    ast = _ast([_para("12"), _para("34")])
    mapping = {
        "boundary_kind": "exact-occurrence",
        "container_ast_path": None,
        "start": {"ast_path": ["blocks"], "offset": 0, "kind": "ordered-list-boundary"},
        "end": {"ast_path": ["blocks"], "offset": 2, "kind": "ordered-list-boundary"},
    }
    assert [row["ast_path"] for row in selected_ast_roles(ast, mapping)] == [
        ["blocks", 0, "c", 0],
        ["blocks", 1, "c", 0],
    ]


@pytest.mark.parametrize("change", ["backwards", "missing-path", "out-of-range"])
def test_unbound_ast_intervals_refuse(change: str) -> None:
    ast = _ast([_para("12")])
    mapping = _mapping(0)
    if change == "backwards":
        mapping["start"]["offset"] = 2
        mapping["end"]["offset"] = 0
    elif change == "missing-path":
        mapping["start"]["ast_path"] = ["blocks", 10]
    else:
        mapping["end"]["offset"] = 3
    with pytest.raises(ValueError):
        selected_ast_roles(ast, mapping)


def _facts() -> tuple[dict[str, Any], str]:
    occurrence = {
        "source": {"path": "projects/selected/manuscript/a.md"},
        "consumed": {"path": "projects/selected/output/manuscript/a.md"},
        "ordinal": 1,
        "key": "VALUE",
        "replacement_sha256": "a" * 64,
    }
    reason = "consumed-value-native-location-link:projects/selected/manuscript/a.md:1:VALUE"
    value = {
        "selected_occurrences": [occurrence],
        "residuals": [reason],
        "code_native_locations": {
            "artifacts": [
                {
                    "artifact_id": "manuscript:pdf",
                    "source_inputs": [occurrence["consumed"]],
                    "occurrences": [
                        {
                            "hydration": occurrence,
                            "roles": [{"actual complete containing role": "DATA"}],
                            "residuals": [],
                        }
                    ],
                }
            ]
        },
    }
    return value, reason


def test_domain_baseline_stays_while_only_projected_exact_native_location_closes() -> None:
    value, reason = _facts()
    baseline = (reason, "separate-scientific-control-failure")
    assert selected_value_lineage_residuals((value,), "manuscript:pdf", baseline, native_qualified=False) == baseline
    assert selected_value_lineage_residuals((value,), "manuscript:pdf", baseline, native_qualified=True) == baseline[1:]
    assert value["residuals"] == [reason]


def test_reader_requires_both_original_and_fresh_current_native_occurrence() -> None:
    original, reason = _facts()
    current = copy.deepcopy(original)
    current["code_native_locations"]["artifacts"][0]["occurrences"][0]["residuals"] = [
        "actual unsupported Code native role"
    ]
    assert reason in selected_value_lineage_residuals(
        (original, current), "manuscript:pdf", (reason,), native_qualified=True
    )


def test_complete_section_source_absence_does_not_invent_a_native_occurrence() -> None:
    value, reason = _facts()
    row = value["code_native_locations"]["artifacts"][0]
    row["source_inputs"], row["occurrences"] = [{"path": "projects/selected/output/manuscript/b.md"}], []
    assert selected_value_lineage_residuals((value,), "manuscript:pdf", (reason,), native_qualified=True) == ()


def test_changed_payload_binding_cannot_use_same_source_key_ordinal_endpoint() -> None:
    value, reason = _facts()
    row = value["code_native_locations"]["artifacts"][0]["occurrences"][0]
    row["hydration"] = {**row["hydration"], "replacement_sha256": "b" * 64}
    with pytest.raises(ValueError, match="exact Source/key/ordinal"):
        selected_value_lineage_residuals((value,), "manuscript:pdf", (reason,), native_qualified=True)


def test_whole_table_interval_requires_every_actual_literal_and_math_cell() -> None:
    attrs = ["", [], []]
    plain = {"t": "Plain", "c": [{"t": "Str", "c": "12"}]}
    math = {"t": "Plain", "c": [{"t": "Math", "c": [{"t": "InlineMath"}, "x=12"]}]}

    def cell(block: dict[str, Any]) -> list[Any]:
        return [attrs, {"t": "AlignDefault"}, 1, 1, [block]]

    table = {
        "t": "Table",
        "c": [
            attrs,
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}]] * 2,
            [attrs, [[attrs, [cell(plain), cell(math)]]]],
            [],
            [attrs, []],
        ],
    }
    ast = _ast([table])
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("actual.md", b"|12|$x=12$|"),), ast)
    cells = plan.tables[0]["rows"][0]["cells"]
    equation = next(row for row in plan.occurrences if row["kind"] == "Math")
    mapping = {
        "boundary_kind": "containing-table",
        "container_ast_path": ["blocks", 0],
        "start": {"ast_path": ["blocks"], "offset": 0, "kind": "containing-table-boundary"},
        "end": {"ast_path": ["blocks"], "offset": 1, "kind": "containing-table-boundary"},
    }
    witness = {
        "findings": [],
        "literal": {
            "matches": [{"block_id": plan.text[0].id, "word_indices": [0]}],
            "supported_words": [{"word_index": 0, "page": 1, "box_pt": [1, 2, 3, 4]}],
        },
        "tables": {
            "rows": [
                {"table_identity": "blocks/0", "row": 0, "cells": [{"identity": item["identity"]} for item in cells]}
            ]
        },
        "equations": {"observations": [{"identity": equation["identity"], "page": 1, "box_pt": [5, 2, 8, 4]}]},
    }
    predicates = {"source_plan": plan.to_dict(), "witness": witness, "findings": []}
    result = pdf_native_endpoints(ast, mapping, predicates)
    assert not result["residuals"]
    assert {row["kind"] for row in result["roles"]} == {"Table", "Str", "Math"}
    witness["tables"]["rows"][0]["cells"].pop()
    assert (
        "selected-PDF-native-containing-role:blocks/0:Table"
        in pdf_native_endpoints(ast, mapping, predicates)["residuals"]
    )
