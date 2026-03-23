"""Tests for ``newspaper.section_graphics``."""

import matplotlib.image as mpimg
import numpy as np

from newspaper.section_graphics import render_section_banner_bw, section_banner_filename
from newspaper.sections import section_banner_targets


def test_section_banner_filename() -> None:
    assert section_banner_filename("03_world") == "section_banner_03_world.png"


def test_section_banner_targets_count_and_excludes_front() -> None:
    targets = section_banner_targets()
    stems = {s for s, _ in targets}
    assert len(targets) == 19
    assert "01_front_page" not in stems
    assert "02_national" in stems
    assert "16_classifieds" in stems
    assert "S01_layout_and_pipeline" in stems
    assert "98_newspaper_and_pipeline_terms" in stems


def test_render_section_banner_writes_png(tmp_path) -> None:
    out = tmp_path / "section_banner_02_national.png"
    render_section_banner_bw(out, "02_national", "National", dpi=120)
    assert out.is_file()
    assert out.stat().st_size > 2_000


def test_render_section_banner_deterministic(tmp_path) -> None:
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    render_section_banner_bw(a, "06_sports", "Sports", dpi=100)
    render_section_banner_bw(b, "06_sports", "Sports", dpi=100)
    assert a.read_bytes() == b.read_bytes()


def test_different_stems_differ(tmp_path) -> None:
    a = tmp_path / "x.png"
    b = tmp_path / "y.png"
    render_section_banner_bw(a, "04_business", "Business", dpi=100)
    render_section_banner_bw(b, "05_technology", "Technology", dpi=100)
    assert a.read_bytes() != b.read_bytes()


def test_banner_grayscaleish(tmp_path) -> None:
    out = tmp_path / "g.png"
    render_section_banner_bw(out, "07_arts", "Arts & Culture", dpi=110)
    img = mpimg.imread(out)
    rgb = img[:, :, :3]
    assert float(np.max(np.abs(rgb[:, :, 0] - rgb[:, :, 1]))) < 0.08
    assert float(np.max(np.abs(rgb[:, :, 1] - rgb[:, :, 2]))) < 0.08
