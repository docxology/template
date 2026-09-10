"""Slides table excerpt geometry, colspan minimums, and table cell pricing (split from test_slides_accessibility.py)."""

from __future__ import annotations

from typing import Any
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    compose_accessible_pandoc_document,
)
from infrastructure.rendering._slides_accessibility_tables import _table_column_minima
from infrastructure.rendering._slides_accessibility_contracts import proportional_text_width_units
from ._slides_accessibility_helpers import (
    _header,
    _paragraph,
    _hard_line_paragraph,
    _citation,
    _document,
    _visible_text,
    _row,
    _table,
    _table_values,
    _spanning_cell,
    _block_cell,
)


def test_semantic_composer_excerpts_table_without_mutating_source() -> None:
    table = _table(10)
    source = _document([_header("Exact values"), table])

    composition = compose_accessible_pandoc_document(
        source,
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered_table = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert composition.excerpted_table_count == 1
    # The configured eight-row value remains an absolute ceiling. Projection
    # geometry retains five compact rows after the header, row struts, and
    # complete longtable rule chrome are accounted for at 20 points. The
    # persistent frame navigation owns the canonical-reader link, so no
    # duplicate table caption consumes a row.
    assert len(rendered_table["c"][4][0][3]) == 5
    assert len(rendered_table["c"][4][0][3]) <= AccessibleSlidePolicy().max_table_rows
    assert rendered_table["c"][1] == [None, []]
    assert len(table["c"][4][0][3]) == 10
    assert all(colspec[1]["t"] == "ColWidth" for colspec in rendered_table["c"][2])
    assert all(colspec[1]["t"] == "ColWidthDefault" for colspec in table["c"][2])


def test_semantic_composer_removes_complete_table_footer_from_projection_excerpt() -> None:
    table = _table(10)
    table["c"][5][1] = [_row("Total 10")]

    composition = compose_accessible_pandoc_document(
        _document([_header("Excerpted total"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered_table = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert composition.excerpted_table_count == 1
    assert len(rendered_table["c"][4][0][3]) < 10
    assert rendered_table["c"][5][1] == []
    source_footer = " ".join(_visible_text(table["c"][5]).split())
    assert "Total" in source_footer and "10" in source_footer


def test_table_excerpt_recomputes_geometry_after_dropping_a_long_footer() -> None:
    table = _table(10)
    footer = _row("complete-source total")
    footer[1][0][4] = [_hard_line_paragraph(7)]
    table["c"][5][1] = [footer]

    composition = compose_accessible_pandoc_document(
        _document([_header("Excerpted long footer"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered_table = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert composition.excerpted_table_count == 1
    assert len(rendered_table["c"][4][0][3]) == 5
    assert rendered_table["c"][5][1] == []
    assert len(table["c"][5][1]) == 1


def test_uniform_pandoc_table_widths_are_redistributed_by_visible_demand() -> None:
    table = _table_values(
        ["ID", "Interpretation"],
        [["A", "A substantially longer source-owned explanation"], ["B", "A second explanation"]],
    )
    table["c"][2] = [
        [{"t": "AlignDefault"}, {"t": "ColWidth", "c": 0.5}],
        [{"t": "AlignDefault"}, {"t": "ColWidth", "c": 0.5}],
    ]

    composition = compose_accessible_pandoc_document(
        _document([_header("Exact values"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    widths = [float(colspec[1]["c"]) for colspec in rendered["c"][2]]
    assert widths[1] > widths[0]
    assert sum(widths) == pytest.approx(1.0)


def test_genuinely_unequal_authored_table_widths_are_preserved() -> None:
    table = _table_values(["ID", "Interpretation"], [["A", "Explanation"]])
    table["c"][2] = [
        [{"t": "AlignDefault"}, {"t": "ColWidth", "c": 0.25}],
        [{"t": "AlignDefault"}, {"t": "ColWidth", "c": 0.75}],
    ]

    composition = compose_accessible_pandoc_document(
        _document([_header("Exact values"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    widths = [float(colspec[1]["c"]) for colspec in rendered["c"][2]]
    assert widths == pytest.approx([0.25, 0.75])


def test_table_widths_reject_an_indivisible_code_token_that_cannot_fit() -> None:
    long_code = "canonical_parameter_identifier_that_must_remain_contiguous"
    table = _table_values(
        ["Symbol", "Meaning", "Code term"],
        [["y_t", "Observation/outcome rank-biserial-derived index", long_code]],
    )
    code_inline = {"t": "Code", "c": [["", [], []], long_code]}
    table["c"][4][0][3][0][1][2][4][0]["c"] = [code_inline]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Notation mapping"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/notation.md",
        )

    assert exc_info.value.context["first_offending_token"] == long_code
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]


def test_overlapping_colspans_share_their_common_column_minimum() -> None:
    wide_token = "W" * 18
    table = {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(3)],
            [
                ["", [], []],
                [
                    [
                        ["", [], []],
                        [
                            _spanning_cell(wide_token, column_span=2),
                            _spanning_cell("x"),
                        ],
                    ]
                ],
            ],
            [
                [
                    ["", [], []],
                    0,
                    [],
                    [
                        [
                            ["", [], []],
                            [
                                _spanning_cell("x"),
                                _spanning_cell(wide_token, column_span=2),
                            ],
                        ]
                    ],
                ]
            ],
            [["", [], []], []],
        ],
    }

    minima, _tokens = _table_column_minima(table["c"], 3)

    # Each W span requires 36 calibrated width units. The one-unit internal
    # gutter means the column minima must contribute at least 35. A local
    # greedy split would over-allocate; the exact interval solver shares the
    # middle column and finds the feasible 37-unit allocation [2, 33, 2].
    assert minima == [2, 33, 2]
    assert sum(minima[:2]) + 1 >= 36
    assert sum(minima[1:]) + 1 >= 36
    assert sum(minima) <= 41


@pytest.mark.parametrize("token_length", [41, 42])
def test_infeasible_colspan_diagnostic_preserves_active_span_provenance(token_length: int) -> None:
    token = "a" * token_length
    table = {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(3)],
            [
                ["", [], []],
                [
                    [
                        ["", [], []],
                        [_spanning_cell("A"), _spanning_cell("B"), _spanning_cell("C")],
                    ]
                ],
            ],
            [
                [
                    ["", [], []],
                    0,
                    [],
                    [
                        [
                            ["", [], []],
                            [_spanning_cell(token, column_span=2), _spanning_cell("x")],
                        ]
                    ],
                ]
            ],
            [["", [], []], []],
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Spanning boundary"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/spanning.md",
        )

    context = exc_info.value.context
    assert context["column_minimum_width_units"] == [2, token_length - 3, 2]
    assert context["first_offending_token"] == token
    assert context["first_offending_column_index"] == 1
    assert context["offending_span_start_column_index"] == 1
    assert context["offending_span_end_column_index"] == 2
    assert context["offending_span_required_width_units"] == token_length - 1


def test_individually_impossible_column_outranks_unrelated_span_diagnostic() -> None:
    def span_row(cells: list[list[Any]]) -> list[Any]:
        return [["", [], []], cells]

    table = {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(3)],
            [["", [], []], [span_row([_spanning_cell("A"), _spanning_cell("B"), _spanning_cell("C")])]],
            [
                [
                    ["", [], []],
                    0,
                    [],
                    [span_row([_spanning_cell("W" * 8, column_span=2), _spanning_cell("W" * 23)])],
                ]
            ],
            [["", [], []], []],
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Mixed width failure"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/table.md",
        )

    context = exc_info.value.context
    assert context["column_minimum_width_units"] == [2, 13, 45]
    assert context["first_offending_column_index"] == 3
    assert context["first_offending_token"] == "W" * 23
    assert context["first_offending_column_minimum_width_units"] == 45
    assert context["offending_span_start_column_index"] is None
    assert context["offending_span_end_column_index"] is None
    assert context["offending_span_required_width_units"] is None


def test_table_code_block_prices_each_physical_line_as_indivisible_monospace() -> None:
    code_line = "aaaaa-" * 8
    table = _table_values(["Code"], [["placeholder"]])
    table["c"][4][0][3][0][1][0] = _block_cell([{"t": "CodeBlock", "c": [["", [], []], code_line]}])

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Verbatim boundary"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/verbatim.md",
        )

    assert exc_info.value.context["first_offending_token"] == code_line
    assert exc_info.value.context["required_width_units"] > 43


@pytest.mark.parametrize(
    ("command", "passing_count", "failing_count"),
    [(r"\sum", 14, 16), (r"\rightarrow", 19, 20)],
)
def test_table_math_controls_use_calibrated_visible_width(
    command: str,
    passing_count: int,
    failing_count: int,
) -> None:
    passing_source = command * passing_count
    passing_table = _table_values(["Expression"], [["placeholder"]])
    passing_table["c"][4][0][3][0][1][0][4][0]["c"] = [{"t": "Math", "c": [{"t": "InlineMath"}, passing_source]}]
    composition = compose_accessible_pandoc_document(
        _document([_header("Math boundary pass"), passing_table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/math.md",
    )
    assert composition.frame_count == 1

    math_source = command * failing_count
    table = _table_values(["Expression"], [["placeholder"]])
    table["c"][4][0][3][0][1][0][4][0]["c"] = [{"t": "Math", "c": [{"t": "InlineMath"}, math_source]}]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Math boundary"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/math.md",
        )

    assert exc_info.value.context["first_offending_token"] == math_source
    assert exc_info.value.context["required_width_units"] > 43


def test_table_list_geometry_prices_indent_and_item_line_structure() -> None:
    horizontal = _table_values(["Item"], [["placeholder"]])
    horizontal["c"][4][0][3][0][1][0] = _block_cell([{"t": "BulletList", "c": [[_paragraph("a" * 42)]]}])
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as width_error:
        compose_accessible_pandoc_document(
            _document([_header("List width"), horizontal]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/list.md",
        )
    assert width_error.value.context["first_offending_token"] == "a" * 42

    vertical = _table_values(["Items"], [["placeholder"]])
    vertical["c"][4][0][3][0][1][0] = _block_cell(
        [{"t": "BulletList", "c": [[_paragraph(f"item-{index}")] for index in range(8)]}]
    )
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as height_error:
        compose_accessible_pandoc_document(
            _document([_header("List height"), vertical]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/list.md",
        )
    assert height_error.value.context["first_row_lines"] == 8


def test_table_cell_geometry_counts_authored_hard_lines() -> None:
    def table_with_lines(line_count: int) -> dict[str, Any]:
        table = _table_values(["Evidence"], [["placeholder"]])
        table["c"][4][0][3][0][1][0] = _block_cell([_hard_line_paragraph(line_count)])
        return table

    composition = compose_accessible_pandoc_document(
        _document([_header("Table hard lines"), table_with_lines(5)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/table-lines.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Table hard lines"), table_with_lines(6)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/table-lines.md",
        )
    assert exc_info.value.context["first_row_lines"] == 6


def test_unmodeled_rich_table_cell_block_fails_with_stable_diagnostic() -> None:
    table = _table_values(["Claim"], [["placeholder"]])
    table["c"][4][0][3][0][1][0] = _block_cell([{"t": "BlockQuote", "c": [_paragraph("bounded evidence")]}])

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-table-cell-block\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Rich cell"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/rich.md",
        )

    assert exc_info.value.context["block_type"] == "BlockQuote"


@pytest.mark.parametrize(
    ("glyph", "passing_count", "failing_count"),
    [("A", 30, 31), ("m", 26, 27), ("w", 30, 31), ("W", 22, 23)],
)
def test_proportional_glyph_classes_match_one_column_preflight_boundary(
    glyph: str,
    passing_count: int,
    failing_count: int,
) -> None:
    passing_token = glyph * passing_count
    failing_token = glyph * failing_count
    passing_table = _table_values(["Field"], [[passing_token]])
    failing_table = _table_values(["Field"], [[failing_token]])

    composition = compose_accessible_pandoc_document(
        _document([_header("Glyph boundary pass"), passing_table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/glyph-boundary.md",
    )
    assert composition.frame_count == 1
    assert proportional_text_width_units(passing_token) <= 43
    assert proportional_text_width_units(failing_token) > 43

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Glyph boundary fail"), failing_table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/glyph-boundary.md",
        )

    context = exc_info.value.context
    assert context["column_count"] == 1
    assert context["available_width_units"] == 43
    assert context["required_width_units"] > context["available_width_units"]
    assert context["first_offending_token"] == failing_token


def test_resolved_citeproc_family_name_sets_table_token_minimum() -> None:
    long_family = "A" * 32
    table = _table_values(["Source"], [["placeholder"]])
    table["c"][4][0][3][0][1][0][4][0]["c"] = [_citation("longfamily2026", rendered_text=f"({long_family} 2026)")]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Resolved citation table"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert long_family in exc_info.value.context["first_offending_token"]
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]


def test_irreducible_eight_column_gallery_fails_before_latex_with_width_context() -> None:
    table = _table_values(
        [
            "Mechanism",
            "Evidence class",
            "Naive score",
            "Selected mean",
            "Mean difference",
            "Confidence interval",
            "Win fraction",
            "Display flag",
        ],
        [["byzantine", "directional", "0.6306", "0.6599", "0.0293", "[0.0124, 0.0462]", "0.84", "shown"]],
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Contamination gallery"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/extended-methods.md",
        )

    context = exc_info.value.context
    assert context["diagnostic_code"] == "slides.density.indivisible-table-width"
    assert context["column_count"] == 8
    assert context["body_font_pt"] == 20
    assert context["required_width_units"] > context["available_width_units"]
    assert len(context["column_minimum_width_units"]) == 8
    assert 1 <= context["first_offending_column_index"] <= 8
    assert context["first_offending_token"] != ""
    assert context["intercolumn_gutter_width_units"] == 7


def test_table_excerpt_geometry_accounts_for_cell_wrapping() -> None:
    table = _table_values(
        ["Metric", "Value"],
        [
            ["first", "short"],
            ["A source-owned explanatory cell " * 8, "long"],
            ["third", "short"],
        ],
    )

    composition = compose_accessible_pandoc_document(
        _document([_header("Exact values"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert len(rendered["c"][4][0][3]) == 1
    assert composition.excerpted_table_count == 1


def test_table_excerpt_geometry_accounts_for_continuation_title_lines() -> None:
    table = _table(10)
    composition = compose_accessible_pandoc_document(
        _document(
            [
                _header(
                    "A deliberately long table heading that preserves its full wording on a divider before projection"
                ),
                table,
            ]
        ),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert composition.section_divider_count == 1
    assert len(rendered["c"][4][0][3]) == 5


def test_table_excerpt_reserves_real_longtable_rule_and_row_strut_geometry() -> None:
    compact = _table(6)
    compact_composition = compose_accessible_pandoc_document(
        _document([_header("Computational complexity"), compact]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/statistics.md",
    )
    compact_rendered = next(block for block in compact_composition.document["blocks"] if block["t"] == "Table")
    assert len(compact_rendered["c"][4][0][3]) == 5
    assert compact_composition.excerpted_table_count == 1

    wrapped = _table_values(
        ["Study", "Key parameters"],
        [
            ["1 — Belief sharing", "n_agents = 7; acuity = 0.55"],
            ["2 — Language acquisition", "num_steps = 24"],
            ["3 — Emergence / BMR", "candidate states n = 4"],
        ],
    )
    wrapped_composition = compose_accessible_pandoc_document(
        _document([_header("Study suite and contamination sweep"), wrapped]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/design.md",
    )
    wrapped_rendered = next(block for block in wrapped_composition.document["blocks"] if block["t"] == "Table")
    assert len(wrapped_rendered["c"][4][0][3]) == 2
    assert wrapped_composition.excerpted_table_count == 1


def test_table_excerpt_fails_closed_when_no_whole_row_fits() -> None:
    table = _table_values(
        ["Metric", "Condition"],
        [
            [
                "alpha beta gamma delta " * 24,
                "nested condition remains source bounded " * 24,
            ]
        ],
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Paired contrasts"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    context = exc_info.value.context
    assert context["source"] == "manuscript/results.md"
    assert context["heading"] == "Paired contrasts"
    assert context["diagnostic_code"] == "slides.density.indivisible-table"
    assert context["column_count"] == 2
    assert context["body_row_count"] == 1
    assert context["available_lines"] == 8
    assert context["fixed_lines"] == 2
    assert context["title_font_pt"] == 28
    assert context["body_font_pt"] == 20
    assert context["maximum_body_rows"] == 8
    assert context["global_header_lines"] >= 1
    assert context["footer_lines"] == 0
    assert context["first_body_header_lines"] == 0
    assert context["first_row_lines"] > context["available_lines"]
    assert len(context["resolved_widths"]) == 2
    assert len(context["column_character_capacities"]) == 2


def test_row_span_uses_physical_columns_and_cannot_be_fragmented_by_excerpt() -> None:
    table = {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(2)],
            [["", [], []], [[["", [], []], [_spanning_cell("ID"), _spanning_cell("Interpretation")]]]],
            [
                [
                    ["", [], []],
                    0,
                    [],
                    [
                        [["", [], []], [_spanning_cell("A", row_span=2), _spanning_cell("short")]],
                        [
                            ["", [], []],
                            [_spanning_cell("A source-owned explanatory value requiring the second physical column")],
                        ],
                    ],
                ]
            ],
            [["", [], []], []],
        ],
    }

    composition = compose_accessible_pandoc_document(
        _document([_header("Spanning values"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    widths = [float(colspec[1]["c"]) for colspec in rendered["c"][2]]
    assert widths[1] > widths[0]
    assert len(rendered["c"][4][0][3]) == 2

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Spanning values"), table]),
            policy=AccessibleSlidePolicy(max_table_rows=1),
            source="manuscript/results.md",
        )
    assert exc_info.value.context["row_span_excerpt_blocked"] is True


def test_header_only_table_body_fails_closed_instead_of_disappearing() -> None:
    table = _table(0)
    table["c"][4][0][2] = [_row("subheader")]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.header-only-table-body\]"):
        compose_accessible_pandoc_document(
            _document([_header("Header-only body"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_malformed_table_body_still_raises_renderer_error() -> None:
    table = _table(1)
    table["c"][4] = [[]]

    with pytest.raises(RenderingError, match="malformed Pandoc Table body"):
        compose_accessible_pandoc_document(
            _document([_header("Malformed body"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_captioned_listing_keeps_source_caption_but_projects_counter_only() -> None:
    caption = "A complete source-owned listing caption that consumes projected vertical geometry"
    code = "\n".join(f"x_{index} = {index}" for index in range(5))
    listing = {
        "t": "CodeBlock",
        "c": [["lst:test", ["python"], [["caption", caption]]], code],
    }
    document = _document([_header("Listing"), listing])

    composition = compose_accessible_pandoc_document(
        document,
        policy=AccessibleSlidePolicy(),
        source="manuscript/listing.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "CodeBlock")
    assert document["blocks"][1]["c"][0][2] == [["caption", caption]]
    assert rendered["c"][0][0] == "lst:test"
    assert rendered["c"][0][2] == [["caption", ""]]
    assert rendered["c"][1] == code

    overheight = {
        "t": "CodeBlock",
        "c": [
            ["lst:test", ["python"], [["caption", caption]]],
            "\n".join(f"x_{index} = {index}" for index in range(7)),
        ],
    }
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Listing"), overheight]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/listing.md",
        )
    assert exc_info.value.context["projected_caption_lines"] == 1
    assert exc_info.value.context["estimated_lines"] == 8


def test_shell_code_reflows_only_at_whitespace_and_never_inside_tokens() -> None:
    fitting = {"t": "CodeBlock", "c": [["", ["bash"], []], "W" * 33 + "'"]}
    fitting_composition = compose_accessible_pandoc_document(
        _document([_header("Fitting shell token"), fitting]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/shell.md",
    )
    assert any(block.get("t") == "CodeBlock" for block in fitting_composition.document["blocks"])

    reflowable = {"t": "CodeBlock", "c": [["", ["bash"], []], "W" * 20 + " " + "W" * 20]}
    reflowed_composition = compose_accessible_pandoc_document(
        _document([_header("Whitespace-reflowable shell command"), reflowable]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/shell.md",
    )
    reflowed = next(block for block in reflowed_composition.document["blocks"] if block.get("t") == "Para")
    assert reflowed["c"][0]["t"] == "Code"

    for unsafe_token in ("W" * 35, "W" * 34 + "'", "W" * 34 + "{"):
        unsafe = {"t": "CodeBlock", "c": [["", ["bash"], []], unsafe_token]}
        with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code-line\]") as exc_info:
            compose_accessible_pandoc_document(
                _document([_header("Unsafe shell token"), unsafe]),
                policy=AccessibleSlidePolicy(),
                source="manuscript/shell.md",
            )
        assert exc_info.value.context["first_offending_token"] == unsafe_token
        assert exc_info.value.context["maximum_characters"] == 34
