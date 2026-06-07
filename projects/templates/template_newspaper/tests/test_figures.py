"""Tests for figure generation (halftone scenes + charts)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from newspaper import figures


def test_scenes_return_images() -> None:
    builders = (
        figures.harbor_scene,
        figures.lighthouse_scene,
        figures.redwoods_scene,
        figures.lily_fields_scene,
        figures.baseball_scene,
        figures.crab_boat_scene,
    )
    for builder in builders:
        img = builder()
        assert isinstance(img, Image.Image)
        assert img.size[0] > 0 and img.size[1] > 0


def test_charts_write_png(tmp_path) -> None:
    for name, chart in (
        ("weather_7day.png", figures.weather_chart),
        ("tides.png", figures.tide_chart),
        ("crab_landings.png", figures.crab_landings_chart),
    ):
        out = chart(tmp_path / name)
        assert out.exists()
        assert out.stat().st_size > 0
        with Image.open(out) as im:
            assert im.format == "PNG"


def test_generate_all_writes_every_figure(tmp_path) -> None:
    paths = figures.generate_all(tmp_path)
    assert len(paths) == 13  # 6 halftone scenes + 4 color ad graphics + 3 charts
    for p in paths:
        assert p.exists() and p.stat().st_size > 0


def test_color_graphics_are_rgb(tmp_path) -> None:
    from PIL import Image as PILImage

    for builder in (
        figures.ad_bakery_logo,
        figures.ad_realty_logo,
        figures.ad_grocery_logo,
        figures.ad_festival_banner,
    ):
        img = builder()
        assert isinstance(img, PILImage.Image)
        assert img.mode == "RGB"


def test_claim_ledger_figure_count_matches_generator(tmp_path) -> None:
    """Bind data/claim_ledger.yaml `figure-count` to what generate_all actually
    produces — the ledger's own contract is that every number is traceable to its
    source, so it must not drift from the generator."""
    import yaml

    ledger_path = Path(__file__).resolve().parent.parent / "data" / "claim_ledger.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    claims = {c["claim_id"]: c["value"] for c in ledger["claims"]}
    assert claims["figure-count"] == len(figures.generate_all(tmp_path))
