"""Real rendering must not overwrite unrelated files through temporary links."""

from pathlib import Path
import shutil

import pytest

from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer


@pytest.mark.slow
@pytest.mark.requires_latex
def test_beamer_rewrite_does_not_follow_predictable_temporary_symlink(tmp_path: Path) -> None:
    if not shutil.which("pandoc") or not shutil.which("xelatex"):
        pytest.skip("Pandoc and XeLaTeX required for real Beamer rendering")
    source = tmp_path / "deck.md"
    source.write_text("## Evidence\n\nKeep unrelated files intact.\n", encoding="utf-8")
    slides = tmp_path / "slides"
    slides.mkdir()
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("preserve me", encoding="utf-8")
    planted = slides / "deck_slides.tex.tmp"
    planted.symlink_to(unrelated)
    renderer = SlidesRenderer(RenderingConfig(slides_dir=str(slides), slide_theme="default"))

    result = renderer.render(source)

    assert result.is_file()
    assert unrelated.read_text(encoding="utf-8") == "preserve me"
    assert planted.is_symlink()
    assert not result.with_suffix(".tex").is_symlink()
