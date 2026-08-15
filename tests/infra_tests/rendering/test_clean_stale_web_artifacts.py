"""Regression test for infrastructure/rendering/_manuscript_source.py's web cleanup.

Follows the No Mocks Policy - exercises the real cleanup function against a
real temp directory tree.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.rendering._manuscript_source import (
    _clean_stale_web_artifacts,
    clean_stale_render_deliverables,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.core import RenderManager


def _make_manager(web_dir: Path) -> RenderManager:
    config = RenderingConfig(web_dir=str(web_dir), enable_html=True)
    return RenderManager(config=config)


def test_clean_stale_web_artifacts_removes_only_manuscript_derived_pages(tmp_path):
    """Manuscript-derived HTML pages are removed; unrelated HTML artifacts survive.

    A project script (e.g. ``build_dashboard.py``) can legitimately write its
    own HTML artifact directly into ``output/web/`` outside the manuscript
    render pipeline. A prior version of this cleanup globbed every ``*.html``
    file in the directory and deleted it alongside the stale manuscript pages,
    silently destroying that artifact on every render pass.
    """
    web_dir = tmp_path / "web"
    web_dir.mkdir()

    combined_index = web_dir / "index.html"
    combined_index.write_text("<html>combined</html>", encoding="utf-8")
    section_page = web_dir / "manuscript__02_methodology.html"
    section_page.write_text("<html>section</html>", encoding="utf-8")
    combined_markdown = web_dir / "_combined_manuscript.md"
    combined_markdown.write_text("# combined", encoding="utf-8")
    favicon = web_dir / "favicon.ico"
    favicon.write_bytes(b"stale renderer favicon")
    dashboard = web_dir / "dashboard.html"
    dashboard.write_text("<html>dashboard</html>", encoding="utf-8")

    manager = _make_manager(web_dir)
    _clean_stale_web_artifacts(manager)

    assert not combined_index.exists()
    assert not section_page.exists()
    assert not combined_markdown.exists()
    assert not favicon.exists()
    assert dashboard.exists(), "unrelated project HTML artifacts must survive cleanup"


def test_clean_stale_web_artifacts_removes_generated_pages_when_html_disabled(tmp_path):
    """Disabled HTML cannot leave a stale combined page looking current."""
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    stray = web_dir / "index.html"
    stray.write_text("<html></html>", encoding="utf-8")

    config = RenderingConfig(web_dir=str(web_dir), enable_html=False)
    manager = RenderManager(config=config)
    _clean_stale_web_artifacts(manager)

    assert not stray.exists()


def test_clean_stale_web_artifacts_noop_when_dir_missing(tmp_path):
    """A missing web directory is a no-op, not an error."""
    manager = _make_manager(tmp_path / "does-not-exist")
    _clean_stale_web_artifacts(manager)


def test_clean_stale_render_deliverables_removes_only_canonical_targets(tmp_path: Path) -> None:
    """Current-run cleanup removes stale evidence and preserves unrelated outputs."""

    output_dir = tmp_path / "output"
    config = RenderingConfig(
        output_dir=str(output_dir),
        pdf_dir=str(output_dir / "pdf"),
        web_dir=str(output_dir / "web"),
        slides_dir=str(output_dir / "slides"),
        docx_dir=str(output_dir / "docx"),
        epub_dir=str(output_dir / "epub"),
    )
    manager = RenderManager(config=config)
    markdown = tmp_path / "manuscript" / "01_intro.md"
    latex = tmp_path / "manuscript" / "appendix.tex"
    markdown.parent.mkdir()
    markdown.write_text("# Intro\n", encoding="utf-8")
    latex.write_text("content\n", encoding="utf-8")

    canonical = [
        output_dir / "pdf" / "sample_combined.pdf",
        output_dir / "pdf" / "_combined_manuscript.md",
        output_dir / "pdf" / "_combined_manuscript.pdf",
        output_dir / "pdf" / "_combined_manuscript.log",
        output_dir / "pdf" / "appendix.pdf",
        output_dir / "pdf" / "deleted_appendix.pdf",
        output_dir / "pdf" / "deleted_appendix.log",
        output_dir / "pdf" / "old_project_combined.pdf",
        output_dir / "tex" / "_combined_manuscript.md",
        output_dir / "web" / "index.html",
        output_dir / "web" / "manuscript__01_intro.html",
        output_dir / "web" / "favicon.ico",
        output_dir / "slides" / "01_intro_slides.pdf",
        output_dir / "slides" / "01_intro_slides.html",
        output_dir / "slides" / "deleted_section_slides.pdf",
        output_dir / "slides" / "deleted_section_slides.log",
        output_dir / "docx" / "sample_combined.docx",
        output_dir / "docx" / "old_project_combined.docx",
        output_dir / "epub" / "sample_combined.epub",
        output_dir / "epub" / "old_project_combined.epub",
        output_dir / "reports" / "manuscript_composition.json",
    ]
    preserved = [
        output_dir / "pdf" / "independent_report.pdf",
        output_dir / "web" / "dashboard.html",
        output_dir / "slides" / "hand_authored_deck.pdf",
    ]
    for path in [*canonical, *preserved]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stale")

    clean_stale_render_deliverables(manager, [markdown, latex], "templates/sample")

    assert all(not path.exists() for path in canonical)
    assert all(path.is_file() for path in preserved)


def test_clean_stale_web_artifacts_fails_when_canonical_target_cannot_be_removed(tmp_path: Path) -> None:
    """A stale combined target cannot survive cleanup and satisfy verification."""

    web_dir = tmp_path / "web"
    (web_dir / "index.html").mkdir(parents=True)

    with pytest.raises(OSError):
        _clean_stale_web_artifacts(_make_manager(web_dir))
