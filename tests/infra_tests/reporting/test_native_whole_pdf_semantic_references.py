"""Real Source censuses and complete control selection; no native pass fixtures.

These pure DATA transforms do not supply Original/current owner authority. The
full genuine native ToolAPI/FLS/reference qualification remains an outer gate.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import replace

import pytest

from infrastructure.reporting.native_format_pdf_semantic_plan import compile_pdf_semantic_plan
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_scientific_math import scientific_math_from_ast
from infrastructure.reporting.native_pdf_citations import citation_occurrences
from infrastructure.reporting.native_pdf_whole_semantic_references import (
    _citation_blockers,
    _manifest,
    _math_blockers,
    citation_occurrence_positions,
    source_crossref_keys,
    whole_pdf_semantic_inputs,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _ast(blocks):
    return json.dumps({"pandoc-api-version": [1, 23, 1], "meta": {}, "blocks": blocks}).encode()


def _cite(key):
    return {
        "t": "Cite",
        "c": [
            [
                {
                    "citationId": key,
                    "citationPrefix": [],
                    "citationSuffix": [],
                    "citationMode": {"t": "NormalCitation"},
                    "citationNoteNum": 0,
                    "citationHash": 0,
                }
            ],
            [{"t": "Str", "c": "@" + key}],
        ],
    }


def _inputs():
    return PDFSourceInputs(
        b"whole manuscript",
        (("source.md", b"original Source"),),
        ("config.yaml", b"metadata: {}\n"),
        None,
        (("references.bib", b"@book{fig:looks-like-a-crossref, title={A}, year={2000}}"),),
        (),
    )


def test_crossref_census_uses_every_explicit_source_attribute_and_no_cite_prefix():
    ast = _ast(
        [
            {"t": "Header", "c": [1, ["sec:intro", [], []], [{"t": "Str", "c": "Introduction"}]]},
            {
                "t": "Para",
                "c": [
                    {"t": "Image", "c": [["fig:actual", [], []], [{"t": "Str", "c": "caption"}], ["image.png", ""]]},
                    {"t": "Span", "c": [["eq:actual", [], []], [{"t": "Math", "c": [{"t": "DisplayMath"}, "x^2"]}]]},
                    _cite("fig:looks-like-a-crossref"),
                    _cite("fig:unbound"),
                ],
            },
            {"t": "CodeBlock", "c": [["lst:actual", [], []], "@fig:inside-literal-code"]},
            {"t": "RawBlock", "c": ["latex", r"\label{fig:dynamic}"]},
        ]
    )
    deadline = time.monotonic() + 10
    keys = source_crossref_keys(ast, deadline=deadline)
    assert keys == ("sec:intro", "fig:actual", "eq:actual", "lst:actual")
    _, occurrences, _, _ = citation_occurrences(ast, deadline=deadline, crossref_keys=keys)
    assert [row.keys for row in occurrences] == [("fig:looks-like-a-crossref",), ("fig:unbound",)]
    blockers = _citation_blockers(_inputs(), ast, keys, deadline=deadline)
    assert len(blockers) == 1 and "citation:000002" in blockers[0] and "fig:unbound" in blockers[0]


def test_duplicate_source_crossref_identity_refuses_instead_of_dropping_an_occurrence():
    ast = _ast(
        [{"t": "Header", "c": [1, ["sec:repeat", [], []], []]}, {"t": "Header", "c": [2, ["sec:repeat", [], []], []]}]
    )
    with pytest.raises(ValueError, match="identity repeats"):
        source_crossref_keys(ast, deadline=time.monotonic() + 10)


def test_missing_reference_is_selected_source_absence_not_an_unconditional_gap(tmp_path):
    reader = SnapshotReader(tmp_path)
    ordinary = _ast([{"t": "Para", "c": [{"t": "Str", "c": "ordinary"}]}])
    assert whole_pdf_semantic_inputs(_inputs(), ordinary, None, reader, deadline=time.monotonic() + 10) == (
        None,
        None,
        [],
    )
    selected = _ast(
        [{"t": "Para", "c": [_cite("fig:looks-like-a-crossref"), {"t": "Math", "c": [{"t": "InlineMath"}, "x^2"]}]}]
    )
    citation, mathematics, blockers = whole_pdf_semantic_inputs(
        _inputs(), selected, None, reader, deadline=time.monotonic() + 10
    )
    assert citation is mathematics is None
    assert len(blockers) == 2 and "selected citation" in blockers[0] and "selected equation" in blockers[1]
    assert reader.native_operation is None and reader.native_producer_operation is None


def test_all_repeated_math_contexts_remain_selected_when_one_dynamic_scope_is_unsupported():
    ast = _ast(
        [
            {"t": "Para", "c": [{"t": "Math", "c": [{"t": "InlineMath"}, "x^2"]}]},
            {
                "t": "Para",
                "c": [
                    {
                        "t": "Note",
                        "c": [{"t": "Para", "c": [{"t": "Math", "c": [{"t": "InlineMath"}, r"\input{external}"]}]}],
                    }
                ],
            },
            {"t": "Header", "c": [2, ["", [], []], [{"t": "Math", "c": [{"t": "InlineMath"}, "x^2"]}]]},
        ]
    )
    nodes = scientific_math_from_ast(ast)
    assert [node.context for node in nodes] == ["body", "footnote", "heading:2"]
    assert len({node.identity for node in nodes}) == 3
    blockers = _math_blockers(ast)
    assert len(blockers) == len(nodes) and all(
        node.identity in blocker for node, blocker in zip(nodes, blockers, strict=True)
    )
    assert _math_blockers(_ast([{"t": "Para", "c": [{"t": "Math", "c": [{"t": "InlineMath"}, "x^2"]}]}])) == []


def test_complete_input_identity_changes_when_an_uncited_bibliography_or_layout_input_changes():
    ast = _ast([])
    inputs = _inputs()
    original = _manifest(inputs, ast)
    assert original["ast_sha256"] == hashlib.sha256(ast).hexdigest()
    assert (
        _manifest(replace(inputs, bibliographies=(("references.bib", b"@book{uncited, title={Changed}}"),)), ast)
        != original
    )
    assert _manifest(replace(inputs, config=("config.yaml", b"metadata: {fontsize: 12pt}")), ast) != original
    assert _manifest(replace(inputs, preamble=("preamble.md", b"changed font declaration")), ast) != original
    assert _manifest(replace(inputs, auxiliary=(("manuscript_vars.yaml", b"changed Source value"),)), ast) != original


def test_control_selector_requires_every_glyph_of_each_complete_source_occurrence():
    ast = _ast([{"t": "Para", "c": [_cite("one"), _cite("two")]}])
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("source.md", b"two citations"),), ast)
    # This remains only a Source-plan/glyph DATA fixture. No receipt or ToolAPI
    # outcome is supplied, and this selector cannot authorize native admission.
    plan = replace(
        plan,
        occurrences=tuple(
            {**row, "citation_reference_id": f"citation:{index:06d}"} for index, row in enumerate(plan.occurrences, 1)
        ),
    )
    observation = {
        "matches": [
            {"occurrence_id": "citation:000001", "glyph_indices": [0, 1]},
            {"occurrence_id": "citation:000002", "glyph_indices": [2, 3]},
        ],
        "observed_glyphs": [
            {
                "glyph_index": index,
                "page": 1,
                "box_pt": [index * 10, 10, index * 10 + 8, 20],
                "geometry_supported": True,
                "roi_px": [0, 0, 8, 10],
            }
            for index in range(4)
        ],
    }
    selected = citation_occurrence_positions(plan, observation, deadline=time.monotonic() + 10)
    assert list(selected) == ["occurrence:" + row["identity"] for row in plan.occurrences]
    assert [len(boxes) for boxes in selected.values()] == [2, 2]
    del observation["observed_glyphs"][-1]["roi_px"]
    missing = citation_occurrence_positions(plan, observation, deadline=time.monotonic() + 10)
    assert list(missing) == ["occurrence:" + plan.occurrences[0]["identity"]]
    assert citation_occurrence_positions(plan, None, deadline=time.monotonic() + 10) == {}
