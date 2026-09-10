"""Shared helpers for the split slides-accessibility test modules (formerly test_slides_accessibility.py)."""

from __future__ import annotations
import base64
from pathlib import Path
from typing import Any


def _inlines(text: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, word in enumerate(text.split()):
        if index:
            result.append({"t": "Space"})
        result.append({"t": "Str", "c": word})
    return result


def _header(text: str, *, level: int = 2, classes: list[str] | None = None) -> dict[str, Any]:
    return {"t": "Header", "c": [level, [text.lower().replace(" ", "-"), classes or [], []], _inlines(text)]}


def _paragraph(text: str) -> dict[str, Any]:
    return {"t": "Para", "c": _inlines(text)}


def _hard_line_paragraph(line_count: int) -> dict[str, Any]:
    inlines: list[dict[str, Any]] = []
    for index in range(line_count):
        if index:
            inlines.append({"t": "LineBreak"})
        inlines.append({"t": "Str", "c": "x"})
    return {"t": "Para", "c": inlines}


def _nested_fraction_source(depth: int) -> str:
    source = "1"
    for _ in range(depth):
        source = rf"\frac{{1}}{{{source}}}"
    return source


def _citation(
    identifier: str,
    *,
    prefix: str = "",
    rendered_text: str | None = None,
    suffix: str = "",
) -> dict[str, Any]:
    return {
        "t": "Cite",
        "c": [
            [
                {
                    "citationId": identifier,
                    "citationPrefix": _inlines(prefix),
                    "citationSuffix": _inlines(suffix),
                    "citationMode": {"t": "NormalCitation"},
                    "citationNoteNum": 0,
                    "citationHash": 0,
                }
            ],
            _inlines(rendered_text) if rendered_text is not None else [{"t": "Str", "c": f"[@{identifier}]"}],
        ],
    }


def _paragraph_with_citations(text: str, identifiers: list[str]) -> dict[str, Any]:
    inlines = _inlines(text)
    citations = {f"REF{index}": _citation(identifier) for index, identifier in enumerate(identifiers)}
    return {
        "t": "Para",
        "c": [citations.get(str(inline.get("c")), inline) for inline in inlines],
    }


def _document(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    return {"pandoc-api-version": [1, 23, 1, 2], "meta": {}, "blocks": blocks}


def _visible_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(part for item in value if (part := _visible_text(item)))
    if not isinstance(value, dict):
        return ""
    if value.get("t") in {"Space", "SoftBreak", "LineBreak"}:
        return " "
    return _visible_text(value["c"] if "c" in value else list(value.values()))


def _cell(value: str) -> list[Any]:
    return [["", [], []], {"t": "AlignDefault"}, 1, 1, [{"t": "Plain", "c": _inlines(value)}]]


def _row(value: str) -> list[Any]:
    return [["", [], []], [_cell(value), _cell("value")]]


def _row_values(values: list[str]) -> list[Any]:
    return [["", [], []], [_cell(value) for value in values]]


def _table(rows: int) -> dict[str, Any]:
    return {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(2)],
            [["", [], []], [_row("key")]],
            [[["", [], []], 0, [], [_row(str(index)) for index in range(rows)]]],
            [["", [], []], []],
        ],
    }


def _table_values(headers: list[str], rows: list[list[str]]) -> dict[str, Any]:
    assert all(len(row) == len(headers) for row in rows)
    return {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in headers],
            [["", [], []], [_row_values(headers)]],
            [[["", [], []], 0, [], [_row_values(row) for row in rows]]],
            [["", [], []], []],
        ],
    }


def _classed_headers(document: dict[str, Any]) -> list[tuple[str, set[str]]]:
    result: list[tuple[str, set[str]]] = []
    for block in document["blocks"]:
        if block["t"] != "Header":
            continue
        text = " ".join(item.get("c", "") for item in block["c"][2] if item["t"] == "Str")
        result.append((text, set(block["c"][1][1])))
    return result


def _write_png(path: Path) -> None:
    # Valid one-pixel RGB PNG; avoids a Pillow dependency in the renderer test.
    path.write_bytes(
        base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
    )


def _image(path: str, *, width: str | None = None, alt: str = "Panel") -> dict[str, Any]:
    attributes: list[list[str]] = [] if width is None else [["width", width]]
    return {
        "t": "Image",
        "c": [["", [], attributes], _inlines(alt), [path, ""]],
    }


def _linked_image(
    thumbnail: str,
    full_size: str,
    *,
    width: str | None = None,
    sibling_text: str | None = None,
) -> dict[str, Any]:
    inlines: list[dict[str, Any]] = [_image(thumbnail, width=width)]
    if sibling_text is not None:
        inlines.extend([{"t": "Space"}, *_inlines(sibling_text)])
    return {
        "t": "Link",
        "c": [["", ["figure-full-size-link"], []], inlines, [full_size, "Open full-size figure"]],
    }


def _spanning_cell(value: str, *, row_span: int = 1, column_span: int = 1) -> list[Any]:
    return [
        ["", [], []],
        {"t": "AlignDefault"},
        row_span,
        column_span,
        [{"t": "Plain", "c": _inlines(value)}],
    ]


def _block_cell(
    blocks: list[dict[str, Any]],
    *,
    row_span: int = 1,
    column_span: int = 1,
) -> list[Any]:
    return [
        ["", [], []],
        {"t": "AlignDefault"},
        row_span,
        column_span,
        blocks,
    ]
