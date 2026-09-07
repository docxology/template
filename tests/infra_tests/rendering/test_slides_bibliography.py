"""Bibliography resolution tests for ``SlidesRenderer``.

Verifies that both slide writers receive a deterministic sorted union of
top-level bibliography files and that the real Pandoc paths (Beamer and
Reveal.js) resolve citations from every bibliography without emitting a
references section.

Follows the No Mocks Policy — tests invoke the real Pandoc pipeline via
``SlidesRenderer.render`` and inspect the resulting artifacts on disk.
"""

from __future__ import annotations

import shutil

import pytest
from pypdf import PdfReader

from infrastructure.rendering import slides_renderer
from infrastructure.rendering.slides_renderer import SlidesRenderer

from ._helpers import _multi_bibliography_slide_fixture, _require_beamer_toolchain


def test_slide_bibliography_args_use_sorted_union_and_suppress_references(tmp_path):
    """Both slide writers receive the same deterministic citation arguments."""
    _source, manuscript_dir = _multi_bibliography_slide_fixture(tmp_path)

    args = slides_renderer._slide_bibliography_args(manuscript_dir)

    expected_bibliographies = [
        f"--bibliography={manuscript_dir / 'references.bib'}",
        f"--bibliography={manuscript_dir / 'z_supplemental.bib'}",
    ]
    assert args == [
        "--citeproc",
        *expected_bibliographies,
        "--metadata",
        "suppress-bibliography=true",
    ]
    assert slides_renderer._slide_bibliography_args(None) == []


@pytest.mark.requires_latex
def test_beamer_resolves_citations_from_every_top_level_bibliography(test_config, tmp_path):
    """The real Beamer/Pandoc path resolves supplemental bibliography citations."""
    _require_beamer_toolchain()
    source, manuscript_dir = _multi_bibliography_slide_fixture(tmp_path)

    result = SlidesRenderer(test_config).render(
        source,
        output_format="beamer",
        manuscript_dir=manuscript_dir,
    )

    extracted = "\n".join(page.extract_text() or "" for page in PdfReader(str(result)).pages)
    assert "Alpha" in extracted
    assert "Omega" in extracted
    assert "alpha2020primary?" not in extracted
    assert "omega2021supplement?" not in extracted
    assert "Primary Source" not in extracted
    assert "Supplemental Source" not in extracted


def test_revealjs_resolves_citations_from_every_top_level_bibliography(test_config, tmp_path):
    """The real Reveal.js/Pandoc path resolves the same supplemental citations."""
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    source, manuscript_dir = _multi_bibliography_slide_fixture(tmp_path)

    result = SlidesRenderer(test_config).render(
        source,
        output_format="revealjs",
        manuscript_dir=manuscript_dir,
    )

    html = result.read_text(encoding="utf-8")
    assert "Alpha" in html
    assert "Omega" in html
    assert "[@alpha2020primary" not in html
    assert "@omega2021supplement]" not in html
    assert 'id="refs"' not in html
