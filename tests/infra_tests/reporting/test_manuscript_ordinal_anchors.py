"""Full-byte/tree DATA transform cases; actual native parser trials are separate."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

import pytest

from infrastructure.rendering.manuscript_hydration_replay import combine_held_manuscripts
from infrastructure.rendering.manuscript_ordinal_anchors import (
    annotate_manuscript_ordinals,
    require_complete_ordinal_ast_equivalence,
    require_unannotated_parser_bytes,
)


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _document(blocks: list[dict[str, Any]]) -> bytes:
    return json.dumps({"pandoc-api-version": [1, 23, 1], "meta": {}, "blocks": blocks}).encode()


def _str(text: str) -> dict[str, str]:
    return {"t": "Str", "c": text}


def _marker(text: str) -> dict[str, Any]:
    return {"t": "RawInline", "c": ["html", text]}


def _anchors() -> tuple[Any, ...]:
    _, anchors = annotate_manuscript_ordinals((b"12",), ((0, 1, "VALUE", 0, 2, _sha(b"12")),))
    return anchors


def test_equal_payloads_keep_distinct_authored_ordinals_and_byte_intervals() -> None:
    bodies = (b"left 12 right 12", b"12")
    annotations, anchors = annotate_manuscript_ordinals(
        bodies,
        ((0, 1, "VALUE", 5, 7, _sha(b"12")), (0, 2, "VALUE", 14, 16, _sha(b"12")), (1, 1, "VALUE", 0, 2, _sha(b"12"))),
    )
    combined = combine_held_manuscripts(annotations, separator="\n---\n\n")
    actual = combine_held_manuscripts(bodies, separator="\n---\n\n")
    boundaries = require_unannotated_parser_bytes(combined, actual, anchors)
    assert boundaries == ((5, 7), (14, 16), (len(actual) - 3, len(actual) - 1))
    assert len({anchor.start for anchor in anchors}) == 3


def test_actual_combine_newline_trimming_bom_and_unicode_preserve_ordinal_ownership() -> None:
    bodies = ("\ufeffFirst é 12\r\n\r\n ".encode(), b"Second\r\n")
    first = len("\ufeffFirst é ".encode())
    annotated, anchors = annotate_manuscript_ordinals(bodies, ((0, 1, "VALUE", first, first + 2, _sha(b"12")),))
    actual = combine_held_manuscripts(bodies, separator="")
    ranges = require_unannotated_parser_bytes(combine_held_manuscripts(annotated, separator=""), actual, anchors)
    assert actual == "First é 12\n\n\nSecond\n".encode()
    assert ranges == ((len("First é ".encode()), len("First é 12".encode())),)


@pytest.mark.parametrize("mutation", ["wrong-digest", "overlap", "utf8-split", "empty"])
def test_false_or_unrepresentable_source_intervals_refuse(mutation: str) -> None:
    body = "é12".encode()
    rows = [(0, 1, "VALUE", 2, 4, _sha(b"12"))]
    if mutation == "wrong-digest":
        rows[0] = (0, 1, "VALUE", 2, 4, _sha(b"21"))
    elif mutation == "overlap":
        rows.append((0, 2, "OTHER", 3, 4, _sha(b"2")))
    elif mutation == "utf8-split":
        rows[0] = (0, 1, "VALUE", 1, 2, _sha(body[1:2]))
    else:
        rows[0] = (0, 1, "VALUE", 2, 2, _sha(b""))
    with pytest.raises(ValueError):
        annotate_manuscript_ordinals((body,), tuple(rows))


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "changed-neighbour"])
def test_complete_processed_input_bytes_must_remain_exact(mutation: str) -> None:
    annotations, anchors = annotate_manuscript_ordinals((b"12",), ((0, 1, "VALUE", 0, 2, _sha(b"12")),))
    body = annotations[0]
    if mutation == "missing":
        body = body.replace(anchors[0].start.encode(), b"")
    elif mutation == "duplicate":
        body += anchors[0].start.encode()
    else:
        body += b"changed"
    with pytest.raises(ValueError):
        require_unannotated_parser_bytes(body, b"12", anchors)


def test_str_split_is_merged_only_across_actual_removed_anchor_boundaries() -> None:
    anchors = _anchors()
    anchor = anchors[0]
    actual = _document([{"t": "Para", "c": [_str("v12tail")]}])
    annotated = _document(
        [{"t": "Para", "c": [_str("v"), _marker(anchor.start), _str("12"), _marker(anchor.end), _str("tail")]}]
    )
    row = require_complete_ordinal_ast_equivalence(annotated, actual, anchors)[0]
    assert row["start"] == {"ast_path": ["blocks", 0, "c", 0, "c"], "offset": 1, "kind": "literal-codepoint"}
    assert row["end"] == {"ast_path": ["blocks", 0, "c", 0, "c"], "offset": 3, "kind": "literal-codepoint"}


@pytest.mark.parametrize("tag", ["Math", "Code", "CodeBlock"])
def test_literal_math_and_code_anchors_keep_whole_source_node_identity(tag: str) -> None:
    anchors = _anchors()
    anchor = anchors[0]
    attribute: Any = {"t": "InlineMath"} if tag == "Math" else ["", [], []]
    node = {"t": tag, "c": [attribute, "x=12"]}
    marked = copy.deepcopy(node)
    marked["c"][1] = "x=" + anchor.start + "12" + anchor.end
    actual = _document([node] if tag == "CodeBlock" else [{"t": "Para", "c": [node]}])
    annotated = _document([marked] if tag == "CodeBlock" else [{"t": "Para", "c": [marked]}])
    row = require_complete_ordinal_ast_equivalence(annotated, actual, anchors)[0]
    path = ["blocks", 0, "c", 1] if tag == "CodeBlock" else ["blocks", 0, "c", 0, "c", 1]
    assert row["start"]["ast_path"] == path == row["end"]["ast_path"]
    assert (row["start"]["offset"], row["end"]["offset"]) == (2, 4)


def test_unknown_neighbours_are_compared_whole_and_never_borrowed_from_original() -> None:
    anchors = _anchors()
    anchor = anchors[0]
    unknown = {"t": "FutureSourceNode", "c": {"scientific": ["complete", "actual", "meaning"]}}
    actual = _document([{"t": "Para", "c": [_str("12")]}, unknown])
    annotated = _document([{"t": "Para", "c": [_marker(anchor.start), _str("12"), _marker(anchor.end)]}, unknown])
    assert require_complete_ordinal_ast_equivalence(annotated, actual, anchors)[0]["ordinal"] == 1
    changed = json.loads(annotated)
    changed["blocks"][1]["c"]["scientific"][2] = "altered"
    with pytest.raises(ValueError, match="complete original AST"):
        require_complete_ordinal_ast_equivalence(json.dumps(changed).encode(), actual, anchors)


@pytest.mark.parametrize("field", ["meta", "pandoc-api-version", "block-order", "text", "attribute"])
def test_every_non_anchor_field_and_order_is_preserved(field: str) -> None:
    anchors = _anchors()
    anchor = anchors[0]
    actual_tree = json.loads(_document([{"t": "Para", "c": [_str("12")]}, {"t": "HorizontalRule"}]))
    changed = copy.deepcopy(actual_tree)
    changed["blocks"][0]["c"] = [_marker(anchor.start), _str("12"), _marker(anchor.end)]
    if field == "meta":
        changed["meta"] = {"title": {"t": "MetaString", "c": "altered"}}
    elif field == "pandoc-api-version":
        changed[field] = [1, 24]
    elif field == "block-order":
        changed["blocks"].reverse()
    elif field == "text":
        changed["blocks"][0]["c"][1] = _str("21")
    else:
        changed["blocks"][0]["attributes"] = ["altered"]
    with pytest.raises(ValueError, match="complete original AST"):
        require_complete_ordinal_ast_equivalence(
            json.dumps(changed).encode(), json.dumps(actual_tree).encode(), anchors
        )


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unmarked-str-merge", "attribute-anchor"])
def test_missing_duplicate_or_unmodeled_anchor_structure_refuses(mutation: str) -> None:
    anchors = _anchors()
    anchor = anchors[0]
    actual = _document([{"t": "Para", "c": [_str("12")]}])
    nodes = [_marker(anchor.start), _str("12"), _marker(anchor.end)]
    if mutation == "missing":
        nodes.pop()
    elif mutation == "duplicate":
        nodes.append(_marker(anchor.end))
    elif mutation == "unmarked-str-merge":
        nodes[1:2] = [_str("1"), _str("2")]
    else:
        nodes[0] = {"t": "Span", "c": [[anchor.start, [], []], []]}
    with pytest.raises(ValueError):
        require_complete_ordinal_ast_equivalence(_document([{"t": "Para", "c": nodes}]), actual, anchors)


def test_duplicate_json_field_is_not_admitted_by_last_value() -> None:
    anchors = _anchors()
    with pytest.raises(ValueError, match="repeats a field"):
        require_complete_ordinal_ast_equivalence(
            b'{"pandoc-api-version":[1,23,1],"meta":{},"blocks":[],"blocks":[]}',
            _document([]),
            anchors,
        )


def test_anchor_node_unknown_fields_cannot_disappear_during_desugaring() -> None:
    anchors = _anchors()
    anchor = anchors[0]
    marker = {**_marker(anchor.start), "scientific": "changed"}
    with pytest.raises(ValueError, match="unmodeled actual AST field"):
        require_complete_ordinal_ast_equivalence(
            _document([{"t": "Para", "c": [marker, _str("12"), _marker(anchor.end)]}]),
            _document([{"t": "Para", "c": [_str("12")]}]),
            anchors,
        )


def test_multiline_selected_replacement_retains_complete_ordered_block_boundaries() -> None:
    anchors = _anchors()
    anchor = anchors[0]
    blocks = [
        {"t": "BulletList", "c": [[{"t": "Plain", "c": [_str("1")]}], [{"t": "Plain", "c": [_str("2")]}]]},
        {"t": "Table", "c": [["", [], []], [None, []], [], [[], []], [], [[], []]]},
    ]
    marker_start = {"t": "RawBlock", "c": ["html", anchor.start]}
    marker_end = {"t": "RawBlock", "c": ["html", anchor.end]}
    row = require_complete_ordinal_ast_equivalence(
        _document([marker_start, *blocks, marker_end]), _document(blocks), anchors
    )[0]
    assert row["start"] == {"ast_path": ["blocks"], "offset": 0, "kind": "ordered-list-boundary"}
    assert row["end"] == {"ast_path": ["blocks"], "offset": 2, "kind": "ordered-list-boundary"}


def test_caption_math_literal_ownership_retains_exact_nested_image_ast_path() -> None:
    anchors = _anchors()
    anchor = anchors[0]
    math = {"t": "Math", "c": [{"t": "InlineMath"}, "x=12"]}
    image = {"t": "Image", "c": [["figure", [], []], [math], ["../figures/actual.png", ""]]}
    original = _document([{"t": "Para", "c": [image]}])
    changed = copy.deepcopy(image)
    changed["c"][1][0]["c"][1] = "x=" + anchor.start + "12" + anchor.end
    row = require_complete_ordinal_ast_equivalence(_document([{"t": "Para", "c": [changed]}]), original, anchors)[0]
    assert row["start"]["ast_path"] == ["blocks", 0, "c", 0, "c", 1, 0, "c", 1]
    assert row["start"]["offset"] == 2
    assert row["end"]["offset"] == 4


@pytest.mark.parametrize("changed", [1, 1.0])
def test_complete_ast_comparison_preserves_exact_json_scalar_types(changed: int | float) -> None:
    anchors = _anchors()
    anchor = anchors[0]
    actual = json.loads(_document([{"t": "Para", "c": [_str("12")]}]))
    actual["meta"] = {"actual": {"t": "MetaBool", "c": True}}
    annotated = copy.deepcopy(actual)
    annotated["meta"]["actual"]["c"] = changed
    annotated["blocks"][0]["c"] = [_marker(anchor.start), _str("12"), _marker(anchor.end)]
    with pytest.raises(ValueError, match="complete original AST"):
        require_complete_ordinal_ast_equivalence(json.dumps(annotated).encode(), json.dumps(actual).encode(), anchors)


def _table_fixture() -> tuple[bytes, dict[str, object], int]:
    body = b"| Key | Count |\n| --- | --- |\n| Row | 12 |\n\n: Caption\n\n"

    # The complete six-field Pandoc Table shape, including column declarations,
    # row spans and cell blocks, is DATA. Real Pandoc trials are separate.
    def cell(text: str) -> list[object]:
        return [["", [], []], {"t": "AlignDefault"}, 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": text}]}]]

    table = {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, [{"t": "Plain", "c": [{"t": "Str", "c": "Caption"}]}]],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}]] * 2,
            [["", [], []], [[["", [], []], [cell("Key"), cell("Count")]]]],
            [[["", [], []], 0, [], [[["", [], []], [cell("Row"), cell("12")]]]]],
            [["", [], []], []],
        ],
    }
    return body, table, len(b"| Key | Count |\n| --- | --- |\n| Row | ")


def test_pipe_carrier_retains_payload_interval_and_complete_table_role() -> None:
    body, table, first = _table_fixture()
    marked, anchors = annotate_manuscript_ordinals((body,), ((0, 1, "COUNT", first, first + 2, _sha(b"12")),))
    assert require_unannotated_parser_bytes(marked[0], body, anchors) == ((first, first + 2),)
    start, end = anchors[0].start, anchors[0].end
    actual = _document([table])
    row = require_complete_ordinal_ast_equivalence(
        _document([{"t": "RawBlock", "c": ["html", start]}, table, {"t": "RawBlock", "c": ["html", end]}]),
        actual,
        anchors,
    )[0]
    assert row["boundary_kind"] == "containing-table"
    assert row["container_ast_path"] == ["blocks", 0]
    assert row["input_payload_byte_range"] == [first, first + 2]
    assert row["input_carrier_byte_range"] != row["input_payload_byte_range"]
    assert row["start"]["kind"] == row["end"]["kind"] == "containing-table-boundary"


def test_pipe_carrier_does_not_relax_inferred_column_widths() -> None:
    body, table, first = _table_fixture()
    _, anchors = annotate_manuscript_ordinals((body,), ((0, 1, "COUNT", first, first + 2, _sha(b"12")),))
    changed = json.loads(json.dumps(table))
    changed["c"][2][0][1] = {"t": "ColWidth", "c": 0.5}
    with pytest.raises(ValueError, match="complete original AST"):
        require_complete_ordinal_ast_equivalence(
            _document(
                [
                    {"t": "RawBlock", "c": ["html", anchors[0].start]},
                    changed,
                    {"t": "RawBlock", "c": ["html", anchors[0].end]},
                ]
            ),
            _document([table]),
            anchors,
        )


def test_pipe_carrier_cannot_promote_a_non_table_ast_role() -> None:
    body, _, first = _table_fixture()
    _, anchors = annotate_manuscript_ordinals((body,), ((0, 1, "COUNT", first, first + 2, _sha(b"12")),))
    other = {"t": "CodeBlock", "c": [["", [], []], body.decode()]}
    with pytest.raises(ValueError, match="genuine complete Table"):
        require_complete_ordinal_ast_equivalence(
            _document(
                [
                    {"t": "RawBlock", "c": ["html", anchors[0].start]},
                    other,
                    {"t": "RawBlock", "c": ["html", anchors[0].end]},
                ]
            ),
            _document([other]),
            anchors,
        )


def test_pipe_carrier_frame_change_refuses_even_when_marker_deletion_matches() -> None:
    body, _, first = _table_fixture()
    marked, anchors = annotate_manuscript_ordinals((body,), ((0, 1, "COUNT", first, first + 2, _sha(b"12")),))
    with pytest.raises(ValueError, match="table-carrier framing"):
        require_unannotated_parser_bytes(marked[0].replace(b"Row", b"Key"), body.replace(b"Row", b"Key"), anchors)


def test_complete_row_expansion_is_a_table_container_not_a_first_cell() -> None:
    body, table, _ = _table_fixture()
    first = len(b"| Key | Count |\n| --- | --- |\n")
    last = first + len(b"| Row | 12 |")
    payload = body[first:last]
    marked, anchors = annotate_manuscript_ordinals((body,), ((0, 1, "ROWS", first, last, _sha(payload)),))
    assert require_unannotated_parser_bytes(marked[0], body, anchors) == ((first, last),)
    row = require_complete_ordinal_ast_equivalence(
        _document(
            [
                {"t": "RawBlock", "c": ["html", anchors[0].start]},
                table,
                {"t": "RawBlock", "c": ["html", anchors[0].end]},
            ]
        ),
        _document([table]),
        anchors,
    )[0]
    assert row["container_ast_path"] == ["blocks", 0]
    assert row["start"]["ast_path"] == row["end"]["ast_path"] == ["blocks"]
    assert row["start"]["offset"] == 0 and row["end"]["offset"] == 1


def test_repeated_table_values_keep_distinct_intervals_with_shared_container() -> None:
    body, table, first = _table_fixture()
    addition = b"| Next | 12 |\n"
    body = body.replace(b"| Row | 12 |\n", b"| Row | 12 |\n" + addition)
    second = first + len(b"12 |\n| Next | ")
    copied = json.loads(json.dumps(table))
    copied["c"][4][0][3].append(json.loads(json.dumps(copied["c"][4][0][3][0])))
    copied["c"][4][0][3][1][1][0][4][0]["c"][0]["c"] = "Next"
    marked, anchors = annotate_manuscript_ordinals(
        (body,),
        ((0, 1, "COUNT", first, first + 2, _sha(b"12")), (0, 2, "COUNT", second, second + 2, _sha(b"12"))),
    )
    assert require_unannotated_parser_bytes(marked[0], body, anchors) == ((first, first + 2), (second, second + 2))
    rows = require_complete_ordinal_ast_equivalence(
        _document(
            [
                {"t": "RawBlock", "c": ["html", "\n".join(anchor.start for anchor in anchors)]},
                copied,
                {"t": "RawBlock", "c": ["html", "\n".join(anchor.end for anchor in anchors)]},
            ]
        ),
        _document([copied]),
        anchors,
    )
    assert rows[0]["container_ast_path"] == rows[1]["container_ast_path"] == ["blocks", 0]
    assert rows[0]["input_payload_byte_range"] != rows[1]["input_payload_byte_range"]


def _caption_alias_document(value: str, *, copied: str | None = None) -> bytes:
    caption = [{"t": "Math", "c": [{"t": "InlineMath"}, value]}]
    alternative = [{"t": "Math", "c": [{"t": "InlineMath"}, value if copied is None else copied]}]
    return _document(
        [
            {
                "t": "Figure",
                "c": [
                    ["fig:checked", [], []],
                    [None, [{"t": "Plain", "c": caption}]],
                    [{"t": "Plain", "c": [{"t": "Image", "c": [["", [], []], alternative, ["figure.png", ""]]}]}],
                ],
            }
        ]
    )


def test_actual_modern_caption_alias_retains_both_complete_source_sites() -> None:
    _, anchors = annotate_manuscript_ordinals((b"12",), ((0, 1, "VALUE", 0, 2, _sha(b"12")),))
    marked = anchors[0].start + "12" + anchors[0].end
    row = require_complete_ordinal_ast_equivalence(
        _caption_alias_document(marked), _caption_alias_document("12"), anchors
    )[0]
    assert row["start"]["ast_path"] == ["blocks", 0, "c", 1, 1, 0, "c", 0, "c", 1]
    assert row["caption_aliases"]["start"][0]["ast_path"] == ["blocks", 0, "c", 2, 0, "c", 0, "c", 1, 0, "c", 1]
    assert row["caption_aliases"]["start"][0]["offset"] == row["start"]["offset"]


def test_caption_alias_cannot_lose_the_alternative_anchor_site() -> None:
    _, anchors = annotate_manuscript_ordinals((b"12",), ((0, 1, "VALUE", 0, 2, _sha(b"12")),))
    marked = anchors[0].start + "12" + anchors[0].end
    with pytest.raises(ValueError, match="both exact complete"):
        require_complete_ordinal_ast_equivalence(
            _caption_alias_document(marked, copied="12"),
            _caption_alias_document("12"),
            anchors,
        )


def test_a_different_source_alternative_cannot_gain_caption_alias_authority() -> None:
    _, anchors = annotate_manuscript_ordinals((b"12",), ((0, 1, "VALUE", 0, 2, _sha(b"12")),))
    marked = anchors[0].start + "12" + anchors[0].end
    copied = anchors[0].start + "other" + anchors[0].end
    with pytest.raises(ValueError, match="nonalias ordinal"):
        require_complete_ordinal_ast_equivalence(
            _caption_alias_document(marked, copied=copied),
            _caption_alias_document("12", copied="other"),
            anchors,
        )
