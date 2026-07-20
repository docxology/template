"""Tests for the content model and YAML loaders."""

from __future__ import annotations

import pytest
import yaml

from newspaper.content import (
    Ad,
    Block,
    Box,
    Edition,
    Figure,
    Page,
    Story,
    _parse_ad,
    _parse_block,
    _parse_box,
    _parse_body,
    _parse_figure,
    _parse_item,
    _parse_page,
    _parse_story,
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
    with pytest.raises(ValueError, match="page number"):
        Page(number=0)


def test_edition_rejects_duplicate_page_numbers() -> None:
    with pytest.raises(ValueError, match="duplicate page number"):
        Edition(
            nameplate="T",
            city="C",
            state="S",
            date="D",
            pages=[Page(number=1), Page(number=1)],
        )


def test_edition_page_count() -> None:
    """Edition.page_count reflects the length of pages list."""
    ed = Edition(nameplate="T", city="C", state="S", date="D")
    assert ed.page_count == 0
    ed.pages.append(Page(number=1))
    assert ed.page_count == 1


# ---------------------------------------------------------------------------
# _parse_block edge cases
# ---------------------------------------------------------------------------


def test_parse_block_pull_as_string() -> None:
    """A pull block whose value is a plain string (not a mapping) must work."""
    blk = _parse_block({"pull": "A memorable line."})
    assert blk.kind == "pull"
    assert blk.text == "A memorable line."
    assert blk.attribution == ""


def test_parse_block_p_key_mapping() -> None:
    """A mapping with a 'p' key is parsed as a paragraph block."""
    blk = _parse_block({"p": "Some text"})
    assert blk.kind == "p"
    assert blk.text == "Some text"


def test_parse_block_unknown_mapping_raises() -> None:
    """A dict with no recognised key raises ValueError."""
    with pytest.raises(ValueError):
        _parse_block({"unknown_key": "something"})


def test_parse_block_non_str_non_dict_raises() -> None:
    """A body block that is neither a string nor a mapping raises ValueError.

    This covers the 194->206 branch in content._parse_block where isinstance(raw, dict)
    is False (input is e.g. an integer or list passed as a raw block value).
    """
    with pytest.raises(ValueError, match="cannot parse body block"):
        _parse_block(42)  # integer is neither str nor dict


def test_parse_story_requires_mapping_and_headline() -> None:
    with pytest.raises(ValueError, match="story must be a mapping"):
        _parse_story("not-a-story")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="story requires a 'headline'"):
        _parse_story({})


def test_parse_box_requires_mapping_and_discriminator() -> None:
    with pytest.raises(ValueError, match="box item must be a mapping"):
        _parse_box("not-a-box")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="box requires a 'box'"):
        _parse_box({})
    with pytest.raises(ValueError, match="'items' must be a list"):
        _parse_box({"box": "generic", "items": "not-a-list"})
    with pytest.raises(ValueError, match="'columns' must be a list"):
        _parse_box({"box": "table", "columns": "not-a-list"})


# ---------------------------------------------------------------------------
# _parse_body edge cases
# ---------------------------------------------------------------------------


def test_parse_body_none_returns_empty() -> None:
    assert _parse_body(None) == []


def test_parse_body_non_list_raises() -> None:
    with pytest.raises(ValueError, match="must be a list"):
        _parse_body("not a list")


# ---------------------------------------------------------------------------
# _parse_figure edge cases
# ---------------------------------------------------------------------------


def test_parse_figure_none_returns_none() -> None:
    assert _parse_figure(None) is None


def test_parse_figure_non_dict_raises() -> None:
    with pytest.raises(ValueError, match="mapping"):
        _parse_figure("just a string")


def test_parse_figure_missing_path_raises() -> None:
    with pytest.raises(ValueError, match="path"):
        _parse_figure({"caption": "no path here"})


def test_parse_figure_bad_height_raises() -> None:
    with pytest.raises(ValueError, match="height"):
        _parse_figure({"path": "x.png", "height": "not_a_number"})


# ---------------------------------------------------------------------------
# _parse_ad edge cases
# ---------------------------------------------------------------------------


def test_parse_ad_non_dict_raises() -> None:
    with pytest.raises(ValueError, match="mapping"):
        _parse_ad("not a dict")


def test_parse_ad_bad_height_raises() -> None:
    with pytest.raises(ValueError, match="numbers"):
        _parse_ad({"sponsor": "Acme", "height": "tall"})


def test_parse_ad_defaults() -> None:
    """_parse_ad fills in all optional fields with sensible defaults."""
    ad = _parse_ad({"sponsor": "Acme Co."})
    assert ad.sponsor == "Acme Co."
    assert ad.border == "box"
    assert ad.height == pytest.approx(0.0)
    assert ad.graphic_height == pytest.approx(70.0)
    assert ad.body == []


# ---------------------------------------------------------------------------
# _parse_item dispatch
# ---------------------------------------------------------------------------


def test_parse_item_dispatch() -> None:
    assert isinstance(_parse_item({"headline": "H", "body": ["a"]}), Story)
    assert isinstance(_parse_item({"box": "index", "items": ["x"]}), Box)
    assert isinstance(_parse_item({"figure": {"path": "p.png"}}), Figure)
    with pytest.raises(ValueError):
        _parse_item({"mystery": 1})
    with pytest.raises(ValueError, match="page item must be a mapping"):
        _parse_item("not-an-item")  # type: ignore[arg-type]


def test_parse_item_dispatches_ad_with_all_fields() -> None:
    item = _parse_item(
        {
            "ad": {
                "sponsor": "Harbor Inn",
                "tagline": "Rest easy",
                "body": ["Great rates"],
                "contact": "555-1234",
                "border": "thick",
            }
        }
    )
    assert isinstance(item, Ad)
    assert item.sponsor == "Harbor Inn"
    assert item.tagline == "Rest easy"
    assert item.border == "thick"


# ---------------------------------------------------------------------------
# _parse_page edge cases
# ---------------------------------------------------------------------------


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


def test_parse_page_missing_number_raises() -> None:
    with pytest.raises(ValueError, match="number"):
        _parse_page({"template": "standard", "main": []})


def test_parse_page_requires_mapping() -> None:
    with pytest.raises(ValueError, match="page must be a mapping"):
        _parse_page("not-a-page")  # type: ignore[arg-type]


def test_parse_page_non_integer_number_raises() -> None:
    with pytest.raises(ValueError):
        _parse_page({"number": "one", "main": []})


def test_rail_rejects_figures() -> None:
    with pytest.raises(ValueError):
        _parse_page({"number": 1, "rail": [{"figure": {"path": "x.png"}}], "main": []})


def test_parse_page_rail_enabled_key() -> None:
    """rail_enabled: true sets page.rail without needing a rail list."""
    page = _parse_page({"number": 2, "rail_enabled": True, "main": []})
    assert page.rail is True
    assert page.rail_items == []


def test_parse_page_rejects_non_list_content_sections() -> None:
    with pytest.raises(ValueError, match="'rail' must be a list"):
        _parse_page({"number": 1, "rail": "not-a-list", "main": []})
    with pytest.raises(ValueError, match="'main' must be a list"):
        _parse_page({"number": 1, "main": "not-a-list"})
    with pytest.raises(ValueError, match="'lead' must be a mapping"):
        _parse_page({"number": 1, "lead": "not-a-story", "main": []})


def test_parse_box_rejects_non_list_table_fields() -> None:
    with pytest.raises(ValueError, match="'rows' must be a list"):
        _parse_item({"box": "table", "rows": "not-a-list"})
    with pytest.raises(ValueError, match="row 0 must be a list"):
        _parse_item({"box": "table", "rows": ["not-a-row"]})


# ---------------------------------------------------------------------------
# load_edition edge cases
# ---------------------------------------------------------------------------


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


def test_load_edition_non_dict_manifest_raises(tmp_path) -> None:
    """A YAML file that is a scalar at the top level is rejected."""
    (tmp_path / "edition.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_edition(tmp_path)


def test_load_edition_missing_masthead_fields_raises(tmp_path) -> None:
    """Missing required masthead fields are reported by name."""
    (tmp_path / "edition.yaml").write_text(
        yaml.dump({"masthead": {"nameplate": "X"}, "pages": ["p1.yaml"]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="city"):
        load_edition(tmp_path)


def test_load_edition_empty_pages_list_raises(tmp_path) -> None:
    """An empty 'pages' list is rejected by the loader."""
    manifest = {"masthead": {"nameplate": "X", "city": "Y", "state": "Z", "date": "D"}, "pages": []}
    (tmp_path / "edition.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty"):
        load_edition(tmp_path)


def test_load_edition_missing_page_file_raises(tmp_path) -> None:
    """A page filename that doesn't exist on disk raises FileNotFoundError."""
    manifest = {
        "masthead": {"nameplate": "X", "city": "Y", "state": "Z", "date": "D"},
        "pages": ["ghost.yaml"],
    }
    (tmp_path / "edition.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="ghost.yaml"):
        load_edition(tmp_path)


def test_load_edition_rejects_page_path_escape(tmp_path) -> None:
    """Manifest entries cannot read page YAML outside content/pages/."""
    manifest = {
        "masthead": {"nameplate": "X", "city": "Y", "state": "Z", "date": "D"},
        "pages": ["../outside.yaml"],
    }
    (tmp_path / "edition.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
    (tmp_path / "outside.yaml").write_text("number: 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="inside the content/pages directory"):
        load_edition(tmp_path)


def test_load_edition_rejects_non_string_page_reference(tmp_path) -> None:
    manifest = {
        "masthead": {"nameplate": "X", "city": "Y", "state": "Z", "date": "D"},
        "pages": [1],
    }
    (tmp_path / "edition.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="page filenames must be non-empty strings"):
        load_edition(tmp_path)


def test_load_edition_rejects_duplicate_manifest_page_file(tmp_path) -> None:
    manifest = {
        "masthead": {"nameplate": "X", "city": "Y", "state": "Z", "date": "D"},
        "pages": ["p1.yaml", "./p1.yaml"],
    }
    (tmp_path / "edition.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    (pages_dir / "p1.yaml").write_text("number: 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate page file"):
        load_edition(tmp_path)


def test_load_edition_rejects_duplicate_page_number(tmp_path) -> None:
    manifest = {
        "masthead": {"nameplate": "X", "city": "Y", "state": "Z", "date": "D"},
        "pages": ["p1.yaml", "p2.yaml"],
    }
    (tmp_path / "edition.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    (pages_dir / "p1.yaml").write_text("number: 1\n", encoding="utf-8")
    (pages_dir / "p2.yaml").write_text("number: 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate page number"):
        load_edition(tmp_path)


def test_load_edition_non_dict_page_raises(tmp_path) -> None:
    """A page YAML file that resolves to a non-dict is rejected."""
    manifest = {
        "masthead": {"nameplate": "X", "city": "Y", "state": "Z", "date": "D"},
        "pages": ["p1.yaml"],
    }
    (tmp_path / "edition.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    (pages_dir / "p1.yaml").write_text("- not\n- a\n- dict\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_edition(tmp_path)
