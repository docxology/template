"""Tests for the content model and YAML loaders."""

from __future__ import annotations

import pytest

from newspaper.content import (
    Block,
    Box,
    Figure,
    Page,
    Story,
    _parse_item,
    _parse_page,
    load_edition,
)


def test_block_validates_kind() -> None:
    with pytest.raises(ValueError):
        Block(kind="banana")


def test_story_validates_level() -> None:
    with pytest.raises(ValueError):
        Story(headline="x", level="enormous")


def test_box_validates_kind() -> None:
    with pytest.raises(ValueError):
        Box(kind="not-a-box")


def test_page_validates_template_and_columns() -> None:
    with pytest.raises(ValueError):
        Page(number=1, template="origami")
    with pytest.raises(ValueError):
        Page(number=1, columns=0)


def test_parse_item_dispatch() -> None:
    assert isinstance(_parse_item({"headline": "H", "body": ["a"]}), Story)
    assert isinstance(_parse_item({"box": "index", "items": ["x"]}), Box)
    assert isinstance(_parse_item({"figure": {"path": "p.png"}}), Figure)
    with pytest.raises(ValueError):
        _parse_item({"mystery": 1})


def test_parse_page_promotes_lead_level() -> None:
    page = _parse_page(
        {
            "number": 3,
            "template": "standard",
            "columns": 5,
            "lead": {"headline": "Big", "body": ["one", {"subhead": "S"}, {"pull": {"quote": "q", "by": "me"}}]},
            "main": [{"box": "briefs", "title": "T", "body": ["x"]}],
        }
    )
    assert page.lead is not None
    assert page.lead.level == "lead"
    assert page.lead.body[1].kind == "subhead"
    assert page.lead.body[2].kind == "pull"
    assert page.lead.body[2].attribution == "me"


def test_rail_rejects_figures() -> None:
    with pytest.raises(ValueError):
        _parse_page(
            {"number": 1, "rail": [{"figure": {"path": "x.png"}}], "main": []}
        )


def test_load_real_edition_has_twelve_pages(edition) -> None:
    assert edition.nameplate == "The Triplicate"
    assert edition.page_count == 12
    # Page numbers are 1..12 and unique.
    nums = [p.number for p in edition.pages]
    assert nums == list(range(1, 13))
    # The front page is a 'front' template with a rail and a lead story.
    front = edition.pages[0]
    assert front.template == "front"
    assert front.rail is True
    assert front.lead is not None and front.lead.level == "lead"


def test_missing_manifest_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        load_edition(tmp_path)
