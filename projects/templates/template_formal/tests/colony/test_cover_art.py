"""Behavioral tests for template_formal.colony.cover_art (thin-orchestrator
rule: real drawing logic lives in src/, so it needs real test coverage).
Real matplotlib, real PNG files on disk -- no mocking of the rendering
call, matching tests/colony/test_visualization.py's conventions."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from template_formal.colony.cover_art import COVER_ART_FILENAME, generate_cover_art, require_cover_art


def test_generate_cover_art_produces_a_real_nonempty_png(tmp_path: Path) -> None:
    output_path = tmp_path / "figures" / COVER_ART_FILENAME

    written = generate_cover_art(output_path, seed=42)

    assert written is not None
    assert written == output_path
    assert written.is_file()
    assert written.stat().st_size > 0
    with Image.open(written) as image:
        assert image.format == "PNG"
        assert image.width >= 100
        assert image.height >= 100
        colors = image.convert("RGBA").getcolors(maxcolors=4096)
        assert colors is None or len(colors) > 1


def test_generate_cover_art_output_is_a_valid_png(tmp_path: Path) -> None:
    output_path = tmp_path / "cover.png"

    written = generate_cover_art(output_path, seed=1)

    assert written is not None
    with written.open("rb") as handle:
        magic = handle.read(8)
    assert magic == b"\x89PNG\r\n\x1a\n"


def test_generate_cover_art_is_deterministic_in_composition_for_a_fixed_seed(tmp_path: Path) -> None:
    """Same seed -> same file size to the byte (matplotlib's Agg backend with
    no embedded timestamp metadata is byte-reproducible here), proving the
    seeded ``random.Random`` -- not the process-global ``random`` module --
    actually drives every stochastic choice (leg jitter, lattice-cell fill).
    Not claimed: reproducibility *across* matplotlib versions/platforms --
    only within one process/environment, which is what this test can
    actually observe (BLAS-style cross-platform float drift is a distinct,
    unrelated concern this test does not touch)."""
    first = generate_cover_art(tmp_path / "first.png", seed=7)
    second = generate_cover_art(tmp_path / "second.png", seed=7)

    assert first is not None
    assert second is not None
    assert first.read_bytes() == second.read_bytes()


def test_generate_cover_art_different_seeds_differ(tmp_path: Path) -> None:
    """Different seeds must actually change the rendered lattice-fill choices,
    not silently draw the identical image regardless of ``seed`` (a
    hardcoded-verdict-shaped defect this template's own gotcha history
    flags: a parameter that is accepted but never consumed)."""
    first = generate_cover_art(tmp_path / "a.png", seed=1)
    second = generate_cover_art(tmp_path / "b.png", seed=2)

    assert first is not None
    assert second is not None
    assert first.read_bytes() != second.read_bytes()


def test_generate_cover_art_creates_parent_directories(tmp_path: Path) -> None:
    output_path = tmp_path / "deeply" / "nested" / "figures" / COVER_ART_FILENAME

    written = generate_cover_art(output_path, seed=0)

    assert written is not None
    assert written.parent.is_dir()


def test_require_cover_art_fails_closed_for_unwritable_destination(tmp_path: Path) -> None:
    blocked_parent = tmp_path / "blocked"
    blocked_parent.write_text("not a directory", encoding="utf-8")

    with pytest.raises(RuntimeError, match="required cover art was not generated"):
        require_cover_art(blocked_parent / COVER_ART_FILENAME, seed=42)
