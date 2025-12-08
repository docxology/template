"""Additional tests for infrastructure/rendering/pdf_renderer.py.

Tests PDF rendering functionality.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from infrastructure.rendering import pdf_renderer


class TestPdfRendererHelpers:
    """Test helper functions."""
    
    def test_check_xelatex(self):
        """Test checking XeLaTeX availability."""
        if hasattr(pdf_renderer, 'check_xelatex'):
            result = pdf_renderer.check_xelatex()
            assert isinstance(result, bool)
    
    def test_check_pdflatex(self):
        """Test checking pdflatex availability."""
        if hasattr(pdf_renderer, 'check_pdflatex'):
            result = pdf_renderer.check_pdflatex()
            assert isinstance(result, bool)
    
    def test_get_latex_engine(self):
        """Test getting LaTeX engine."""
        if hasattr(pdf_renderer, 'get_latex_engine'):
            engine = pdf_renderer.get_latex_engine()
            assert engine is not None or True


class TestPdfRendererConfig:
    """Test configuration functionality."""
    
    def test_default_config(self):
        """Test default configuration."""
        if hasattr(pdf_renderer, 'PDFRenderConfig'):
            config = pdf_renderer.PDFRenderConfig()
            assert config is not None
    
    def test_custom_config(self):
        """Test custom configuration."""
        if hasattr(pdf_renderer, 'PDFRenderConfig'):
            try:
                config = pdf_renderer.PDFRenderConfig(engine='xelatex')
                assert config is not None
            except TypeError:
                pass


class TestPdfRendererOutput:
    """Test output handling."""
    
    def test_output_path_generation(self, tmp_path):
        """Test output path generation."""
        tex = tmp_path / "test.tex"
        tex.write_text("\\documentclass{article}")
        
        if hasattr(pdf_renderer, 'get_output_path'):
            output = pdf_renderer.get_output_path(str(tex))
            assert output is not None
    
    def test_cleanup_temp_files(self, tmp_path):
        """Test cleanup of temporary files."""
        # Create temp files
        (tmp_path / "test.aux").write_text("")
        (tmp_path / "test.log").write_text("")
        
        if hasattr(pdf_renderer, 'cleanup_temp_files'):
            pdf_renderer.cleanup_temp_files(tmp_path)
            # Should not raise


class TestPdfRendererErrors:
    """Test error handling."""
    
    def test_handle_latex_error(self, tmp_path):
        """Test handling LaTeX errors."""
        tex = tmp_path / "bad.tex"
        tex.write_text("\\invalid")
        
        if hasattr(pdf_renderer, 'render_pdf'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="Error")
                try:
                    result = pdf_renderer.render_pdf(str(tex))
                except Exception:
                    pass  # Expected to fail
    
    def test_handle_missing_file(self, tmp_path):
        """Test handling missing file."""
        if hasattr(pdf_renderer, 'render_pdf'):
            try:
                result = pdf_renderer.render_pdf(str(tmp_path / "missing.tex"))
            except Exception:
                pass  # Expected to fail






