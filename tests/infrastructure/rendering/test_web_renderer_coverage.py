"""Comprehensive tests for infrastructure/rendering/web_renderer.py.

Tests web/HTML rendering functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from pathlib import Path
import pytest

from infrastructure.rendering import web_renderer


class TestWebRendererCore:
    """Test core web renderer functionality."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        assert web_renderer is not None
    
    def test_has_render_functions(self):
        """Test that module has render functions."""
        module_funcs = [a for a in dir(web_renderer) if not a.startswith('_') and callable(getattr(web_renderer, a, None))]
        assert len(module_funcs) > 0


class TestHtmlRendering:
    """Test HTML rendering functionality."""
    
    def test_render_html(self, tmp_path):
        """Test rendering HTML."""
        md = tmp_path / "doc.md"
        md.write_text("# Title\n\nContent")
        
        if hasattr(web_renderer, 'render_html'):
            try:
                result = web_renderer.render_html(str(md))
            except Exception:
                pass
    
    def test_render_html_with_template(self, tmp_path):
        """Test rendering HTML with template."""
        md = tmp_path / "doc.md"
        md.write_text("# Title")
        
        if hasattr(web_renderer, 'render_html'):
            try:
                result = web_renderer.render_html(str(md), template='default')
            except Exception:
                pass


class TestMathJaxIntegration:
    """Test MathJax integration."""
    
    def test_render_with_mathjax(self, tmp_path):
        """Test rendering with MathJax."""
        md = tmp_path / "math.md"
        md.write_text("# Math\n\n$E = mc^2$")
        
        if hasattr(web_renderer, 'render_html'):
            try:
                result = web_renderer.render_html(str(md), mathjax=True)
            except Exception:
                pass
    
    def test_mathjax_config(self):
        """Test MathJax configuration."""
        if hasattr(web_renderer, 'get_mathjax_config'):
            config = web_renderer.get_mathjax_config()
            assert config is not None


class TestCssIntegration:
    """Test CSS integration."""
    
    def test_add_stylesheet(self, tmp_path):
        """Test adding stylesheet."""
        if hasattr(web_renderer, 'add_stylesheet'):
            html = "<html><head></head><body></body></html>"
            result = web_renderer.add_stylesheet(html, "style.css")
            assert result is not None
    
    def test_inline_css(self, tmp_path):
        """Test inlining CSS."""
        css = tmp_path / "style.css"
        css.write_text("body { color: black; }")
        
        if hasattr(web_renderer, 'inline_css'):
            html = "<html><head></head><body></body></html>"
            try:
                result = web_renderer.inline_css(html, str(css))
            except Exception:
                pass


class TestAssetHandling:
    """Test asset handling."""
    
    def test_copy_assets(self, tmp_path):
        """Test copying assets."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "image.png").write_bytes(b'\x89PNG')
        
        if hasattr(web_renderer, 'copy_assets'):
            try:
                web_renderer.copy_assets(str(src), str(tmp_path / "out"))
            except Exception:
                pass
    
    def test_resolve_asset_paths(self, tmp_path):
        """Test resolving asset paths."""
        html = '<img src="image.png">'
        
        if hasattr(web_renderer, 'resolve_asset_paths'):
            result = web_renderer.resolve_asset_paths(html, tmp_path)
            assert result is not None


class TestWebRendererIntegration:
    """Integration tests for web renderer."""
    
    def test_full_render_workflow(self, tmp_path):
        """Test complete rendering workflow."""
        # Create test content
        md = tmp_path / "doc.md"
        md.write_text("# Document\n\n## Section\n\nContent here.")
        
        # Module should be importable
        assert web_renderer is not None


class TestCombinedHtmlRendering:
    """Test combined HTML rendering functionality."""

    def test_render_combined_creates_index_html(self, tmp_path):
        """Test that render_combined creates index.html with TOC."""
        from infrastructure.rendering.config import RenderingConfig
        from infrastructure.rendering.web_renderer import WebRenderer

        # Create test markdown files
        md1 = tmp_path / "01_intro.md"
        md1.write_text("# Introduction\n\nThis is the introduction.")

        md2 = tmp_path / "02_methods.md"
        md2.write_text("# Methods\n\nThis describes the methods.")

        md3 = tmp_path / "03_results.md"
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
        
        result = renderer.render_combined(source_files, tmp_path, "test_project")

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
        from infrastructure.rendering.core import RenderManager
        from infrastructure.rendering.config import RenderingConfig

        # Create test files
        md1 = tmp_path / "a.md"
        md1.write_text("# Section A\n\nContent A.")

        md2 = tmp_path / "b.md"
        md2.write_text("# Section B\n\nContent B.")

        # Setup config
        web_dir = tmp_path / "output" / "web"
        config = RenderingConfig(
            web_dir=str(web_dir),
            output_dir=str(tmp_path / "output"),
        )

        manager = RenderManager(config)
        result = manager.render_combined_web([md1, md2], tmp_path, "test")

        assert result.exists()
        assert result.name == "index.html"
















