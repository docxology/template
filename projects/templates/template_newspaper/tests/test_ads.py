"""Tests for the display-ad system, color graphics, and spot color."""

from __future__ import annotations

from dataclasses import replace

import pytest

from newspaper.config import NewspaperConfig
from newspaper.content import Ad, Block, Edition, Page, _parse_ad, _parse_item
from newspaper.engine import render_edition


def test_ad_requires_sponsor() -> None:
    with pytest.raises(ValueError):
        Ad(sponsor="")
    with pytest.raises(ValueError) as exc:
        _parse_ad({"tagline": "no sponsor"})
    assert "sponsor" in str(exc.value)


def test_ad_validates_border() -> None:
    with pytest.raises(ValueError):
        Ad(sponsor="X", border="neon")


def test_parse_item_dispatches_ad() -> None:
    item = _parse_item({"ad": {"sponsor": "Foglight Bakery", "border": "double",
                               "background": "#F8EFD9", "accent": "#6E3C18",
                               "body": ["Fresh loaves"], "contact": "555-0210"}})
    assert isinstance(item, Ad)
    assert item.sponsor == "Foglight Bakery"
    assert item.border == "double"
    assert item.body[0].text == "Fresh loaves"


def _ad_page(border: str) -> Edition:
    ad = Ad(sponsor="Test Co", tagline="We sell things", border=border,
            background="#EAF1F5", accent="#1F3A5F", body=[Block("p", "Open daily.")],
            contact="555-0000")
    page = Page(number=1, template="standard", columns=4, main_items=[ad])
    return Edition(nameplate="T", city="C", state="S", date="D", pages=[page])


def test_ad_renders_for_each_border(tmp_path) -> None:
    for border in ("box", "double", "thick", "none"):
        out = tmp_path / f"{border}.pdf"
        result = render_edition(_ad_page(border), NewspaperConfig(), project_root=tmp_path, output_path=out)
        assert result.page_count == 1
        assert result.all_pages_fit
        assert out.read_bytes().startswith(b"%PDF-")


def test_spot_color_config() -> None:
    assert NewspaperConfig(spot_color=False).spot() is None
    spot = NewspaperConfig(spot_color=True, spot_hex="#1F6F8B").spot()
    assert spot is not None


def test_spot_color_changes_output(project_root, tmp_path) -> None:
    """Enabling spot color must actually change the rendered bytes."""
    from newspaper.config import load_newspaper_config
    from newspaper.content import load_edition

    edition = load_edition(project_root / "content")
    base = load_newspaper_config(project_root / "content")
    mono = tmp_path / "mono.pdf"
    color = tmp_path / "color.pdf"
    render_edition(edition, replace(base, spot_color=False), project_root=project_root, output_path=mono)
    render_edition(edition, replace(base, spot_color=True, spot_hex="#1F6F8B"),
                   project_root=project_root, output_path=color)
    assert mono.read_bytes() != color.read_bytes()
