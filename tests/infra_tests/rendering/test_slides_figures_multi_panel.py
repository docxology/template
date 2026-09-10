"""Slides figure isolation and multi-panel figure geometry (split from test_slides_accessibility.py)."""

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
    _inlines,
    _header,
    _paragraph,
    _document,
    _visible_text,
    _classed_headers,
    _image,
    _linked_image,
)


def test_semantic_composer_isolates_figures_equations_code_and_evidence() -> None:
    image = {
        "t": "Image",
        "c": [["", [], []], _inlines("Trend lines"), ["trend.png", ""]],
    }
    figure = {
        "t": "Figure",
        "c": [["fig:trend", [], []], [None, [_paragraph("A detailed caption")]], [{"t": "Plain", "c": [image]}]],
    }
    equation = {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, "x = y"]}]}
    code = {"t": "CodeBlock", "c": [["", ["python"], []], "result = aggregate(request)"]}
    evidence = {"t": "BlockQuote", "c": [_paragraph("Bounded evidence statement")]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Reading order"), figure, equation, code, evidence]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/methods.md",
    )

    classes = [classes for _title, classes in _classed_headers(composition.document)]
    assert classes == [
        {"figure-led"},
        {"equation-led"},
        {"code-led"},
        {"evidence-slide"},
    ]
    assert composition.figure_frame_count == 1
    assert "A detailed caption" not in " ".join(_visible_text(composition.document).split())
    rendered_figure = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    assert rendered_figure["c"][1] == [None, []]
    rendered_image = rendered_figure["c"][2][0]["c"][0]
    assert ["width", "98%"] in rendered_image["c"][0][2]
    assert ["height", "80%"] in rendered_image["c"][0][2]
    assert ["data-slide-figure-min-allocation-percent", "70"] in rendered_image["c"][0][2]


def test_semantic_composer_drops_page_break_and_keeps_crossref_suffixed_equation_atomic() -> None:
    page_break = {"t": "RawBlock", "c": ["tex", "\\newpage"]}
    equation = {
        "t": "Para",
        "c": [
            {"t": "Math", "c": [{"t": "DisplayMath"}, "x = y"]},
            {"t": "Space"},
            {"t": "Str", "c": "{#eq:identity}"},
        ],
    }

    composition = compose_accessible_pandoc_document(
        _document([_header("Equation"), page_break, equation]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/formalism.md",
    )

    assert composition.frame_count == 1
    assert all(block != page_break for block in composition.document["blocks"])
    assert _classed_headers(composition.document)[0][1] == {"equation-led"}


def test_long_title_figure_allocation_uses_title_adjusted_body_geometry() -> None:
    image = {"t": "Image", "c": [["", [], []], _inlines("Trend"), ["trend.png", ""]]}
    figure = {
        "t": "Figure",
        "c": [["fig:trend", [], []], [None, []], [{"t": "Plain", "c": [image]}]],
    }
    authored_title = (
        "A deliberately wide evidence heading that wraps across multiple projection lines for careful reading"
    )
    composition = compose_accessible_pandoc_document(
        _document(
            [
                _header(authored_title),
                figure,
            ]
        ),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    assert composition.section_divider_count == 1
    headers = _classed_headers(composition.document)
    assert "section-divider" in headers[0][1]
    assert "part 2" in headers[1][0]
    continuation_headers = [block for block in composition.document["blocks"] if block["t"] == "Header"]
    continuation_header = continuation_headers[1]["c"]
    assert continuation_header[2]
    visible_title = " ".join(_visible_text(continuation_header[2]).split())
    assert proportional_text_width_units(visible_title) <= 35
    assert any(
        pair
        == [
            "aria-label",
            f"{authored_title}, part 2",
        ]
        for pair in continuation_header[1][2]
    )
    rendered_figure = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    rendered_image = rendered_figure["c"][2][0]["c"][0]
    # The compact continuation title fits one projected title line while the
    # complete authored heading remains its accessible name.
    assert ["width", "98%"] in rendered_image["c"][0][2]
    assert ["height", "80%"] in rendered_image["c"][0][2]
    assert ["data-slide-figure-min-allocation-percent", "70"] in rendered_image["c"][0][2]


@pytest.mark.parametrize("authored_title", ["W" * 22, "unbreakable_identifier_" + "x" * 64])
def test_unbreakable_title_fails_before_divider_or_content_render(authored_title: str) -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-title-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header(authored_title), _paragraph("Bounded content.")]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["first_offending_token"] == authored_title
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]


def test_multi_panel_figure_preserves_one_bounded_authored_row() -> None:
    left = _image("left.png", width="45%", alt="Left panel")
    right = _image("right.png", width="45%", alt="Right panel")
    figure = {
        "t": "Figure",
        "c": [
            ["fig:panels", [], []],
            [None, [_paragraph("Complete caption")]],
            [{"t": "Plain", "c": [left, {"t": "Space"}, right]}],
        ],
    }

    composition = compose_accessible_pandoc_document(
        _document([_header("Panel comparison"), figure]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    images = [item for item in rendered["c"][2][0]["c"] if item.get("t") == "Image"]
    assert len(images) == 2
    assert [[pair for pair in image["c"][0][2] if pair[0] == "width"] for image in images] == [
        [["width", "45%"]],
        [["width", "45%"]],
    ]
    assert all(["height", "80%"] in image["c"][0][2] for image in images)
    assert all(["data-slide-figure-min-allocation-percent", "70"] in image["c"][0][2] for image in images)
    assert all("accessible-multi-image-panel" in image["c"][0][1] for image in images)


def test_multi_panel_figure_rejects_hard_line_break_pseudo_rows() -> None:
    figure = {
        "t": "Figure",
        "c": [
            ["fig:panels", [], []],
            [None, []],
            [
                {
                    "t": "Plain",
                    "c": [
                        _image("left.png", width="45%", alt="Left"),
                        {"t": "LineBreak"},
                        _image("right.png", width="45%", alt="Right"),
                    ],
                }
            ],
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.multi-image-layout\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Panel comparison"), figure]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert "pseudo-rows" in str(exc_info.value)


def test_multi_panel_figure_requires_declared_minimum_usable_width() -> None:
    figure = {
        "t": "Figure",
        "c": [
            ["fig:panels", [], []],
            [None, []],
            [
                {
                    "t": "Plain",
                    "c": [
                        _image("left.png", width="30%", alt="Left"),
                        {"t": "Space"},
                        _image("right.png", width="30%", alt="Right"),
                    ],
                }
            ],
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.figure-area\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Panel comparison"), figure]),
            policy=AccessibleSlidePolicy(min_figure_area_percent=70),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["authored_total_width_percent"] == 60
    assert exc_info.value.context["minimum_total_width_percent"] == 70


@pytest.mark.parametrize(
    "body",
    [
        [
            {"t": "Plain", "c": [_image("left.png", width="45%", alt="Left")]},
            {"t": "Plain", "c": [_image("right.png", width="45%", alt="Right")]},
        ],
        [
            {
                "t": "Plain",
                "c": [
                    _image("left.png", width="55%", alt="Left"),
                    {"t": "Space"},
                    _image("right.png", width="55%", alt="Right"),
                ],
            }
        ],
    ],
)
def test_multi_panel_figure_fails_closed_on_unbounded_layout(body: list[dict[str, Any]]) -> None:
    figure = {"t": "Figure", "c": [["fig:panels", [], []], [None, []], body]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.multi-image-layout\]"):
        compose_accessible_pandoc_document(
            _document([_header("Panel comparison"), figure]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_single_image_figure_rejects_peer_prose_but_accepts_image_only_body() -> None:
    valid = {
        "t": "Figure",
        "c": [
            ["fig:single", [], []],
            [None, [_paragraph("Complete caption")]],
            [{"t": "Plain", "c": [_image("single.png", alt="Single panel")]}],
        ],
    }
    composition = compose_accessible_pandoc_document(
        _document([_header("Single panel"), valid]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    assert ["width", "98%"] in rendered["c"][2][0]["c"][0]["c"][0][2]

    invalid = {
        "t": "Figure",
        "c": [
            ["fig:mixed", [], []],
            [None, []],
            [
                {"t": "Plain", "c": [_image("single.png", alt="Single panel")]},
                _paragraph("Peer prose that must not bypass density accounting."),
            ],
        ],
    }
    with pytest.raises(RenderingError, match=r"\[slides\.density\.mixed-image-frame\]"):
        compose_accessible_pandoc_document(
            _document([_header("Mixed single panel"), invalid]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_image_only_paragraph_receives_allocation_and_mixed_image_prose_fails_closed() -> None:
    image_paragraph = {"t": "Para", "c": [_image("trend.png", alt="Trend")]}
    composition = compose_accessible_pandoc_document(
        _document([_header("Image"), image_paragraph]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Para")
    assert ["width", "98%"] in rendered["c"][0]["c"][0][2]
    assert ["height", "80%"] in rendered["c"][0]["c"][0][2]
    assert ["data-slide-figure-min-allocation-percent", "70"] in rendered["c"][0]["c"][0][2]

    mixed = {"t": "Para", "c": [_image("trend.png"), {"t": "Space"}, *_inlines("Peer prose")]}
    with pytest.raises(RenderingError, match=r"\[slides\.density\.mixed-image-frame\]"):
        compose_accessible_pandoc_document(
            _document([_header("Mixed"), mixed]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_linked_and_classed_image_wrappers_preserve_targets_and_allocation() -> None:
    linked = _linked_image("thumb.png", "full.png")
    composition = compose_accessible_pandoc_document(
        _document([_header("Linked image"), {"t": "Para", "c": [linked]}]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered_link = next(block for block in composition.document["blocks"] if block["t"] == "Para")["c"][0]
    assert rendered_link["c"][2] == ["full.png", "Open full-size figure"]
    assert ["width", "98%"] in rendered_link["c"][1][0]["c"][0][2]
    assert ["height", "80%"] in rendered_link["c"][1][0]["c"][0][2]
    assert ["data-slide-figure-min-allocation-percent", "70"] in rendered_link["c"][1][0]["c"][0][2]

    row = {
        "t": "Plain",
        "c": [
            _linked_image("left.png", "left-full.png", width="45%"),
            {"t": "Space"},
            _linked_image("right.png", "right-full.png", width="45%"),
        ],
    }
    figure = {"t": "Figure", "c": [["fig:links", [], []], [None, []], [row]]}
    composition = compose_accessible_pandoc_document(
        _document([_header("Linked panels"), figure]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    links = [item for item in rendered["c"][2][0]["c"] if item.get("t") == "Link"]
    assert [link["c"][2][0] for link in links] == ["left-full.png", "right-full.png"]

    wrapped = {
        "t": "Div",
        "c": [
            ["", ["figure-wrapper"], []],
            [{"t": "Para", "c": [{"t": "Span", "c": [["", ["panel"], []], [_image("panel.png")]]}]}],
        ],
    }
    wrapped_composition = compose_accessible_pandoc_document(
        _document([_header("Wrapped image"), wrapped]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    assert wrapped_composition.figure_frame_count == 1
    wrapped_div = next(block for block in wrapped_composition.document["blocks"] if block["t"] == "Div")
    wrapped_image = wrapped_div["c"][1][0]["c"][0]["c"][1][0]
    assert ["width", "98%"] in wrapped_image["c"][0][2]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.mixed-image-frame\]"):
        compose_accessible_pandoc_document(
            _document(
                [
                    _header("Linked prose"),
                    {"t": "Para", "c": [_linked_image("thumb.png", "full.png", sibling_text="details")]},
                ]
            ),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )
