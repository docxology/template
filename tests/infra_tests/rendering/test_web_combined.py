"""Tests for infrastructure/rendering/web_renderer.py split by area.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""


class TestCombinedHtmlRendering:
    """Test combined HTML rendering functionality."""

    def test_render_combined_creates_index_html(self, tmp_path):
        """Test that render_combined creates index.html with TOC."""
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering.web_renderer import WebRenderer

        # Create test markdown files
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        md1 = manuscript_dir / "01_intro.md"
        md1.write_text("# Introduction\n\nThis is the introduction.")

        md2 = manuscript_dir / "02_methods.md"
        md2.write_text("# Methods\n\nThis describes the methods.")

        md3 = manuscript_dir / "03_results.md"
        md3.write_text("# Results\n\n$E = mc^2$\n\nSome results here.")

        # Setup config
        web_dir = tmp_path / "output" / "web"
        web_dir.mkdir(parents=True, exist_ok=True)

        config = RenderingConfig(
            web_dir=str(web_dir),
            output_dir=str(tmp_path / "output"),
        )

        # Test render_combined
        renderer = WebRenderer(config)
        source_files = [md1, md2, md3]

        result = renderer.render_combined(source_files, manuscript_dir, "test_project")

        # Verify index.html was created
        assert result.name == "index.html"
        assert result.exists()
        assert result.stat().st_size > 0

        # Verify content includes TOC and sections
        content = result.read_text()
        # Pandoc generates TOC with nav id="TOC" element, not "Table of Contents" text
        assert 'id="TOC"' in content or 'id="toc"' in content
        assert "Introduction" in content
        assert "Methods" in content
        assert "Results" in content
        # Pandoc generates IDs from heading text (e.g., id="introduction"), not section-N
        assert 'id="introduction"' in content
        assert 'id="methods"' in content
        assert 'id="results"' in content

    def test_render_manager_combined_web(self, tmp_path):
        """Test RenderManager.render_combined_web method."""
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering.core import RenderManager

        # Create test files
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        md1 = manuscript_dir / "a.md"
        md1.write_text("# Section A\n\nContent A.")

        md2 = manuscript_dir / "b.md"
        md2.write_text("# Section B\n\nContent B.")

        # Setup config
        web_dir = tmp_path / "output" / "web"
        config = RenderingConfig(
            web_dir=str(web_dir),
            output_dir=str(tmp_path / "output"),
        )

        manager = RenderManager(config)
        result = manager.render_combined_web([md1, md2], manuscript_dir, "test")

        assert result.exists()
        assert result.name == "index.html"

    def test_render_combined_resolves_bibliographic_citations(self, tmp_path):
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering.web_renderer import WebRenderer

        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        md = manuscript_dir / "01_intro.md"
        md.write_text(
            "# Introduction\n\nPrior work matters [@jaynes2003probability; @shannon1948theory].\n",
            encoding="utf-8",
        )
        (manuscript_dir / "references.bib").write_text(
            "@book{jaynes2003probability,\n"
            "  author = {Jaynes, Edwin T.},\n"
            "  title = {Probability Theory},\n"
            "  year = {2003},\n"
            "  publisher = {Cambridge University Press}\n"
            "}\n",
            encoding="utf-8",
        )
        (manuscript_dir / "z_supplemental.bib").write_text(
            "@article{shannon1948theory,\n"
            "  author = {Shannon, Claude E.},\n"
            "  title = {A Mathematical Theory of Communication},\n"
            "  year = {1948},\n"
            "  journal = {Bell System Technical Journal}\n"
            "}\n",
            encoding="utf-8",
        )

        web_dir = tmp_path / "output" / "web"
        config = RenderingConfig(web_dir=str(web_dir), output_dir=str(tmp_path / "output"))
        result = WebRenderer(config).render_combined([md], manuscript_dir, "test")

        content = result.read_text(encoding="utf-8")
        assert "Jaynes" in content
        assert "Shannon" in content
        assert "#ref-jaynes2003probability" in content
        assert "#ref-shannon1948theory" in content
        assert "[@jaynes2003probability]" not in content
        assert "[jaynes2003probability]" not in content
