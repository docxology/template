"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import WebRenderer

from ._web_renderer_test_helpers import _make_renderer


class TestAssetHandling:
    """Test asset handling."""

    def test_render_preserves_local_image_reference(self, tmp_path):
        """A markdown image remains addressable in the written HTML."""
        md = tmp_path / "doc.md"
        md.write_text("# Title\n\n![alt text](image.png)\n", encoding="utf-8")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        renderer = _make_renderer(tmp_path)
        html = renderer.render(md).read_text(encoding="utf-8")
        assert "image.png" in html
        assert "alt text" in html


def test_responsive_variant_uses_mobile_sibling_when_present(tmp_path: Path) -> None:
    web_dir = tmp_path / "output" / "web"
    figure_dir = tmp_path / "output" / "figures"
    web_dir.mkdir(parents=True)
    figure_dir.mkdir(parents=True)
    (figure_dir / "graphical.png").write_bytes(b"desktop")
    (figure_dir / "graphical_mobile.png").write_bytes(b"mobile")
    html_file = web_dir / "index.html"
    html_file.write_text(
        '<html><body><img src="../figures/graphical.png" alt="Graphical abstract"></body></html>',
        encoding="utf-8",
    )

    WebRenderer._add_responsive_image_variants(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert '<picture><source media="(max-width: 600px)"' in content
    assert 'srcset="../figures/graphical_mobile.png"' in content


def test_figure_images_link_to_full_resolution_assets_idempotently(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/dense.png" '
        'alt="Dense scientific figure"><figcaption>Dense figure.</figcaption></figure></body></html>',
        encoding="utf-8",
    )

    WebRenderer._add_full_resolution_figure_links(html_file)
    WebRenderer._add_full_resolution_figure_links(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert content.count('class="figure-full-size-link"') == 1
    assert 'href="../figures/dense.png"' in content
    assert 'target="_blank"' in content
    assert 'rel="noopener"' in content
    assert 'aria-label="Open full-size figure, Dense figure."' in content
    assert 'class="figure-full-size-label"' in content


def test_numbered_figure_full_size_link_has_contextual_accessible_name(
    tmp_path: Path,
) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/dense.png" '
        'alt="Dense scientific figure"><figcaption>Figure 7: Evidence map \\(F(q)\\).</figcaption>'
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._add_full_resolution_figure_links(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert 'aria-label="Open full-size Figure 7, Evidence map F(q)."' in content
    assert 'aria-label="Open full-size figure"' not in content


def test_full_size_link_uses_concise_caption_result_not_caption_metadata(
    tmp_path: Path,
) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:evidence"><img src="../figures/evidence.png" '
        'alt="Evidence map"><figcaption>Figure 12: Evidence classes remain in separate lanes. '
        "Source relation: source-owned explanatory map; uncertainty: none.</figcaption>"
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._add_full_resolution_figure_links(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert 'aria-label="Open full-size Figure 12, Evidence classes remain in separate lanes."' in content
    assert "Source relation" in content
    assert 'aria-label="Open full-size Figure 12, Evidence classes remain in separate lanes. Source' not in content


def test_full_size_link_shortens_a_long_result_at_a_semantic_boundary(
    tmp_path: Path,
) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure><img src="evidence.png" alt="Evidence map">'
        "<figcaption>Figure 6: Evidence class and replication remain claim-lane specific; "
        "guarantees do not migrate between client and server lanes.</figcaption></figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._add_full_resolution_figure_links(html_file)

    content = html_file.read_text(encoding="utf-8")
    assert 'aria-label="Open full-size Figure 6, Evidence class and replication remain claim-lane specific"' in content
    assert "guarantees do not migrate" in content
    assert (
        'aria-label="Open full-size Figure 6, Evidence class and replication remain claim-lane specific;' not in content
    )


def test_full_size_figure_link_rejects_missing_context(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure><img src="../figures/dense.png" alt=""></figure></body></html>',
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="contextual full-size link"):
        WebRenderer._add_full_resolution_figure_links(html_file)


def test_individual_render_embeds_publication_css_and_full_resolution_figure_link(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "03_results.md"
    source.write_text(
        "# Results\n\n![Dense figure](../figures/dense.png){#fig:dense width=100%}\n",
        encoding="utf-8",
    )
    web_dir = tmp_path / "output" / "web"
    renderer = WebRenderer(RenderingConfig(web_dir=str(web_dir), output_dir=str(tmp_path / "output")))

    result = renderer.render(source)

    content = result.read_text(encoding="utf-8")
    assert "--brand-1" in content
    assert "width: min(100%, 800px)" in content
    assert 'class="figure-full-size-link"' in content
    assert 'href="../figures/dense.png"' in content


def test_individual_render_output_names_include_parent_context(tmp_path: Path) -> None:
    renderer = _make_renderer(tmp_path)
    source_a = tmp_path / "manuscript" / "parts" / "alpha" / "00-overview.md"
    source_b = tmp_path / "manuscript" / "parts" / "beta" / "00-overview.md"

    assert renderer._output_file_for_source(source_a).name == "alpha__00-overview.html"
    assert renderer._output_file_for_source(source_b).name == "beta__00-overview.html"
