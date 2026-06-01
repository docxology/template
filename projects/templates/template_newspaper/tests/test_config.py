"""Tests for the strict newspaper render configuration."""

from __future__ import annotations

import pytest

from newspaper.config import NewspaperConfig, load_newspaper_config


def test_defaults_are_tabloid() -> None:
    cfg = NewspaperConfig()
    geom = cfg.geometry()
    assert cfg.page == "tabloid"
    assert geom.width < geom.height  # portrait
    assert cfg.gutter_points == pytest.approx(cfg.gutter_inches * 72)
    assert cfg.rail_points == pytest.approx(cfg.rail_inches * 72)


def test_from_dict_rejects_unknown_render_key() -> None:
    with pytest.raises(ValueError) as exc:
        NewspaperConfig.from_dict({"render": {"bogus_key": 1}})
    assert "bogus_key" in str(exc.value)
    assert "Allowed" in str(exc.value)


def test_from_dict_rejects_bad_values() -> None:
    with pytest.raises(ValueError):
        NewspaperConfig.from_dict({"render": {"page": "scroll"}})
    with pytest.raises(ValueError):
        NewspaperConfig.from_dict({"render": {"columns_default": 0}})
    with pytest.raises(ValueError):
        NewspaperConfig.from_dict({"render": {"rail_inches": 0}})


def test_all_page_sizes_build_geometry() -> None:
    for size in ("tabloid", "broadsheet", "berliner", "letter"):
        cfg = NewspaperConfig.from_dict({"render": {"page": size}})
        geom = cfg.geometry()
        assert geom.width > 0 and geom.height > 0


def test_load_from_real_content(content_dir) -> None:
    cfg = load_newspaper_config(content_dir)
    assert cfg.output_basename == "the-triplicate"
    assert cfg.page == "tabloid"
