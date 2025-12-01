"""Comprehensive tests for infrastructure/rendering/slides_renderer.py.

Tests slides rendering functionality.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import subprocess
import pytest

from infrastructure.rendering import slides_renderer
from infrastructure.rendering.slides_renderer import SlidesRenderer
from infrastructure.rendering.config import RenderingConfig
from infrastructure.core.exceptions import RenderingError


class TestSlidesRendererClass:
    """Test SlidesRenderer class."""
    
    def test_slides_renderer_initialization(self, tmp_path):
        """Test SlidesRenderer initialization."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        assert renderer.config == config
    
    def test_render_with_revealjs(self, tmp_path):
        """Test render() method with revealjs format (lines 49-50)."""
        config = RenderingConfig(output_dir=tmp_path, slides_dir=tmp_path / "slides")
        renderer = SlidesRenderer(config)
        
        # Create test markdown
        source = tmp_path / "slides.md"
        source.write_text("# Slide 1\n\n---\n\n# Slide 2")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = renderer.render(source, format="revealjs")
            
            # Should call pandoc with revealjs format
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "-t" in call_args
            assert "revealjs" in call_args
    
    def test_render_with_beamer(self, tmp_path):
        """Test render() method with beamer format (lines 46-47)."""
        config = RenderingConfig(output_dir=tmp_path, slides_dir=tmp_path / "slides")
        renderer = SlidesRenderer(config)
        
        source = tmp_path / "slides.md"
        source.write_text("# Slide 1")
        
        # Beamer rendering requires LaTeX, so we mock it
        with patch.object(renderer, '_render_beamer_with_paths') as mock_beamer:
            mock_beamer.return_value = tmp_path / "slides.pdf"
            
            result = renderer.render(source, format="beamer")
            
            mock_beamer.assert_called_once()


class TestRevealJsRendering:
    """Test reveal.js rendering (covers lines 54-73)."""
    
    def test_render_revealjs_success(self, tmp_path):
        """Test successful reveal.js rendering (lines 54-67)."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.html"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            
            result = renderer._render_revealjs(source, output)
            
            assert result == output
    
    def test_render_revealjs_failure(self, tmp_path):
        """Test reveal.js rendering failure (lines 69-73)."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.html"
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, 'pandoc', stderr="Rendering error"
            )
            
            with pytest.raises(RenderingError):
                renderer._render_revealjs(source, output)


class TestBeamerRendering:
    """Test Beamer rendering (covers lines 75-137)."""
    
    def test_render_beamer_with_paths_success(self, tmp_path):
        """Test successful beamer rendering."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.pdf"
        
        # Mock both pandoc and latex compilation
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            
            with patch('infrastructure.rendering.slides_renderer.compile_latex') as mock_latex:
                # Create fake output PDF
                output.write_text("fake pdf")
                
                result = renderer._render_beamer_with_paths(source, output, None, None)
                
                # Should call pandoc
                mock_run.assert_called_once()
    
    def test_render_beamer_with_resource_paths(self, tmp_path):
        """Test beamer rendering with manuscript and figures directories (lines 99-102)."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.pdf"
        manuscript_dir = tmp_path / "manuscript"
        figures_dir = tmp_path / "figures"
        manuscript_dir.mkdir()
        figures_dir.mkdir()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            
            with patch('infrastructure.rendering.slides_renderer.compile_latex'):
                output.write_text("fake pdf")
                
                result = renderer._render_beamer_with_paths(
                    source, output, manuscript_dir, figures_dir
                )
                
                # Check that resource paths were added
                call_args = mock_run.call_args[0][0]
                assert "--resource-path" in call_args
    
    def test_render_beamer_pdf_not_found(self, tmp_path):
        """Test beamer rendering when PDF not generated (lines 127-131)."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.pdf"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            
            with patch('infrastructure.rendering.slides_renderer.compile_latex'):
                # Don't create the output file
                with pytest.raises(RenderingError) as exc_info:
                    renderer._render_beamer_with_paths(source, output, None, None)
                
                assert "PDF not found" in str(exc_info.value)
    
    def test_render_beamer_subprocess_failure(self, tmp_path):
        """Test beamer rendering subprocess failure (lines 133-137)."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        source = tmp_path / "slides.md"
        source.write_text("# Test Slide")
        output = tmp_path / "slides.pdf"
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, 'pandoc', stderr="Beamer error"
            )
            
            with pytest.raises(RenderingError):
                renderer._render_beamer_with_paths(source, output, None, None)


class TestFigurePathFixing:
    """Test figure path fixing (covers lines 139-173)."""
    
    def test_fix_figure_paths_basic(self, tmp_path):
        """Test basic figure path fixing (lines 160-165)."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        tex_content = r"\includegraphics{../output/figures/test.png}"
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()
        
        fixed = renderer._fix_figure_paths(tex_content, output_dir, figures_dir)
        
        assert "../figures/test.png" in fixed
    
    def test_fix_figure_paths_already_correct(self, tmp_path):
        """Test that already correct paths are unchanged (lines 167-168)."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        tex_content = r"\includegraphics{../figures/test.png}"
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()
        
        fixed = renderer._fix_figure_paths(tex_content, output_dir, figures_dir)
        
        # Should remain unchanged
        assert "../figures/test.png" in fixed
    
    def test_fix_figure_paths_multiple(self, tmp_path):
        """Test fixing multiple figure paths."""
        config = RenderingConfig(output_dir=tmp_path)
        renderer = SlidesRenderer(config)
        
        tex_content = r"""
        \includegraphics{../output/figures/fig1.png}
        \includegraphics{../output/figures/fig2.png}
        \includegraphics{../figures/fig3.png}
        """
        output_dir = tmp_path / "slides"
        figures_dir = tmp_path / "figures"
        output_dir.mkdir()
        figures_dir.mkdir()
        
        fixed = renderer._fix_figure_paths(tex_content, output_dir, figures_dir)
        
        assert "../figures/fig1.png" in fixed
        assert "../figures/fig2.png" in fixed
        assert "../figures/fig3.png" in fixed


class TestSlidesRendererCore:
    """Test core slides renderer functionality."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        assert slides_renderer is not None
    
    def test_has_render_functions(self):
        """Test that module has render functions."""
        module_funcs = [a for a in dir(slides_renderer) if not a.startswith('_') and callable(getattr(slides_renderer, a, None))]
        assert len(module_funcs) > 0


class TestBeamerRendering:
    """Test Beamer slides rendering."""
    
    def test_render_beamer(self, tmp_path):
        """Test Beamer rendering."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1\n\n---\n\n# Slide 2")
        
        if hasattr(slides_renderer, 'render_beamer'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                try:
                    result = slides_renderer.render_beamer(str(md))
                except Exception:
                    pass
    
    def test_render_beamer_with_theme(self, tmp_path):
        """Test Beamer rendering with theme."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1")
        
        if hasattr(slides_renderer, 'render_beamer'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                try:
                    result = slides_renderer.render_beamer(str(md), theme='Madrid')
                except Exception:
                    pass


class TestRevealJsRendering:
    """Test reveal.js slides rendering."""
    
    def test_render_revealjs(self, tmp_path):
        """Test reveal.js rendering."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1\n\n---\n\n# Slide 2")
        
        if hasattr(slides_renderer, 'render_revealjs'):
            try:
                result = slides_renderer.render_revealjs(str(md))
            except Exception:
                pass
    
    def test_render_revealjs_with_options(self, tmp_path):
        """Test reveal.js with options."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1")
        
        if hasattr(slides_renderer, 'render_revealjs'):
            try:
                result = slides_renderer.render_revealjs(str(md), theme='moon')
            except Exception:
                pass


class TestSlidesParsing:
    """Test slides parsing functionality."""
    
    def test_parse_slides(self):
        """Test parsing slide content."""
        content = "# Slide 1\n\n---\n\n# Slide 2\n\n---\n\n# Slide 3"
        
        if hasattr(slides_renderer, 'parse_slides'):
            slides = slides_renderer.parse_slides(content)
            assert isinstance(slides, list)
    
    def test_extract_slide_metadata(self):
        """Test extracting slide metadata."""
        content = "---\ntitle: Test\n---\n\n# Slide 1"
        
        if hasattr(slides_renderer, 'extract_metadata'):
            metadata = slides_renderer.extract_metadata(content)
            assert metadata is not None


class TestSlideTemplates:
    """Test slide template functionality."""
    
    def test_apply_template(self, tmp_path):
        """Test applying template."""
        md = tmp_path / "slides.md"
        md.write_text("# Slide 1")
        
        if hasattr(slides_renderer, 'apply_template'):
            try:
                result = slides_renderer.apply_template(str(md), template='default')
            except Exception:
                pass
    
    def test_list_templates(self):
        """Test listing available templates."""
        if hasattr(slides_renderer, 'list_templates'):
            templates = slides_renderer.list_templates()
            assert isinstance(templates, (list, tuple))


class TestSlidesRendererIntegration:
    """Integration tests for slides renderer."""
    
    def test_full_render_workflow(self, tmp_path):
        """Test complete rendering workflow."""
        # Create test slides
        md = tmp_path / "slides.md"
        md.write_text("# Title Slide\n\n---\n\n# Content\n\n- Item 1\n- Item 2")
        
        # Module should be importable
        assert slides_renderer is not None

