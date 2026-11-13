"""Finite AST/native DATA joins; no fixture creates Source/OS authority."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from infrastructure.rendering.manuscript_hydration_replay import require_shared_hydration
from infrastructure.rendering.manuscript_injection import write_resolved_manuscript_tree
from infrastructure.reporting.native_code_native_endpoints import pdf_native_endpoints, selected_ast_roles
from infrastructure.reporting.native_code_native_locations import (
    CODE_SCOPE,
    _binding,
    _context_inputs,
    _inputs,
    _selected,
)
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_content_contracts import semantic_content_contract_from_ast
from infrastructure.reporting.native_format_pdf_semantic_plan import compile_pdf_semantic_plan
from infrastructure.reporting.native_format_semantic_source import (
    semantic_contract_ast,
    semantic_lua_filters,
    semantic_parser_options,
)
from infrastructure.reporting.native_html_hydration_ordinals import compose_html_ordinal_input
from infrastructure.reporting.native_office_ordered_blocks import ordered_office_block_correspondence
from infrastructure.reporting.native_oracle_selected_lineage import _occurrences, selected_value_lineage_residuals
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


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


@pytest.mark.parametrize(
    ("artifact_id", "owned_indices", "expected_keys"),
    [
        ("manuscript:html", (0, 1, 2), ["RESULT_TABLE_ROWS", "SETUP", "SETUP"]),
        ("section:03_results.md:html", (0,), ["RESULT_TABLE_ROWS"]),
        ("section:05_experimental_setup.md:html", (1,), ["SETUP", "SETUP"]),
        ("section:06_token_free.md:html", (2,), []),
    ],
)
def test_real_html_owned_inputs_drive_occurrences_and_section_absence(
    tmp_path: Path, artifact_id: str, owned_indices: tuple[int, ...], expected_keys: list[str]
) -> None:
    """Real writer/parser DATA separates ownership; no native authority is constructed."""
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("pandoc not available on PATH")
    project = tmp_path / "projects" / CODE_SCOPE
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    names = ("03_results.md", "05_experimental_setup.md", "06_token_free.md")
    authored = (
        b"# Results\n\n| Method | Value |\n| --- | --- |\n{{RESULT_TABLE_ROWS}}\n",
        b"# Setup\n\nValue {{SETUP}}, repeated {{SETUP}}.\n",
        b"# Discussion\n\nAuthored text without generated tokens.\n",
    )
    for name, content in zip(names, authored, strict=True):
        (manuscript / name).write_bytes(content)
    values = {"RESULT_TABLE_ROWS": "| scalar | 7 |", "SETUP": "7"}
    consumed = write_resolved_manuscript_tree(project, values)
    reader = SnapshotReader(tmp_path)
    sources = tuple(reader.read((consumed / name).relative_to(tmp_path).as_posix()) for name in names)
    hydration = {
        "ordered_inputs": [
            {
                "ordinal": ordinal,
                "source": _binding(reader.read((manuscript / name).relative_to(tmp_path).as_posix())),
                "consumed": _binding(snapshot),
                "transformation": "shared-uppercase-token-hydration",
                "hydration": require_shared_hydration(content, values, snapshot.content).data(),
            }
            for ordinal, (name, content, snapshot) in enumerate(zip(names, authored, sources, strict=True), 1)
        ]
    }
    context_sources = tuple((snapshot.relative, snapshot.content) for snapshot in sources)
    arguments = [pandoc, *semantic_parser_options(tmp_path, CODE_SCOPE)]
    for lua_filter in semantic_lua_filters():
        arguments.extend(["--lua-filter", str(lua_filter)])
    actual_ast = subprocess.run(
        arguments,
        input=compose_html_ordinal_input(tuple(snapshot.content for snapshot in sources)),
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    artifact = NativeArtifact(artifact_id, "html", f"projects/{CODE_SCOPE}/output/web/selected.html")
    contract = semantic_content_contract_from_ast(
        artifact_id,
        context_sources,
        semantic_contract_ast(tmp_path, CODE_SCOPE, artifact, context_sources, actual_ast),
    )
    observer = {"semantic_source": {"body": {"contract": contract.to_dict()}}}
    context = _context_inputs(artifact, observer, reader)
    owned = _inputs(artifact, observer, reader)
    assert context == [_binding(snapshot) for snapshot in sources]
    assert owned == [context[index] for index in owned_indices]
    complete, residuals = _occurrences(hydration)
    assert residuals == []
    assert _selected(hydration, context)[0] == complete
    selected, _ = _selected(hydration, owned)
    assert [row["key"] for row in complete] == ["RESULT_TABLE_ROWS", "SETUP", "SETUP"]
    assert [row["key"] for row in selected] == expected_keys
    assert selected == [row for row in complete if row["consumed"] in owned]
    assert len({(row["source"]["path"], row["ordinal"]) for row in selected}) == len(selected)
    reasons = [
        "consumed-value-native-location-link:" + row["source"]["path"] + f":{row['ordinal']}:{row['key']}"
        for row in complete
    ]
    baseline = (*reasons, "separate-scientific-control-failure")
    facts = {
        "selected_occurrences": complete,
        "residuals": reasons,
        "code_native_locations": {
            "artifacts": [{"artifact_id": artifact_id, "source_inputs": owned, "occurrences": []}]
        },
    }
    assert selected_value_lineage_residuals((facts,), artifact_id, baseline, native_qualified=False) == baseline
    expected = tuple(reason for row, reason in zip(complete, reasons, strict=True) if row["consumed"] in owned)
    assert selected_value_lineage_residuals(
        (facts, copy.deepcopy(facts)), artifact_id, baseline, native_qualified=True
    ) == (*expected, "separate-scientific-control-failure")
    repeated = copy.deepcopy(facts)
    repeated["code_native_locations"]["artifacts"][0]["source_inputs"].append(copy.deepcopy(owned[0]))
    with pytest.raises(ValueError, match="repeated an artifact-owned"):
        selected_value_lineage_residuals((repeated,), artifact_id, baseline, native_qualified=True)
    if selected:
        changed = copy.deepcopy(facts)
        changed["code_native_locations"]["artifacts"][0]["source_inputs"][0]["bytes"] += 1
        with pytest.raises(ValueError, match="exact owned Source input body"):
            selected_value_lineage_residuals((changed,), artifact_id, baseline, native_qualified=True)
    foreign = next((row for row in complete if row["consumed"] not in owned), None)
    if foreign is not None:
        facts["code_native_locations"]["artifacts"][0]["occurrences"] = [{"hydration": foreign}]
        with pytest.raises(ValueError, match="foreign occurrence"):
            selected_value_lineage_residuals((facts,), artifact_id, baseline, native_qualified=True)
    assert reader.unchanged()


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
