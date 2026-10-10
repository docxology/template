"""Pure HTML input/Figure cases; no JSON constructs native authority."""

from __future__ import annotations

import hashlib
import json

import pytest

from infrastructure.rendering.manuscript_ordinal_anchors import (
    annotate_manuscript_ordinals,
    require_unannotated_parser_bytes,
)
from infrastructure.reporting.native_format_html_glyph_contours import compile_source_character_runs
from infrastructure.reporting.native_html_hydration_ordinals import compose_html_ordinal_input, _table_native_projection
from infrastructure.reporting.native_format_semantic_ast import compile_semantic_ast
from infrastructure.reporting.native_format_html_image_alt import (
    compile_original_image_alt,
    figure_caption_image_aliases,
    inspect_original_image_alt,
)


def _ast(blocks: list[dict]) -> bytes:
    return json.dumps({"pandoc-api-version": [1, 23, 1], "meta": {}, "blocks": blocks}).encode()


def _str(text: str) -> dict:
    return {"t": "Str", "c": text}


def _figure(caption: list[dict], *, short: list[dict] | None = None) -> dict:
    return {
        "t": "Figure",
        "c": [
            ["fig:case", [], []],
            [short, [{"t": "Plain", "c": caption}]],
            [{"t": "Plain", "c": [{"t": "Image", "c": [["", [], []], caption, ["figure.png", ""]]}]}],
        ],
    }


def test_combined_html_keeps_own_source_order_and_separator() -> None:
    assert (
        compose_html_ordinal_input((b"\nfirst  \n\n", b"second\n"), combined=True)
        == b"first\n\n\n\n---\n\n\n\nsecond\n"
    )


def test_section_html_keeps_own_original_newlines() -> None:
    assert compose_html_ordinal_input((b"\nfirst  \n\n",), combined=False) == b"\nfirst  \n\n"


def test_section_cannot_acquire_combined_inputs() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        compose_html_ordinal_input((b"a\n", b"b\n"), combined=False)


def test_combined_html_preserves_citations_for_real_citeproc() -> None:
    body = b"Study [@first; @second] and [@fig:plot].\n"
    assert compose_html_ordinal_input((body,), combined=True) == body


def test_section_html_uses_actual_citation_text_but_retains_crossrefs() -> None:
    body = b"Study [@first; @second] and [@fig:plot].\n"
    assert compose_html_ordinal_input((body,), combined=False) == b"Study [first; second] and [@fig:plot].\n"


def test_html_uses_actual_raw_latex_and_image_path_transform() -> None:
    body = b"`\\hyperref[item]{visible}`{=latex} ![Figure](../../output/figures/plot.png)\n"
    assert compose_html_ordinal_input((body,), combined=True) == b"visible ![Figure](../figures/plot.png)\n"


@pytest.mark.parametrize("combined", [False, True])
def test_html_ordinal_bytes_retain_unicode_exact_payload_and_own_input_offsets(combined: bool) -> None:
    body = "Before é and $0.01$ after.\n".encode()
    first = len("Before ".encode())
    last = first + len("é".encode())
    marked, anchors = annotate_manuscript_ordinals(
        (body,), ((0, 1, "UNICODE", first, last, hashlib.sha256(body[first:last]).hexdigest()),)
    )
    original = compose_html_ordinal_input((body,), combined=combined)
    annotated = compose_html_ordinal_input(marked, combined=combined)
    assert require_unannotated_parser_bytes(annotated, original, anchors) == ((first, last),)


def test_html_complete_table_carrier_preserves_actual_grid_and_payload_interval() -> None:
    body = b"| Key | Value |\n| --- | --- |\n| a | 7 |\n"
    first = body.index(b"a |")
    last = first + len(b"a | 7")
    marked, anchors = annotate_manuscript_ordinals(
        (body,), ((0, 1, "TABLE", first, last, hashlib.sha256(body[first:last]).hexdigest()),)
    )
    assert anchors[0].boundary_kind == "containing-table"
    assert (anchors[0].carrier_first, anchors[0].carrier_last) == (0, len(body) - 1)
    assert require_unannotated_parser_bytes(
        compose_html_ordinal_input(marked, combined=True), compose_html_ordinal_input((body,), combined=True), anchors
    ) == ((first, last),)


def test_html_transform_inside_selected_payload_is_refused_without_a_span_adapter() -> None:
    body = b"`\\hyperref[item]{visible}`{=latex}\n"
    first, last = 1, len(body) - len(b"`{=latex}\n")
    marked, anchors = annotate_manuscript_ordinals(
        (body,), ((0, 1, "RAW", first, last, hashlib.sha256(body[first:last]).hexdigest()),)
    )
    with pytest.raises(ValueError):
        require_unannotated_parser_bytes(
            compose_html_ordinal_input(marked, combined=True),
            compose_html_ordinal_input((body,), combined=True),
            anchors,
        )


def test_modern_figure_caption_has_own_visible_source_run_and_no_alt_relabel() -> None:
    result = compile_source_character_runs(_ast([_figure([_str("seven")])]))
    assert [(row["source_id"], row["text"]) for row in result["runs"]] == [
        ("glyph-source:blocks/0/c/1/1/0/c/0", "seven")
    ]
    assert result["blockers"] == []


def test_figure_math_and_code_keep_existing_role_predicates() -> None:
    caption = [{"t": "Math", "c": [{"t": "InlineMath"}, "x+1"]}, {"t": "Code", "c": [["", [], []], "run"]}]
    result = compile_source_character_runs(_ast([_figure(caption)]))
    assert [row["text"] for row in result["runs"]] == ["run"]
    assert any("MathJax shaping/contours" in value for value in result["blockers"])
    assert any("image caption/alternative" in value for value in result["blockers"])


def test_figure_short_caption_is_separate_unsupported_role() -> None:
    result = compile_source_character_runs(_ast([_figure([_str("long")], short=[_str("short")])]))
    assert [row["text"] for row in result["runs"]] == ["long"]
    assert any("short-caption" in value for value in result["blockers"])


@pytest.mark.parametrize("content", [None, [], [["", [], []], [None], []], [["", [], []], [None, "wrong"], []]])
def test_malformed_modern_figure_cannot_supply_a_visible_caption(content: object) -> None:
    with pytest.raises(ValueError, match="modern caption/body shape"):
        compile_source_character_runs(_ast([{"t": "Figure", "c": content}]))


def test_unknown_figure_descendant_is_not_silently_ignored() -> None:
    result = compile_source_character_runs(_ast([_figure([{"t": "UnknownInline", "c": "seven"}])]))
    assert result["runs"] == []
    assert any("UnknownInline" in value for value in result["blockers"])


def test_modern_figure_semantic_caption_and_image_keep_distinct_actual_ast_ids() -> None:
    body = _ast([_figure([_str("seven")])])
    result = compile_semantic_ast((("source.md", b"![seven](figure.png)\n"),), body)
    assert [(row.id, row.tokens) for row in result["blocks"]] == [("ast:blocks/0/c/1/1/0/c:text:0", ("seven",))]
    assert result["images"] == [("ast:blocks/0/c/2/0/c/0", "figure.png", "seven")]
    assert result["blockers"] == []
    assert any(row["tag"] == "Figure" for row in result["occurrences"])


def test_modern_figure_semantics_keep_caption_math_and_rich_alt_obligation() -> None:
    caption = [_str("score"), {"t": "Space"}, {"t": "Math", "c": [{"t": "InlineMath"}, "x+1"]}]
    result = compile_semantic_ast((("source.md", b"fixture"),), _ast([_figure(caption)]))
    assert result["maths"] == [("ast:blocks/0/c/1/1/0/c/2", "x+1")]
    assert result["images"] == [("ast:blocks/0/c/2/0/c/0", "figure.png", "score x+1")]
    assert result["blockers"] == []


def test_modern_figure_semantics_do_not_drop_unknown_caption_descendants() -> None:
    result = compile_semantic_ast(
        (("source.md", b"fixture"),), _ast([_figure([{"t": "UnknownInline", "c": [_str("seven")]}])])
    )
    assert any("unsupported inline UnknownInline" in value for value in result["blockers"])
    assert any("seven" in row.tokens for row in result["blocks"])


def test_modern_figure_semantic_short_caption_stays_a_separate_role() -> None:
    result = compile_semantic_ast((("source.md", b"fixture"),), _ast([_figure([_str("long")], short=[_str("short")])]))
    assert figure_caption_image_aliases(_ast([_figure([_str("long")], short=[_str("short")])])) == {}
    assert [token for row in result["blocks"] for token in row.tokens] == ["short", "long"]


def test_math_caption_alias_has_exact_attribute_string_and_distinct_visible_math() -> None:
    caption = [_str("score"), {"t": "Space"}, {"t": "Math", "c": [{"t": "InlineMath"}, r"\alpha_{2}+1"]}]
    body = _ast([_figure(caption)])
    aliases = figure_caption_image_aliases(body)
    assert aliases["blocks/0/c/2/0/c/0"]["expected_alt"] == r"score \alpha_{2}+1"
    source = compile_original_image_alt(body, body)
    assert source["blockers"] == []
    assert source["images"][0]["caption_alias"]["caption_path"] == "blocks/0/c/1/1/0/c"
    dom = {"images": [{"src": "figure.png", "alt_present": True, "alt": r"score \alpha_{2}+1"}]}
    assert inspect_original_image_alt(source, dom)["status"] == "pass"
    dom["images"][0]["alt"] = "score alpha2+1"
    assert inspect_original_image_alt(source, dom)["status"] == "fail"
    glyph = compile_source_character_runs(body)
    assert [row["text"] for row in glyph["runs"]] == ["score"]
    assert any("MathJax shaping/contours" in item for item in glyph["blockers"])
    assert not any("image caption/alternative" in item for item in glyph["blockers"])


@pytest.mark.parametrize(
    "alternative",
    [
        [],
        [{"t": "Code", "c": [["", [], []], "x"]}],
        [{"t": "RawInline", "c": ["html", "x"]}],
        [{"t": "Strong", "c": [_str("x")]}],
    ],
)
def test_unknown_empty_or_rich_nonmodel_caption_alternatives_stay_obligated(alternative: list[dict]) -> None:
    body = _ast([_figure(alternative)])
    assert figure_caption_image_aliases(body) == {}
    assert compile_original_image_alt(body, body)["blockers"]
    assert any("image caption/alternative" in item for item in compile_source_character_runs(body)["blockers"])


def test_nonalias_math_alternative_cannot_borrow_visible_caption_model() -> None:
    figure = _figure([_str("caption")])
    figure["c"][2][0]["c"][0]["c"][1] = [{"t": "Math", "c": [{"t": "InlineMath"}, "2"]}]
    body = _ast([figure])
    assert figure_caption_image_aliases(body) == {}
    assert compile_original_image_alt(body, body)["blockers"]


def test_explicit_alt_override_does_not_acquire_alias_permission() -> None:
    figure = _figure([{"t": "Math", "c": [{"t": "InlineMath"}, "2"]}])
    figure["c"][2][0]["c"][0]["c"][0][2] = [["alt", "override"]]
    body = _ast([figure])
    assert figure_caption_image_aliases(body) == {}
    assert compile_original_image_alt(body, body)["blockers"]


def test_projected_alt_change_is_not_qualified_by_original_alias() -> None:
    original = _ast([_figure([{"t": "Math", "c": [{"t": "InlineMath"}, "2"]}])])
    projected = _ast([_figure([{"t": "Math", "c": [{"t": "InlineMath"}, "3"]}])])
    assert compile_original_image_alt(original, projected)["findings"]


def _table_case() -> tuple:
    original = [{"source_id": "ast:blocks/0", "rows": [{"cells": [{"source_id": "raw-cell"}]}]}]
    filtered = [{"source_id": "ast:blocks/3", "rows": [{"cells": [{"source_id": "cell-a"}, {"source_id": "cell-b"}]}]}]
    native = [{"source_id": "ast:blocks/3", "cells": [{"source_id": "cell-a"}, {"source_id": "cell-b"}]}]
    return (
        "ast:blocks/0",
        [{"kind": "Table", "ast_path": ["blocks", 3]}],
        original,
        filtered,
        native,
        [{"source_id": "ast:blocks/0", "digest": "allocation"}],
        [{"source_digest": "allocation"}],
    )


def test_table_endpoint_uses_filtered_identity_and_retains_original_complete_roster() -> None:
    result = _table_native_projection(*_table_case())
    assert result is not None
    assert result["original_table"]["source_id"] == "ast:blocks/0"
    assert result["table"]["source_id"] == "ast:blocks/3"
    assert result["filtered_ast_path"] == ["blocks", 3]
    assert [cell["source_id"] for cell in result["table"]["cells"]] == ["cell-a", "cell-b"]


@pytest.mark.parametrize("defect", ["raw-path", "missing-cell", "reordered-cells", "repeated-table", "allocation"])
def test_table_projection_cannot_borrow_raw_path_or_partial_native_cells(defect: str) -> None:
    case = _table_case()
    if defect == "raw-path":
        case[1][0]["ast_path"] = ["blocks", 0]
    elif defect == "missing-cell":
        case[4][0]["cells"].pop()
    elif defect == "reordered-cells":
        case[4][0]["cells"].reverse()
    elif defect == "repeated-table":
        case[4].append(case[4][0])
    else:
        case[6][0]["source_digest"] = "other-allocation"
    assert _table_native_projection(*case) is None
