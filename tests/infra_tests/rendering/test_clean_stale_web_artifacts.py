"""Regression test for infrastructure/rendering/_manuscript_source.py's web cleanup.

Follows the No Mocks Policy - exercises the real cleanup function against a
real temp directory tree.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering._manuscript_source import _clean_stale_web_artifacts
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
    dashboard = web_dir / "dashboard.html"
    dashboard.write_text("<html>dashboard</html>", encoding="utf-8")

    manager = _make_manager(web_dir)
    _clean_stale_web_artifacts(manager)

    assert not combined_index.exists()
    assert not section_page.exists()
    assert not combined_markdown.exists()
    assert dashboard.exists(), "unrelated project HTML artifacts must survive cleanup"


def test_clean_stale_web_artifacts_noop_when_html_disabled(tmp_path):
    """No files are touched when HTML rendering is disabled."""
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    stray = web_dir / "index.html"
    stray.write_text("<html></html>", encoding="utf-8")

    config = RenderingConfig(web_dir=str(web_dir), enable_html=False)
    manager = RenderManager(config=config)
    _clean_stale_web_artifacts(manager)

    assert stray.exists()


def test_clean_stale_web_artifacts_noop_when_dir_missing(tmp_path):
    """A missing web directory is a no-op, not an error."""
    manager = _make_manager(tmp_path / "does-not-exist")
    _clean_stale_web_artifacts(manager)
