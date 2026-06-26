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


def test_from_dict_rejects_negative_gutter() -> None:
    """gutter_inches < 0 is rejected."""
    with pytest.raises(ValueError, match="gutter_inches"):
        NewspaperConfig(gutter_inches=-0.1)


def test_from_dict_rejects_empty_output_basename() -> None:
    """An empty output_basename string is rejected."""
    with pytest.raises(ValueError, match="output_basename"):
        NewspaperConfig(output_basename="")


def test_from_dict_render_non_dict_raises() -> None:
    """A non-dict 'render' section is rejected."""
    with pytest.raises(ValueError, match="mapping"):
        NewspaperConfig.from_dict({"render": "just a string"})


def test_all_page_sizes_build_geometry() -> None:
    for size in ("tabloid", "broadsheet", "berliner", "letter"):
        cfg = NewspaperConfig.from_dict({"render": {"page": size}})
        geom = cfg.geometry()
        assert geom.width > 0 and geom.height > 0


def test_spot_disabled_returns_none() -> None:
    assert NewspaperConfig(spot_color=False).spot() is None


def test_spot_enabled_with_valid_hex_returns_color() -> None:
    spot = NewspaperConfig(spot_color=True, spot_hex="#9E1B32").spot()
    assert spot is not None


def test_spot_enabled_with_invalid_hex_returns_none() -> None:
    """An unparseable hex string falls back to None gracefully (no crash)."""
    spot = NewspaperConfig(spot_color=True, spot_hex="not-a-hex-color").spot()
    assert spot is None


def test_load_from_real_content(content_dir) -> None:
    cfg = load_newspaper_config(content_dir)
    assert cfg.output_basename == "the-triplicate"
    assert cfg.page == "tabloid"


def test_load_newspaper_config_missing_file_raises(tmp_path) -> None:
    """FileNotFoundError when no edition.yaml is present."""
    with pytest.raises(FileNotFoundError):
        load_newspaper_config(tmp_path)


def test_load_newspaper_config_non_dict_raises(tmp_path) -> None:
    """A YAML file that is not a mapping is rejected."""
    (tmp_path / "edition.yaml").write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_newspaper_config(tmp_path)
